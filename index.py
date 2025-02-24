from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from predictions import CoastalPredictor
from pathlib import Path 
import pandas as pd
import geopandas as gpd
import json
import os
import logging
from models import User, ChatMessage
from forms import LoginForm, RegistrationForm
from extensions import db, login_manager, csrf
from reports import get_risk_report, get_hazard_report, get_beaches_graph

# Configurazione logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Creazione della directory per le immagini statiche
if not os.path.exists('static/img'):
    os.makedirs('static/img')

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

# Creazione dell'app e inizializzazione di socketio
app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

def cleanup_old_messages():
    try:
        three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
        ChatMessage.query.filter(ChatMessage.created_at < three_days_ago).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f'Errore nella pulizia dei messaggi: {str(e)}')

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

MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')

# Gestisce la visualizzazione della home page
@app.route('/')
@app.route('/home')
@login_required 
def home():
    try:
        # Carica dati dalle varie cartelle
        beaches_data = pd.read_csv('data/beaches.csv')
        risk_data = pd.read_csv('data/risk/risk_weights.csv')
        hazard_data = pd.read_csv('data/hazard/hazard_weights.csv')
        
        # Carica dati curve
        curves_data = {}
        curves_path = Path('data/curves')
        for curve_file in curves_path.glob('*.csv'):
            curves_data[curve_file.stem] = pd.read_csv(curve_file)

        # Prepara i dati per il template
        context = {
            'username': current_user.username,
            'mapbox_token': MAPBOX_TOKEN,
            'beaches': beaches_data.to_dict('records'),
            'risk_data': risk_data.to_dict('records'),
            'hazard_data': hazard_data.to_dict('records'),
            'curves_data': curves_data
        }
        
        return render_template('home.html', **context)
    except Exception as e:
        logger.error(f'Errore nel caricamento della home page: {str(e)}')
        return render_template('500.html'), 500

@app.route('/api/map-data')
@login_required
def get_map_data():
    try:
        # Carica i dati GeoJSON delle spiagge
        beaches = gpd.read_file('data/beaches.geojson')
        
        # Carica altri layers 
        economy = gpd.read_file('data/risk/economia.geojson')
        hazards = gpd.read_file('data/risk/peligrosidad.geojson')
        
        return jsonify({
            'beaches': beaches.to_json(),
            'economy': economy.to_json(),
            'hazards': hazards.to_json()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/risk-report')
@login_required
def risk_report():
    data = get_data()
    if data:
        return str(get_risk_report("interactive", data))
    return render_template('500.html'), 500

@app.route('/hazard-report')
@login_required
def hazard_report():
    data = get_data()
    if data:
        return str(get_hazard_report("interactive", data))
    return render_template('500.html'), 500

@app.route('/risk-pdf')
@login_required
def risk_pdf():
    data = get_data()
    if data:
        return send_file(
            io.BytesIO(get_risk_report("static", data)),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="risk-report.pdf"
        )
    return render_template('500.html'), 500

@app.route('/hazard-pdf')
@login_required
def hazard_pdf():
    data = get_data()
    if data:
        return send_file(
            io.BytesIO(get_hazard_report("static", data)),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="hazard-report.pdf"
        )
    return render_template('500.html'), 500

@app.route('/beaches-graph')
@login_required
def beaches_graph():
    data = get_data()
    if data:
        return get_beaches_graph(data)
    return render_template('500.html'), 500

def get_data():
    session_data = session.get("data", {})
    data = {
        key: pd.read_json(
            io.StringIO(df_json), 
            orient="split", 
            typ="series", 
            convert_dates=False
        )
        for key, df_json in session_data.items()
    }
    return data    

@app.route('/api/prediction/<int:year>')
def get_prediction(year):
    try:
        predictor = CoastalPredictor()
        data = predictor.get_data_for_year(year)
        
        return jsonify({
            'coastline_features': data['coastline']['features'],
            'risk_features': data['risk']['features'],
            'prediction_factor': data['prediction_factor']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def load_geojson(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {'type': 'FeatureCollection', 'features': []}

@app.route('/api/trend/<int:year>')
@login_required
def get_trend(year):
    current_data = load_data_for_year(year)
    previous_data = load_data_for_year(year - 1)
    
    trend = calculate_trend(current_data, previous_data)
    
    return jsonify(trend)

def load_data_for_year(year):
    """Carica i dati per un anno specifico"""
    try:
        with open(f'data/yearly_data/{year}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'risk': 0, 'coastline': 0}

@app.route('/get_messages')
@login_required
def get_messages():
    cleanup_old_messages()
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(50).all()
    return jsonify([{
        'username': msg.user.username,
        'message': msg.message,
        'timestamp': msg.created_at.strftime('%d/%m/%Y %H:%M'),
        'avatar_id': msg.user.avatar_id
    } for msg in messages])
    
def cleanup_old_messages():
    try:
        three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
        ChatMessage.query.filter(ChatMessage.created_at < three_days_ago).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f'Errore nella pulizia dei messaggi: {str(e)}')

# WebSocket per i messaggi in tempo reale
@socketio.on('send_message')
def handle_message(data):
    if not current_user.is_authenticated:
        return
    
    try:
        message = ChatMessage(
            user_id=current_user.id,
            message=data['message']
        )
        db.session.add(message)
        db.session.commit()
        
        emit('new_message', {
            'username': current_user.username,
            'message': message.message,
            'timestamp': message.created_at.strftime('%d/%m/%Y %H:%M'),
            'isAdmin': current_user.is_admin,
            'avatar_id': current_user.avatar_id
        }, broadcast=True)
        
    except Exception as e:
        logger.error(f'Errore nell\'invio del messaggio: {str(e)}')
        db.session.rollback()
        
# Gestisce la visualizzazione della pagina admin
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    return render_template('admin.html', users=User.query.all())

# Gestisce la promozione/rimozione degli amministratori
@app.route('/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        user_to_toggle = User.query.get_or_404(user_id)
        
        # Impedisci di modificare l'admin principale
        if user_to_toggle.username == 'admin':
            flash('Non puoi modificare i permessi dell\'amministratore principale.', 'error')
            return redirect(url_for('admin'))
        
        # Impedisci di modificare il proprio stato di admin
        if user_to_toggle == current_user:
            flash('Non puoi modificare il tuo stato di amministratore.', 'error')
            return redirect(url_for('admin'))
            
        # Controlla che ci sia sempre almeno un admin
        if user_to_toggle.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
            flash('Deve esistere almeno un amministratore nel sistema.', 'error')
            return redirect(url_for('admin'))
        
        user_to_toggle.is_admin = not user_to_toggle.is_admin
        db.session.commit()
        
        action = "rimosso da" if not user_to_toggle.is_admin else "promosso ad"
        flash(f'Utente {user_to_toggle.username} {action} amministratore.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Errore nella modifica dei permessi: {str(e)}')
        flash('Errore durante la modifica dei permessi.', 'error')
        
    return redirect(url_for('admin'))

# Gestisce l'attivazione/disattivazione degli utenti
@app.route('/toggle_user/<int:user_id>', methods=['POST'])
@login_required
def toggle_user(user_id):
    if not current_user.is_admin:
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    user_to_toggle = User.query.get_or_404(user_id)
    
    # Impedisci di disattivare l'admin principale
    if user_to_toggle.username == 'admin':
        flash('Non puoi disattivare l\'amministratore principale.', 'error')
        return redirect(url_for('admin'))
    
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

@app.route('/api/geojson_files')
def get_geojson_files():
    geojson_files = []
    for root, dirs, files in os.walk('data'):
        for file in files:
            if file.endswith('.geojson'):
                file_path = os.path.join(root, file)
                geojson_files.append(file_path)
    return jsonify(geojson_files)

if __name__ == '__main__':
    init_app_db()
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
