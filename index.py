import os
import json
import numpy as np
import pandas as pd
import traceback
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from pathlib import Path
from flask_socketio import emit
from models import User, Message
from forms import LoginForm, RegisterForm
from extensions import db, login_manager, csrf, socketio
from reports import generate_risk_report, generate_hazard_report
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione dell'app Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chiave_segreta')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_LOGIN_ATTEMPTS'] = 5
app.config['ACCOUNT_LOCKOUT_MINUTES'] = 15

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
    public_endpoints = ['login', 'register', 'static']
    if not current_user.is_authenticated and request.endpoint not in public_endpoints:
        return redirect(url_for('login'))

# Gestisce la registrazione degli utenti
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Verifica se username esiste già
        if User.query.filter_by(username=form.username.data).first():
            flash('Username già in uso. Scegli un altro username.', 'error')
            return render_template('register.html', form=form)
        
        # Crea nuovo utente
        user = User(
            username=form.username.data,
            email=form.email.data,
            avatar_id=form.avatar_id.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registrazione completata! Ora puoi effettuare il login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

# Gestisce il login degli utenti
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Verifica se l'utente esiste
        if user is None:
            flash('Username non trovato. Controlla e riprova.', 'error')
            return render_template('login.html', form=form)
        
        # Controlla se l'account è bloccato
        if user.is_locked():
            remaining_time = user.get_lockout_remaining_time()
            flash(f'Account temporaneamente bloccato. Riprova tra {remaining_time} minuti.', 'error')
            return render_template('login.html', form=form)
        
        # Verifica la password
        if user.check_password(form.password.data):
            user.reset_failed_attempts()
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page if next_page and url_for('login') not in next_page else url_for('home'))
        
        # Incrementa il contatore di tentativi falliti
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
        if os.path.exists(beaches_geojson_path):
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
        context = {
            'username': current_user.username,
            'mapbox_token': MAPBOX_TOKEN,
            'beaches': beaches_data,
            'risk_data': risk_data,
            'hazard_data': hazard_data,
            'beaches_geojson': beaches_geojson,
            'economy_geojson': economy_geojson,
            'hazards_geojson': hazards_geojson
        }
        
        return render_template('home.html', **context)
        
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
                              username=current_user.username)
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
                              username=current_user.username)
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
        beaches_data = pd.read_csv('data/beaches.csv')
        beach = beaches_data[beaches_data['id'] == beach_id].iloc[0] if not beaches_data[beaches_data['id'] == beach_id].empty else None
        
        if beach is None:
            return jsonify({'error': 'Spiaggia non trovata'}), 404
        
        pdf_path = generate_risk_report(beach.to_dict(), current_user.username)
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
        beaches_data = pd.read_csv('data/beaches.csv')
        beach = beaches_data[beaches_data['id'] == beach_id].iloc[0] if not beaches_data[beaches_data['id'] == beach_id].empty else None
        
        if beach is None:
            return jsonify({'error': 'Spiaggia non trovata'}), 404
        
        pdf_path = generate_hazard_report(beach.to_dict(), current_user.username)
        return jsonify({'success': True, 'pdf_path': pdf_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Gestione della chat
@socketio.on('message')
def handle_message(data):
    if current_user.is_authenticated:
        message_text = data.get('message', '').strip()
        if message_text:
            # Salva il messaggio nel database
            message = Message(text=message_text, user_id=current_user.id)
            db.session.add(message)
            db.session.commit()
            
            # Invia il messaggio a tutti i client connessi
            emit('message', {
                'user': current_user.username,
                'message': message_text,
                'avatar_id': current_user.avatar_id,
                'time': datetime.now().strftime('%H:%M')
            }, broadcast=True)

# Admin route
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Accesso negato: devi essere un amministratore per accedere a questa pagina', 'error')
        return redirect(url_for('home'))
    
    users = User.query.all()
    return render_template('admin.html', users=users)

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

# Aggiungi un comando per eseguire automaticamente la pulizia dei messaggi
@app.cli.command("cleanup-messages")
def cleanup_messages_command():
    """Pulisce i messaggi più vecchi di 3 giorni."""
    with app.app_context():
        cleanup_old_messages()
        print("Pulizia dei messaggi completata.")

# Inizializzazione del database
def init_app_db():
    with app.app_context():
        db.create_all()
        # Crea utente admin se non esiste
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
            print(f"Creazione admin con password: {admin_password}")
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()

# Esecuzione dell'applicazione
if __name__ == '__main__':
    # Crea le directory necessarie se non esistono
    os.makedirs('data', exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)
    
    # Inizializza il database e l'utente admin
    print("Inizializzazione del database...")
    init_app_db()
    
    # Pulizia dei messaggi vecchi all'avvio
    with app.app_context():
        try:
            cleanup_old_messages()
            print("Pulizia automatica dei messaggi completata.")
        except Exception as e:
            print(f"Attenzione: Errore durante la pulizia dei messaggi: {e}")
    
    # Stampa un messaggio di avvio
    print("============================================")
    print("Applicazione avviata!")
    print("Accedi a http://localhost:5000 nel browser")
    print("Credenziali predefinite: admin/admin")
    print("============================================")
    
    # Avvia l'app
    socketio.run(app, debug=(os.environ.get('FLASK_ENV') == 'development'), host='0.0.0.0')