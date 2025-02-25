from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO

# Inizializzazione delle estensioni con parametro use_native_unicode=True
db = SQLAlchemy(engine_options={"pool_pre_ping": True})
login_manager = LoginManager()
csrf = CSRFProtect()

# Configurazione di SocketIO (per la chat in tempo reale)
socketio = SocketIO()

# Verifica che email_validator sia installato correttamente
def check_email_validator():
    try:
        import email_validator
        print(f"Email validator versione: {email_validator.__version__}")
        return True
    except ImportError:
        print("Attenzione: email_validator non è installato. I form di registrazione potrebbero non funzionare correttamente.")
        return False