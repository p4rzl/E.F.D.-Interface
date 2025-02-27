import os
from flask import Flask
from models import db, User
from migrations.add_verification_code import run_migration

# Configurazione dell'app Flask minimale per la migrazione
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def run_migrations():
    with app.app_context():
        # Crea le tabelle se non esistono
        db.create_all()
        
        # Esegui la migrazione personalizzata
        run_migration()
        
        print("Verifica struttura attuale tabella users:")
        # Connessione diretta al database per ispezionare la struttura
        import sqlite3
        from sqlite3 import Error
        
        try:
            conn = sqlite3.connect('instance/database.db')
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            print("\nStruttura della tabella users:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
                
            conn.close()
        except Error as e:
            print(f"Errore SQLite: {e}")
        
        print("\nMigrazione database completata.")

if __name__ == "__main__":
    run_migrations()
