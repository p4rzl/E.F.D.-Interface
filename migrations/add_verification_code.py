import sqlite3
import os

def run_migration():
    """Aggiunge il campo verification_code alla tabella users"""
    try:
        # Determina il percorso del database
        db_path = 'instance/database.db'
        
        # Verifica che il file database esista
        if not os.path.exists(db_path):
            print(f"Database non trovato: {db_path}")
            return False
            
        # Connessione al database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Controlla se la colonna esiste già
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'verification_code' not in columns:
            # Aggiungi la colonna verification_code
            cursor.execute("ALTER TABLE users ADD COLUMN verification_code VARCHAR(6)")
            print("Colonna 'verification_code' aggiunta con successo")
        else:
            print("La colonna 'verification_code' esiste già")
        
        # Commit delle modifiche
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
        return False

if __name__ == "__main__":
    print("Avvio migrazione del database...")
    success = run_migration()
    if success:
        print("Migrazione completata con successo")
    else:
        print("Migrazione fallita")
