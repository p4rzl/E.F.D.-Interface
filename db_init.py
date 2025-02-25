from index import app, db, User
import os
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Crea tutte le tabelle
        db.create_all()
        
        # Verifica se esiste già l'utente admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Crea l'utente admin
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,
                is_active=True,
                avatar_id='1'
            )
            admin.password_hash = generate_password_hash(admin_password)
            
            # Salva nel database
            db.session.add(admin)
            db.session.commit()
            print(f"Utente admin creato con password: {admin_password}")
        else:
            print("Utente admin già esistente")

if __name__ == "__main__":
    init_db()
    print("Database inizializzato con successo")
