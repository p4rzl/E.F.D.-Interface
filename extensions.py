from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy(engine_options={"pool_pre_ping": True})
login_manager = LoginManager()
csrf = CSRFProtect()

# Rimuoviamo completamente il riferimento a SocketIO
# Non è più necessario in nessuna parte dell'applicazione

# Verifica che email_validator sia installato correttamente
def check_email_validator():
    try:
        import email_validator
        print(f"Email validator versione: {email_validator.__version__}")
        return True
    except ImportError:
        print("Attenzione: email_validator non è installato. I form di registrazione potrebbero non funzionare correttamente.")
        return False