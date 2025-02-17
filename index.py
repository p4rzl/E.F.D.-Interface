from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os

# Carica le variabili d'ambiente
load_dotenv()

# Inizializzazione dell'app
app = Flask(__name__)

# Configurazioni di sicurezza
app.secret_key = os.getenv('SECRET_KEY')
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800,  # 30 minuti
    WTF_CSRF_TIME_LIMIT=3600  # 1 ora
)

# Inizializzazione delle estensioni
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Per favore, effettua il login per accedere a questa pagina.'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)
csrf = CSRFProtect(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    failed_login_attempts = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256:260000')
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        db.session.commit()

    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.is_active = False
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    return render_template("index.html", username=current_user.username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = FlaskForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(username=request.form['username']).first()
        
        if user and not user.is_active:
            flash('Account disattivato. Contatta l\'amministratore.', 'error')
            return redirect(url_for('login'))

        if user and user.check_password(request.form['password']):
            login_user(user, remember=False)
            user.update_last_login()
            next_page = request.args.get('next')
            if not next_page or url_for('login') in next_page:
                next_page = url_for('home')
            return redirect(next_page)
        else:
            if user:
                user.increment_failed_attempts()
            flash('Username o password non validi', 'error')
            return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='127.0.0.1', port=5000)