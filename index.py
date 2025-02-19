from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timezone
from functools import wraps      # Da cambiare
from dotenv import load_dotenv
import os
import logging
from extensions import db, login_manager, csrf

# Configurazione logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crea e configura l'app Flask
def create_app():
    app = Flask(__name__)
    load_dotenv()

    # Configurazioni di sicurezza
    app.secret_key = os.getenv('SECRET_KEY')
    app.config.update(
        ENV=os.getenv('FLASK_ENV', 'production'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=1800,
        WTF_CSRF_TIME_LIMIT=3600,
        MAX_LOGIN_ATTEMPTS=5,
        LOCKOUT_TIME=30,
    )

    # Inizializzazione delle estensioni
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # Configurazione login manager
    login_manager.login_view = 'login'
    login_manager.login_message = 'Per favore, effettua il login per accedere a questa pagina.'
    login_manager.login_message_category = 'warning'
    login_manager.refresh_view = 'login'
    login_manager.needs_refresh_message = 'Per favore, effettua nuovamente il login per confermare la tua identità.'
    login_manager.needs_refresh_message_category = 'warning'

    # Registrazione dei middleware
    @app.before_request
    def require_login():
        public_endpoints = ['login', 'register', 'static']
        if not current_user.is_authenticated and request.endpoint not in public_endpoints:
            return redirect(url_for('login'))

    return app

# Creazione dell'app
app = create_app()

from models import User
from forms import LoginForm, RegistrationForm

# Carica l'utente dal database
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Gestisce l'accesso non autorizzato
@login_manager.unauthorized_handler
def unauthorized():
    flash('Devi effettuare il login per accedere a questa pagina.', 'error')
    return redirect(url_for('login', next=request.url))

# Gestisce la registrazione degli utenti
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registrazione completata con successo! Ora puoi effettuare il login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante la registrazione: {str(e)}')
            flash('Si è verificato un errore durante la registrazione. Riprova più tardi.', 'error')
    
    return render_template('register.html', form=form)

# Gestisce il login degli utenti
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if not user:
            flash('Username o password non validi', 'error')
            return render_template('login.html', form=form)
            
        if not user.is_active:
            flash('Account disattivato. Contatta l\'amministratore.', 'error')
            return render_template('login.html', form=form)
        
        if user.is_locked():
            remaining_time = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            flash(f'Account temporaneamente bloccato. Riprova tra {remaining_time} minuti.', 'error')
            return render_template('login.html', form=form)

        if user.check_password(form.password.data):
            login_user(user, remember=False)
            user.update_last_login()
            next_page = request.args.get('next')
            return redirect(next_page if next_page and url_for('login') not in next_page else url_for('home'))
        
        user.increment_failed_attempts()
        remaining_attempts = app.config['MAX_LOGIN_ATTEMPTS'] - user.failed_login_attempts
        flash(f'Password non valida. Tentativi rimanenti: {remaining_attempts}', 'error')
    
    return render_template('login.html', form=form)

# Gestisce il logout degli utenti
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('login'))

# Gestisce la visualizzazione della home page
@app.route('/')
@app.route('/home')
@login_required
def home():
    try:
        return render_template('home.html', username=current_user.username)
    except Exception as e:
        logger.error(f'Errore nel caricamento della home page: {str(e)}')
        return render_template('500.html'), 500

# Gestisce la visualizzazione della pagina admin
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    return render_template('admin.html', users=User.query.all())

# Gestisce l'attivazione/disattivazione degli utenti
@app.route('/toggle_user/<int:user_id>', methods=['POST'])
@login_required
def toggle_user(user_id):
    if not current_user.is_admin:
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    user_to_toggle = User.query.get_or_404(user_id)
    if user_to_toggle == current_user:
        flash('Non puoi disattivare il tuo account.', 'error')
        return redirect(url_for('admin'))
        
    user_to_toggle.is_active = not user_to_toggle.is_active
    db.session.commit()
    flash(f'Stato utente {user_to_toggle.username} aggiornato.', 'success')
    return redirect(url_for('admin'))

# Gestisce l'errore 404
@app.errorhandler(404)
def not_found_error(e):
    return render_template('404.html'), 404

# Gestisce l'errore 500
@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

# Forza l'uso di HTTPS in produzione
@app.before_request
def before_request():
    if os.getenv('FLASK_ENV') == 'production':
        if not request.is_secure and request.host != '127.0.0.1:5000':
            secure_url = request.url.replace('http://', 'https://', 1)
            return redirect(secure_url, code=301)

# Inizializza il database dell'app
def init_app_db():
    with app.app_context():
        db.create_all()
        # Crea utente admin se non esiste
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin'))
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_app_db()
    app.run(debug=True, host='127.0.0.1', port=5000)