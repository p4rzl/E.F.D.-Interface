import os
import json
import numpy as np
import pandas as pd
import traceback
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_from_directory
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from pathlib import Path
from flask_socketio import emit
from models import User, Message, SystemConfig
from forms import LoginForm, RegisterForm
from extensions import db, login_manager, csrf, socketio
from reports import generate_risk_report, generate_hazard_report
from dotenv import load_dotenv
import glob
from email_service import email_service
from translations import get_translations, get_available_languages

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Variabile globale per tenere traccia degli utenti online
online_users = set()

# Configurazione dell'app Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chiave_segreta')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_LOGIN_ATTEMPTS'] = 5
app.config['ACCOUNT_LOCKOUT_MINUTES'] = 15

# Configura l'URL base per le email
app.config['BASE_URL'] = os.environ.get('BASE_URL', 'http://localhost:5000')

# Inizializza le estensioni
db.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Per favore, effettua il login per accedere a questa pagina.'
login_manager.login_message_category = 'warning'

# Token per Mapbox
MAPBOX_TOKEN = os.environ.get('MAPBOX_TOKEN', 'pk.eyJ1IjoicDRyemwiLCJhIjoiY203ZWw3emd5MGN0eDJrc2V0eTdpcWN2ZCJ9.4VJRSR4REamVL1Qdw1wVdA')

# Inizializza SocketIO
socketio.init_app(app, cors_allowed_origins="*")

# Inizializzare il servizio email
email_service.init_app(app)

# Carica l'utente dal database
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Gestisce l'accesso non autorizzato
@login_manager.unauthorized_handler
def unauthorized():
    flash('Devi effettuare il login per accedere a questa pagina.', 'warning')
    return redirect(url_for('login', next=request.url))

# Solo le route pubbliche sono accessibili senza login
@app.before_request
def require_login():
    public_endpoints = ['login', 'register', 'static', 'verify_code', 'resend_verification', 
                       'forgot_password', 'reset_password', 'forgot_username']
    if not current_user.is_authenticated and request.endpoint not in public_endpoints:
        return redirect(url_for('login'))

# Funzione di utilità per creare dati di base per il template
def get_base_template_data():
    # Ottieni la lingua dalla sessione o dai parametri
    lang = request.args.get('lang', session.get('lang', 'it'))
    # Salva la lingua nella sessione
    session['lang'] = lang
    
    # Ottieni lo stato della chat
    chat_enabled = SystemConfig.get('chat_enabled', 'true') == 'true'
    
    return {
        'current_user': current_user,
        'lang': lang,
        't': get_translations(lang),  # Traduzioni
        'languages': get_available_languages(),  # Lingue disponibili
        'chat_enabled': chat_enabled  # Stato della chat
    }

# Gestisce la registrazione degli utenti
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Ottieni i dati base per il template (che includono la variabile 't' per le traduzioni)
    template_data = get_base_template_data()
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Verifica se username esiste già
        if User.query.filter_by(username=form.username.data).first():
            flash(template_data['t']['username_already_used'], 'error')
            template_data['form'] = form
            return render_template('register.html', **template_data)
        
        # Verifica se email esiste già
        if User.query.filter_by(email=form.email.data).first():
            flash(template_data['t']['email_already_registered'], 'error')
            template_data['form'] = form
            return render_template('register.html', **template_data)
        
        # Crea nuovo utente con l'avatar scelto
        user = User(
            username=form.username.data,
            email=form.email.data,
            avatar_id=int(form.avatar_id.data),  # Convertiamo esplicitamente in int
            email_verified=False  # Utente non verificato inizialmente
        )
        user.set_password(form.password.data)
        
        # Genera codice di verifica
        verification_code = user.generate_verification_code()
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Invia email con codice di verifica
            email_sent = email_service.send_verification_email(user, verification_code, template_data['lang'])
            
            if email_sent:
                flash(template_data['t']['verification_code_sent'], 'success')
            else:
                # Se l'invio dell'email fallisce, mostra il codice direttamente (solo per sviluppo)
                flash(template_data['t']['email_send_error'], 'warning')
                flash(f'Il tuo codice di verifica è: {verification_code}', 'info')
            
            # Reindirizza alla pagina di inserimento del codice
            verify_path = url_for('verify_code', email=user.email)
            return redirect(verify_path)
        except Exception as e:
            db.session.rollback()
            print(f"Errore durante la registrazione: {e}")
            flash(template_data['t']['registration_error'], 'error')
    
    # Aggiungi il form ai dati del template
    template_data['form'] = form
    return render_template('register.html', **template_data)

# Nuova route per la verifica tramite codice
@app.route('/verify-code/<email>', methods=['GET', 'POST'])
def verify_code(email):
    # Ottieni i dati base per il template
    template_data = get_base_template_data()
    t = template_data['t']  # Per facilità di riferimento
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash(t['user_not_found'], 'error')
        return redirect(url_for('login'))
    
    if user.email_verified:
        flash(t['email_already_verified'], 'info')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        code = request.form.get('verification_code')
        if not code:
            flash(t['enter_verification_code'], 'error')
            return render_template('verify_code.html', email=email, **template_data)
            
        if user.is_code_expired():
            # Codice scaduto, genera un nuovo codice
            new_code = user.generate_verification_code()
            db.session.commit()
            
            email_sent = email_service.send_verification_email(user, new_code, template_data['lang'])
            
            if email_sent:
                flash(t['code_expired'], 'info')
            else:
                flash(t['email_send_error'], 'error')
            
            return render_template('verify_code.html', email=email, **template_data)
            
        if user.verify_email_with_code(code):
            db.session.commit()
            flash(t['email_verified'], 'success')
            return redirect(url_for('login'))
        else:
            flash(t['invalid_code'], 'error')
    
    return render_template('verify_code.html', email=email, **template_data)

# Aggiorna la route per richiedere un nuovo codice di verifica
@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Ottieni i dati base per il template
    template_data = get_base_template_data()
    t = template_data['t']  # Per facilità di riferimento
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash(t['user_not_found'], 'error')
            return render_template('resend_verification.html', **template_data)
        
        if user.email_verified:
            flash(t['email_already_verified'], 'info')
            return redirect(url_for('login'))
        
        # Genera un nuovo codice di verifica
        verification_code = user.generate_verification_code()
        db.session.commit()
        # Invia email con il nuovo codice
        email_sent = email_service.send_verification_email(user, verification_code, template_data['lang'])
        if email_sent:
            flash(t['code_resent'], 'success')
        else:
            flash(t['email_send_error'], 'warning')
            if app.config.get('FLASK_ENV') == 'development':
                flash(f'Codice: {verification_code}', 'info')
        
        # Reindirizza alla pagina di verifica
        return redirect(url_for('verify_code', email=user.email))
    
    return render_template('resend_verification.html', **template_data)

# Modifica la funzione di login per controllare se l'email è verificata
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Ottieni i dati base per il template (che includono la variabile 't' per le traduzioni)
    template_data = get_base_template_data()
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Verifica se l'utente esiste
        if user is None:
            flash(template_data['t']['user_not_found'], 'error')
            template_data['form'] = form
            return render_template('login.html', **template_data)
        
        # Controlla se l'account è bloccato
        if user.is_locked():
            remaining_time = user.get_lockout_remaining_time()
            flash(f"{template_data['t']['account_locked']} {remaining_time} {template_data['t']['minutes']}.", 'error')
            template_data['form'] = form
            return render_template('login.html', **template_data)
        
        # Verifica la password
        if user.check_password(form.password.data):
            # Verifica che l'email sia verificata
            if not user.email_verified:
                flash(template_data['t']['verify_email_first'], 'warning')
                return redirect(url_for('verify_code', email=user.email))
                
            user.reset_failed_attempts()
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page if next_page and url_for('login') not in next_page else url_for('home'))
        
        # Incrementa il contatore di tentativi falliti
        user.increment_failed_attempts()
        remaining_attempts = app.config['MAX_LOGIN_ATTEMPTS'] - user.failed_login_attempts
        flash(f"{template_data['t']['invalid_password']} {remaining_attempts} {template_data['t']['remaining_attempts']}", 'error')
    
    # Aggiungi il form al contesto del template
    template_data['form'] = form
    return render_template('login.html', **template_data)

# Gestisce il logout degli utenti
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('login'))

# Modifica le funzioni di caricamento dati per gestire meglio i casi di file mancanti
@app.route('/')
@app.route('/home')
@login_required
def home():
    try:
        # Crea il percorso assoluto alla directory data
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        
        # Prepara dizionari vuoti per i dati
        beaches_data = []
        risk_data = {}
        hazard_data = {}
        beaches_geojson = None
        economy_geojson = None
        hazards_geojson = None
        
        # Carica dati delle spiagge se il file esiste
        beaches_path = os.path.join(data_dir, 'beaches.csv')
        if (os.path.exists(beaches_path)):
            beaches_data = pd.read_csv(beaches_path)
            # Converte valori problematici in float o None
            numeric_columns = ['length', 'width', 'risk_index', 'erosion_rate']
            for col in numeric_columns:
                if col in beaches_data.columns:
                    beaches_data[col] = pd.to_numeric(beaches_data[col], errors='coerce')
            # Converti NaN in None per gestire correttamente il template Jinja
            beaches_data = beaches_data.replace({np.nan: None})
            beaches_data = beaches_data.to_dict('records')
        else:
            print(f"File non trovato: {beaches_path}")
            # Crea dati di esempio se il file non esiste
            beaches_data = [
                {"id": 1, "name": "Spiaggia di Esempio 1", "length": 500, "width": 25, "risk_index": 0.65, "erosion_rate": 0.5},
                {"id": 2, "name": "Spiaggia di Esempio 2", "length": 800, "width": 30, "risk_index": 0.45, "erosion_rate": 0.3}
            ]
        
        # Carica dati di rischio e pericolo
        risk_path = os.path.join(data_dir, 'risk', 'risk_weights.csv')
        if os.path.exists(risk_path):
            # Legge il file CSV con indice
            risk_df = pd.read_csv(risk_path, comment="#", index_col=0)
            risk_df = risk_df.replace({np.nan: None})
            # Converti DataFrame in formato più accessibile per il template
            risk_data = {}
            for idx, row in risk_df.iterrows():
                risk_data[idx] = {
                    'weight': row.get('weight'),
                    'value': row.get('value')
                }
        else:
            # Dati di esempio per rischio
            risk_data = {
                'Economico': {'weight': 0.3, 'value': 0.65},
                'Sociale': {'weight': 0.4, 'value': 0.75},
                'Ambientale': {'weight': 0.3, 'value': 0.45}
            }
        
        hazard_path = os.path.join(data_dir, 'hazard', 'hazard_weights.csv')
        if os.path.exists(hazard_path):
            # Legge il file CSV con indice
            hazard_df = pd.read_csv(hazard_path, comment="#", index_col=0)
            hazard_df = hazard_df.replace({np.nan: None})
            # Converti DataFrame in formato più accessibile per il template
            hazard_data = {}
            for idx, row in hazard_df.iterrows():
                hazard_data[idx] = {
                    'weight': row.get('weight'),
                    'value': row.get('value')
                }
        else:
            # Dati di esempio per pericolo
            hazard_data = {
                'Erosione': {'weight': 0.4, 'value': 0.8},
                'Inondazione': {'weight': 0.3, 'value': 0.6},
                'Tempeste': {'weight': 0.3, 'value': 0.5}
            }
        
        # Prepara i dati geojson per la mappa
        beaches_geojson_path = os.path.join(data_dir, 'beaches.geojson')
        if (os.path.exists(beaches_geojson_path)):
            with open(beaches_geojson_path, 'r') as f:
                beaches_geojson = json.load(f)
        else:
            # Crea GeoJSON di esempio
            beaches_geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "id": 1,
                            "name": "Spiaggia di Esempio 1",
                            "length": 500,
                            "width": 25,
                            "risk_index": 0.65,
                            "erosion_rate": 0.5
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[1.29, 41.11], [1.30, 41.11], [1.30, 41.12], [1.29, 41.12], [1.29, 41.11]]]
                        }
                    }
                ]
            }
            
        # Carica dati di economia e pericolo per la mappa
        economy_geojson_path = os.path.join(data_dir, 'risk', 'economia.geojson')
        if os.path.exists(economy_geojson_path):
            with open(economy_geojson_path, 'r') as f:
                economy_geojson = json.load(f)
        
        hazards_geojson_path = os.path.join(data_dir, 'risk', 'peligrosidad.geojson')
        if os.path.exists(hazards_geojson_path):
            with open(hazards_geojson_path, 'r') as f:
                hazards_geojson = json.load(f)
        
        # Prepara i dati per il template
        template_data = get_base_template_data()
        template_data.update({
            'mapbox_token': MAPBOX_TOKEN,
            'beaches': beaches_data,
            'risk_data': risk_data,
            'hazard_data': hazard_data,
            'beaches_geojson': beaches_geojson,
            'economy_geojson': economy_geojson,
            'hazards_geojson': hazards_geojson
        })
        return render_template('home.html', **template_data)
    except Exception as e:
        import traceback
        error_msg = f'Errore nel caricamento della home page: {str(e)}'
        error_traceback = traceback.format_exc()
        print(error_msg)
        print(error_traceback)
        flash(error_msg, 'error')
        return render_template('500.html'), 500

# API per dati mappa con previsioni migliorate
@app.route('/api/map-data')
@login_required
def get_map_data():
    year = request.args.get('year', 2023, type=int)
    layer_type = request.args.get('layer', 'all')
    
    try:
        # Crea il percorso assoluto alla directory data
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        beaches_path = os.path.join(data_dir, 'beaches.csv')
        
        # Carica dati delle spiagge
        if os.path.exists(beaches_path):
            beaches_data = pd.read_csv(beaches_path)
        else:
            # Dati di esempio se il file non esiste
            beaches_data = pd.DataFrame({
                'id': range(1, 3),
                'name': ['Spiaggia di Esempio 1', 'Spiaggia di Esempio 2'],
                'length': [500, 800],
                'width': [25, 30],
                'risk_index': [0.65, 0.45],
                'erosion_rate': [0.5, 0.3]
            })
        
        # Converti valori problematici in float
        numeric_columns = ['length', 'width', 'risk_index', 'erosion_rate']
        for col in numeric_columns:
            if col in beaches_data.columns:
                beaches_data[col] = pd.to_numeric(beaches_data[col], errors='coerce')
        
        # Crea una copia dei dati originali per confronto
        original_data = beaches_data.copy()
        
        # Applica previsioni in base all'anno selezionato
        if year > 2023:
            years_forward = year - 2023
            # Simulazione di erosione (sottraendo larghezza basata sul tasso di erosione)
            for i, beach in beaches_data.iterrows():
                if pd.notna(beach['erosion_rate']) and pd.notna(beach['width']):
                    # Calcola la nuova larghezza
                    new_width = max(0, beach['width'] - (beach['erosion_rate'] * years_forward))
                    beaches_data.at[i, 'width'] = new_width
                    # Aggiorna l'indice di rischio (aumenta con l'erosione)
                    if beach['width'] > 0:
                        # Formula semplice: rischio aumenta proporzionalmente alla riduzione della larghezza
                        width_reduction_ratio = (beach['width'] - new_width) / beach['width']
                        risk_increase = min(0.5, width_reduction_ratio * 0.5)  # max 0.5 aumento
                        new_risk = min(1.0, beach['risk_index'] + risk_increase)
                        beaches_data.at[i, 'risk_index'] = new_risk
        
        # Converti dati in GeoJSON per la mappa
        beaches_geojson = None
        beaches_geojson_path = os.path.join(data_dir, 'beaches.geojson')
        
        if os.path.exists(beaches_geojson_path):
            with open(beaches_geojson_path, 'r') as f:
                beaches_geojson = json.load(f)
                
            # Aggiorna i dati GeoJSON con i valori previsti
            if beaches_geojson and 'features' in beaches_geojson:
                for feature in beaches_geojson['features']:
                    if 'properties' in feature and 'id' in feature['properties']:
                        beach_id = feature['properties']['id']
                        beach_row = beaches_data[beaches_data['id'] == beach_id]
                        
                        if not beach_row.empty:
                            feature['properties']['width'] = float(beach_row['width'].iloc[0])
                            feature['properties']['risk_index'] = float(beach_row['risk_index'].iloc[0])
        
        # Prepara statistiche comparative
        stats = {
            'year': year,
            'avg_width_reduction': (original_data['width'].mean() - beaches_data['width'].mean()) if year > 2023 else 0,
            'avg_risk_increase': (beaches_data['risk_index'].mean() - original_data['risk_index'].mean()) if year > 2023 else 0,
            'critically_eroded': beaches_data[beaches_data['width'] < 5].shape[0],
            'total_beaches': beaches_data.shape[0]
        }
        
        # Converti NaN in None
        beaches_data = beaches_data.replace({np.nan: None})
        
        # Restituisci i dati
        return jsonify({
            'beaches': beaches_data.to_dict('records'),
            'geojson': beaches_geojson,
            'stats': stats
        })
    
    except Exception as e:
        print(f'Errore nella generazione dei dati della mappa: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': 'Errore nel caricamento dei dati'}), 500

# Gestisce la generazione di report di rischio
@app.route('/risk-report')
@login_required
def risk_report():
    beach_id = request.args.get('beach', type=int)
    if not beach_id:
        flash('ID spiaggia non valido', 'error')
        return redirect(url_for('home'))
    
    try:
        beaches_data = pd.read_csv('data/beaches.csv')
        beach = beaches_data[beaches_data['id'] == beach_id].iloc[0] if not beaches_data[beaches_data['id'] == beach_id].empty else None
        
        if beach is None:
            flash('Spiaggia non trovata', 'error')
            return redirect(url_for('home'))
        
        return render_template('risk_report.html', 
                              beach=beach.to_dict(), 
                              username=current_user.username, 
                              datetime=datetime)  # Passa l'oggetto datetime
    except Exception as e:
        flash(f'Errore nella generazione del report: {str(e)}', 'error')
        return redirect(url_for('home'))

# Gestisce la generazione di report di pericolo
@app.route('/hazard-report')
@login_required
def hazard_report():
    beach_id = request.args.get('beach', type=int)
    if not beach_id:
        flash('ID spiaggia non valido', 'error')
        return redirect(url_for('home'))
    
    try:
        beaches_data = pd.read_csv('data/beaches.csv')
        beach = beaches_data[beaches_data['id'] == beach_id].iloc[0] if not beaches_data[beaches_data['id'] == beach_id].empty else None
        
        if beach is None:
            flash('Spiaggia non trovata', 'error')
            return redirect(url_for('home'))
        
        return render_template('hazard_report.html', 
                              beach=beach.to_dict(), 
                              username=current_user.username, 
                              datetime=datetime)  # Passa l'oggetto datetime
    except Exception as e:
        flash(f'Errore nella generazione del report: {str(e)}', 'error')
        return redirect(url_for('home'))

# Genera PDF del report di rischio
@app.route('/risk-pdf')
@login_required
def risk_pdf():
    beach_id = request.args.get('beach', type=int)
    if not beach_id:
        return jsonify({'error': 'ID spiaggia non valido'}), 400
    
    try:
        # Pulizia dei report vecchi prima di generarne di nuovi
        cleanup_old_reports()
        
        # Ottieni la lingua selezionata dall'utente
        language = request.args.get('lang', 'it')
        # Valida la lingua per sicurezza
        if language not in ['it', 'en', 'es', 'fr', 'de']:
            language = 'it'  # Default a italiano
        
        beaches_data = pd.read_csv('data/beaches.csv')
        beach = beaches_data[beaches_data['id'] == beach_id].iloc[0] if not beaches_data[beaches_data['id'] == beach_id].empty else None
        
        if beach is None:
            return jsonify({'error': 'Spiaggia non trovata'}), 404
        
        # Passa la lingua al generatore di report
        pdf_path = generate_risk_report(beach.to_dict(), current_user.username, language)
        return jsonify({'success': True, 'pdf_path': pdf_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Genera PDF del report di pericolo
@app.route('/hazard-pdf')
@login_required
def hazard_pdf():
    beach_id = request.args.get('beach', type=int)
    if not beach_id:
        return jsonify({'error': 'ID spiaggia non valido'}), 400
    
    try:
        # Pulizia dei report vecchi prima di generarne di nuovi
        cleanup_old_reports()
        
        # Ottieni la lingua selezionata dall'utente
        language = request.args.get('lang', 'it')
        # Valida la lingua per sicurezza
        if language not in ['it', 'en', 'es', 'fr', 'de']:
            language = 'it'  # Default a italiano
        
        beaches_data = pd.read_csv('data/beaches.csv')
        beach = beaches_data[beaches_data['id'] == beach_id].iloc[0] if not beaches_data[beaches_data['id'] == beach_id].empty else None
        
        if beach is None:
            return jsonify({'error': 'Spiaggia non trovata'}), 404
        
        # Passa la lingua al generatore di report
        pdf_path = generate_hazard_report(beach.to_dict(), current_user.username, language)
        return jsonify({'success': True, 'pdf_path': pdf_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Gestione della chat
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        # Aggiungi l'utente alla lista degli utenti online
        online_users.add(current_user.username)
        
        # Notifica tutti gli utenti che questo utente è online
        emit('user_status', {
            'username': current_user.username,
            'status': True
        }, broadcast=True)
        
        # Aggiungi un flag per evitare duplicazioni
        session['messages_sent'] = session.get('messages_sent', False)
        # Invia la cronologia dei messaggi solo la prima volta
        if not session['messages_sent']:
            # Recupera gli ultimi 50 messaggi dal database
            recent_messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()
            recent_messages.reverse()  # Inverti per ordine cronologico
            # Invia la cronologia dei messaggi al client che si è connesso
            for message in recent_messages:
                user = User.query.get(message.user_id)
                if user:
                    # Verifica se il messaggio appartiene all'utente corrente
                    is_own = message.user_id == current_user.id
                    emit('message', {
                        'id': f'msg-{message.id}',  # ID univoco
                        'user': user.username,
                        'message': message.text,
                        'avatar_id': user.avatar_id,
                        'is_admin': user.is_admin,
                        'is_own': is_own,  # Aggiungi flag per identificare i messaggi propri
                        'time': message.timestamp.strftime('%H:%M')
                    }, broadcast=False)  # Invia solo al client connesso
            # Imposta il flag per evitare reinvii
            session['messages_sent'] = True

# Aggiunta per gestire la disconnessione
@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        # Rimuovi l'utente dalla lista degli utenti online
        online_users.discard(current_user.username)
        
        # Notifica tutti gli utenti che questo utente è offline
        emit('user_status', {
            'username': current_user.username,
            'status': False
        }, broadcast=True)
        
        # Resetta il flag di messaggi inviati alla disconnessione
        if 'messages_sent' in session:
            session.pop('messages_sent', None)

@socketio.on('message')
def handle_message(data):
    if current_user.is_authenticated:
        message_text = data.get('message', '').strip()
        if message_text:
            # Salva il messaggio nel database
            message = Message(text=message_text, user_id=current_user.id)
            db.session.add(message)
            db.session.commit()
            # Invia il messaggio a tutti i client connessi con ID univoco
            emit('message', {
                'id': f'msg-{message.id}',  # ID univoco per questo messaggio
                'user': current_user.username,
                'message': message_text,
                'avatar_id': current_user.avatar_id,
                'is_admin': current_user.is_admin,  # Aggiungi flag per amministratore
                'time': datetime.now().strftime('%H:%M')
            }, broadcast=True)

# Admin route
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per accedere a questa pagina', 'error')
        return redirect(url_for('home'))
    
    # Ottieni lo stato della chat dal database (default: attivata)
    chat_enabled = SystemConfig.get('chat_enabled', 'true') == 'true'
    
    users = User.query.all()
    return render_template('admin.html', users=users, chat_enabled=chat_enabled)

# Nuova route per attivare/disattivare la chat
@app.route('/admin/toggle-chat', methods=['POST'])
@login_required
def toggle_chat_visibility():
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per eseguire questa azione', 'error')
        return redirect(url_for('home'))
    
    # Ottieni lo stato corrente e cambialo
    current_state = SystemConfig.get('chat_enabled', 'true')
    new_state = 'false' if current_state == 'true' else 'true'
    
    # Salva il nuovo stato
    SystemConfig.set('chat_enabled', new_state, 'Indica se la chat è visibile agli utenti')
    
    # Messaggio di conferma
    action = "attivata" if new_state == 'true' else "disattivata"
    flash(f'La chat è stata {action} con successo', 'success')
    
    return redirect(url_for('admin'))

# Route per attivare/disattivare utenti
@app.route('/toggle_user/<int:user_id>', methods=['POST'])
@login_required
def toggle_user(user_id):
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per eseguire questa azione', 'error')
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    # Previene la modifica dell'utente admin principale e dell'utente corrente
    if user.username == 'admin' or user == current_user:
        flash('Non puoi modificare questo utente', 'error')
        return redirect(url_for('admin'))
    user.is_active = not user.is_active
    db.session.commit()
    status = "attivato" if user.is_active else "disattivato"
    flash(f'Utente {user.username} {status} con successo', 'success')
    return redirect(url_for('admin'))

# Route per promuovere/declassare utenti ad admin
@app.route('/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per eseguire questa azione', 'error')
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    # Previene la modifica dell'utente admin principale e dell'utente corrente
    if user.username == 'admin' or user == current_user:
        flash('Non puoi modificare questo utente', 'error')
        return redirect(url_for('admin'))
    user.is_admin = not user.is_admin
    db.session.commit()
    status = "promosso ad amministratore" if user.is_admin else "rimosso da amministratore"
    flash(f'Utente {user.username} {status} con successo', 'success')
    return redirect(url_for('admin'))

# Route per eliminare un utente (solo admin)
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per eseguire questa azione', 'error')
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    # Previene l'eliminazione dell'utente admin principale e dell'utente corrente
    if user.username == 'admin' or user == current_user:
        flash('Non puoi eliminare questo utente', 'error')
        return redirect(url_for('admin'))
    db.session.delete(user)
    db.session.commit()
    flash(f'Utente {user.username} eliminato con successo', 'success')
    return redirect(url_for('admin'))

# Gestione degli errori
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

# HTTPS redirect in produzione
@app.before_request
def before_request():
    if os.environ.get('FLASK_ENV') == 'production':
        if not request.is_secure and request.host != '127.0.0.1:5000':
            secure_url = request.url.replace('http://', 'https://', 1)
            return redirect(secure_url, code=301)

# Pulizia dei messaggi vecchi (ridotta a 3 giorni)
def cleanup_old_messages():
    cutoff = datetime.now() - timedelta(days=3)  # Modificato da 7 a 3 giorni
    old_messages = Message.query.filter(Message.timestamp < cutoff).all()
    for message in old_messages:
        db.session.delete(message)
    db.session.commit()

# Aggiungi una route per eseguire la pulizia dei messaggi
@app.route('/admin/cleanup-messages', methods=['POST'])
@login_required
def admin_cleanup_messages():
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per eseguire questa azione', 'error')
        return redirect(url_for('home'))
    try:
        cleanup_old_messages()
        flash('Pulizia dei messaggi vecchi completata con successo', 'success')
    except Exception as e:
        flash(f'Errore durante la pulizia dei messaggi: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

# Aggiungi una route per eliminare tutti i messaggi
@app.route('/admin/delete-all-messages', methods=['POST'])
@login_required
def admin_delete_all_messages():
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per eseguire questa azione', 'error')
        return redirect(url_for('home'))
    
    try:
        # Elimina tutti i messaggi dal database
        Message.query.delete()
        db.session.commit()
        flash('Tutti i messaggi sono stati eliminati con successo', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione dei messaggi: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

# Aggiungi un comando per eseguire automaticamente la pulizia dei messaggi
@app.cli.command("cleanup-messages")
def cleanup_messages_command():
    """Pulisce i messaggi più vecchi di 3 giorni."""
    with app.app_context():
        cleanup_old_messages()
        print("Pulizia dei messaggi completata.")

# Nuova route dedicata alla chat
@app.route('/chat')
@login_required
def chat_page():
    # Controlla se la chat è attivata
    chat_enabled = SystemConfig.get('chat_enabled', 'true') == 'true'
    
    # Se la chat è disattivata e l'utente non è admin, reindirizza alla home
    if not chat_enabled and not current_user.is_admin:
        flash('La chat è attualmente disattivata', 'info')
        return redirect(url_for('home'))
    
    # Recupera gli ultimi 100 messaggi per mostrarli nella pagina
    messages = Message.query.order_by(Message.timestamp.asc()).limit(100).all()
    
    # Recupera tutti gli utenti attivi
    users = User.query.filter_by(is_active=True).all()
    
    # Aggiungi proprietà is_online a ogni utente
    for user in users:
        user.is_online = user.username in online_users or user == current_user
    
    # Aggiungi automaticamente l'utente corrente alla lista di utenti online
    online_users.add(current_user.username)
    
    template_data = get_base_template_data()
    template_data.update({
        'messages': messages, 
        'users': users
    })
    
    return render_template('chat.html', **template_data)

# Aggiungiamo una route specifica per i suoni
@app.route('/static/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'audio'), filename)

# Inizializzazione del database
def init_app_db():
    with app.app_context():
        db.create_all()
        # Crea utente admin se non esiste
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True, email_verified=True)  # Admin è già verificato
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
            print(f"Creazione admin con password: {admin_password}")
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()        
        
        # Imposta la configurazione predefinita della chat se non esiste
        if not SystemConfig.query.filter_by(key='chat_enabled').first():
            SystemConfig.set('chat_enabled', 'true', 'Indica se la chat è visibile agli utenti')

# Funzione per eliminare i report vecchi
def cleanup_old_reports():
    """Elimina i report PDF più vecchi di 10 minuti"""
    try:
        reports_dir = os.path.join(app.static_folder, 'reports')
        if not os.path.exists(reports_dir):
            return
        # Tempo limite: 10 minuti fa
        cutoff_time = datetime.now() - timedelta(minutes=10)
        
        # Trova tutti i file PDF nella directory reports
        pdf_files = glob.glob(os.path.join(reports_dir, "*.pdf"))
        
        cleaned = 0
        for pdf_path in pdf_files:
            # Ottieni la data di modifica del file
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(pdf_path))
            
            # Se il file è più vecchio del tempo limite, eliminalo
            if file_mod_time < cutoff_time:
                try:
                    os.remove(pdf_path)
                    cleaned += 1
                except (PermissionError, OSError) as e:
                    print(f"Errore nell'eliminazione del file {pdf_path}: {str(e)}")
        if cleaned > 0:
            print(f"Pulizia report: {cleaned} file PDF eliminati.")
    except Exception as e:
        print(f"Errore durante la pulizia dei report: {str(e)}")
        traceback.print_exc()

# Aggiungiamo una route per la pulizia dei report all'area admin
@app.route('/admin/cleanup-reports', methods=['POST'])
@login_required
def admin_cleanup_reports():
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per eseguire questa azione', 'error')
        return redirect(url_for('home'))
    
    try:
        cleanup_old_reports()
        flash('Pulizia dei report vecchi completata con successo', 'success')
    except Exception as e:
        flash(f'Errore durante la pulizia dei report: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

# Aggiungi un comando CLI per pulire i report vecchi
@app.cli.command("cleanup-reports")
def cleanup_reports_command():
    """Pulisce i report PDF più vecchi di 10 minuti."""
    with app.app_context():
        cleanup_old_reports()
        print("Pulizia dei report completata.")

# Route per recupero password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # Ottieni i dati base per il template
    template_data = get_base_template_data()
    t = template_data['t']  # Per facilità di riferimento
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash(t['user_not_found'], 'error')
            return render_template('forgot_password.html', **template_data)
        
        # Genera un token di reset
        reset_token = user.generate_reset_token()
        db.session.commit()
        
        # Crea URL di reset con dominio personalizzato
        base_url = app.config.get('BASE_URL')
        reset_path = url_for('reset_password', token=reset_token)
        reset_url = f"{base_url}{reset_path}"
        
        # Invia email con link di reset
        email_sent = email_service.send_password_reset_email(user, reset_url, template_data['lang'])
        
        if email_sent:
            flash(t['reset_link_sent'], 'success')
        else:
            flash(t['email_send_error'], 'warning')
            # In ambiente di sviluppo, mostra l'URL di reset
            if app.config.get('FLASK_ENV') == 'development':
                flash(f'URL di reset (solo per sviluppo): {reset_url}', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html', **template_data)
    
# Route per reimpostare la password
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Ottieni la lingua dalla sessione o dai parametri
    lang = request.args.get('lang', session.get('lang', 'it'))
    session['lang'] = lang
    t = get_translations(lang)
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Trova l'utente con il token di reset
    user = User.query.filter_by(reset_password_token=token).first()
    if not user:
        flash(t['invalid_reset_link'], 'error')
        return redirect(url_for('forgot_password'))
    
    if user.is_reset_token_expired():
        flash(t['expired_reset_link'], 'error')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password:
            flash(t['enter_password'], 'error')
            return render_template('reset_password.html', token=token, t=t, lang=lang, languages=get_available_languages())
            
        if password != confirm_password:
            flash(t['passwords_not_match'], 'error')
            return render_template('reset_password.html', token=token, t=t, lang=lang, languages=get_available_languages())
            
        if len(password) < 8:
            flash(t['password_requirements'], 'error')
            return render_template('reset_password.html', token=token, t=t, lang=lang, languages=get_available_languages())
        
        # Imposta la nuova password e cancella il token di reset
        user.set_password(password)
        user.reset_password_token = None
        user.reset_token_expiration = None
        db.session.commit()
        
        flash(t['password_reset_success'], 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token, t=t, lang=lang, languages=get_available_languages())

# Route per recupero username
@app.route('/forgot-username', methods=['GET', 'POST'])
def forgot_username():
    # Ottieni i dati base per il template
    template_data = get_base_template_data()
    t = template_data['t']  # Per facilità di riferimento
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash(t['user_not_found'], 'error')
            return render_template('forgot_username.html', **template_data)
        
        # Invia email con username
        email_sent = email_service.send_username_reminder_email(user, template_data['lang'])
        if email_sent:
            flash(t['username_reminder_sent'], 'success')
        else:
            flash(t['email_send_error'], 'warning')
            # In ambiente di sviluppo, mostra l'username
            if app.config.get('FLASK_ENV') == 'development':
                flash(f'Il tuo nome utente è: {user.username}', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_username.html', **template_data)

# Esecuzione dell'applicazione
if __name__ == '__main__':
    # Crea le directory necessarie se non esistono
    os.makedirs('data', exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)
    # Crea la directory per i log delle email se in modalità file
    if os.environ.get('EMAIL_SERVICE_TYPE') == 'file':
        log_dir = os.environ.get('EMAIL_LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
    
    # Inizializza il database e l'utente admin
    print("Inizializzazione del database...")
    init_app_db()
    
    # Esegui le migrazioni necessarie
    try:
        from migrations.add_verification_code import run_migration
        run_migration()
        print("Migrazione verification_code completata.")
    except Exception as e:
        print(f"Avviso: Migrazione non eseguita - {str(e)}")
    
    # Pulizia dei messaggi vecchi all'avvio
    with app.app_context():
        try:
            cleanup_old_messages()
            print("Pulizia automatica dei messaggi completata.")
            # Aggiungiamo anche la pulizia dei report all'avvio
            cleanup_old_reports()
            print("Pulizia automatica dei report completata.")
        except Exception as e:
            print(f"Attenzione: Errore durante la pulizia automatica: {e}")
    
    # Stampa un messaggio di avvio
    print("============================================")
    print("Applicazione avviata!")
    print("Accedi a http://localhost:5000 nel browser")
    print("Credenziali predefinite: admin/admin")
    print("============================================")
    
    # Avvia l'app
    socketio.run(app, debug=(os.environ.get('FLASK_ENV') == 'development'), host='0.0.0.0')

# Aggiungi questi gestori di eventi socket.io per supportare la nuova chat

@socketio.on('get_messages')
def handle_get_messages(data):
    if not current_user.is_authenticated:
        return
    
    chat_type = data.get('chatType')
    target_id = data.get('targetId')
    
    messages = []
    
    if chat_type == 'general':
        # Recupera i messaggi della chat generale (limitati a 50)
        messages = Message.query.filter_by(message_type='general').order_by(Message.timestamp.desc()).limit(50).all()
    elif chat_type == 'private' and target_id:
        # Recupera i messaggi privati tra i due utenti
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == target_id)) |
            ((Message.sender_id == target_id) & (Message.recipient_id == current_user.id))
        ).filter_by(message_type='private').order_by(Message.timestamp.asc()).all()
    elif chat_type == 'group' and target_id:
        # Recupera i messaggi del gruppo
        messages = Message.query.filter_by(
            group_id=target_id, message_type='group'
        ).order_by(Message.timestamp.asc()).all()
    
    # Invia i messaggi al client
    for message in messages:
        sender = User.query.get(message.sender_id)
        if sender:
            emit('message', {
                'id': f'msg-{message.id}',
                'user': sender.username,
                'message': message.text,
                'avatar_id': sender.avatar_id,
                'is_admin': sender.is_admin,
                'is_own': message.sender_id == current_user.id,
                'time': message.timestamp.strftime('%H:%M'),
                'chatType': message.message_type,
                'fromUserId': message.sender_id,
                'toUserId': message.recipient_id,
                'groupId': message.group_id
            })

@socketio.on('get_chat_participants')
def handle_get_chat_participants(data):
    if not current_user.is_authenticated:
        return
        
    chat_type = data.get('chatType')
    target_id = data.get('targetId')
    
    online_users_list = []
    offline_users_list = []
    
    if chat_type == 'general':
        # Per la chat generale, includi tutti gli utenti
        all_users = User.query.filter(User.is_active == True).all()
        
        for user in all_users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'avatar_id': user.avatar_id,
                'is_admin': user.is_admin
            }
            
            # Verifica se l'utente è online
            if user.username in online_users:
                online_users_list.append(user_data)
            else:
                offline_users_list.append(user_data)
                
    elif chat_type == 'private' and target_id:
        # Per le chat private, includi solo l'altro utente e l'utente corrente
        other_user = User.query.get(target_id)
        
        if other_user and other_user.is_active:
            user_data = {
                'id': other_user.id,
                'username': other_user.username,
                'avatar_id': other_user.avatar_id,
                'is_admin': other_user.is_admin
            }
            
            # Verifica se l'utente è online
            if other_user.username in online_users:
                online_users_list.append(user_data)
            else:
                offline_users_list.append(user_data)
                
        # Includi anche l'utente corrente (sempre "online")
        online_users_list.append({
            'id': current_user.id,
            'username': current_user.username,
            'avatar_id': current_user.avatar_id,
            'is_admin': current_user.is_admin
        })
        
    elif chat_type == 'group' and target_id:
        # Per le chat di gruppo, includi i membri del gruppo
        group = ChatGroup.query.get(target_id)
        if group:
            for member in group.members:
                if member.is_active:
                    user_data = {
                        'id': member.id,
                        'username': member.username,
                        'avatar_id': member.avatar_id,
                        'is_admin': member.is_admin
                    }
                    
                    # Verifica se l'utente è online
                    if member.username in online_users:
                        online_users_list.append(user_data)
                    else:
                        offline_users_list.append(user_data)
    
    # Invia i partecipanti al client
    emit('chat_participants', {
        'online': online_users_list,
        'offline': offline_users_list
    })

@socketio.on('get_group_info')
def handle_get_group_info(data):
    if not current_user.is_authenticated:
        return
        
    group_id = data.get('group_id')
    if not group_id:
        return
        
    group = ChatGroup.query.get(group_id)
    if not group:
        return
        
    creator = User.query.get(group.creator_id)
    creator_name = creator.username if creator else 'Unknown'
    
    # Prepara le informazioni sui membri
    members = []
    for member in group.members:
        if member.is_active:
            members.append({
                'id': member.id,
                'username': member.username,
                'avatar_id': member.avatar_id,
                'is_admin': member.is_admin,
                'is_online': member.username in online_users
            })
    
    # Invia le informazioni sul gruppo al client
    emit('group_info', {
        'id': group.id,
        'name': group.name,
        'description': group.description,
        'creator_id': group.creator_id,
        'creator_name': creator_name,
        'created_at': group.created_at.isoformat(),
        'members': members
    })

@socketio.on('create_group')
def handle_create_group(data):
    if not current_user.is_authenticated:
        return
        
    name = data.get('name')
    description = data.get('description', '')
    member_ids = data.get('members', [])
    
    if not name:
        return
    
    try:
        # Crea un nuovo gruppo
        group = ChatGroup(
            name=name,
            description=description,
            creator_id=current_user.id
        )
        
        # Aggiungi il creatore come membro
        group.members.append(current_user)
        
        # Aggiungi gli altri membri
        if member_ids:
            for member_id in member_ids:
                member = User.query.get(member_id)
                if member and member.is_active:
                    group.members.append(member)
        
        db.session.add(group)
        db.session.commit()
        
        # Notifica a tutti gli utenti il nuovo gruppo
        emit('new_group', {
            'id': group.id,
            'name': group.name,
            'description': group.description,
            'creator_id': group.creator_id
        }, broadcast=True)
        
        # Invia un messaggio di sistema nel gruppo
        system_message = Message(
            text=f"{current_user.username} ha creato il gruppo",
            sender_id=current_user.id,
            group_id=group.id,
            message_type='group'
        )
        db.session.add(system_message)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Errore nella creazione del gruppo: {str(e)}")

@socketio.on('join_group')
def handle_join_group(data):
    if not current_user.is_authenticated:
        return
        
    group_id = data.get('group_id')
    if not group_id:
        return
        
    group = ChatGroup.query.get(group_id)
    if not group:
        return
        
    # Aggiungi l'utente al gruppo se non è già membro
    if current_user not in group.members:
        group.members.append(current_user)
        db.session.commit()
