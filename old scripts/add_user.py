from index import db, User, app

def add_user(username, password, is_admin):
    with app.app_context():
        user = User(username=username)
        user.set_password(password)
        user.is_admin = is_admin
        db.session.add(user)
        db.session.commit()
        print(f"Utente {username} aggiunto con successo!")

if __name__ == "__main__":
    username = input("Inserisci username: ")
    password = input("Inserisci password: ")
    is_admin_input = input("L'utente è un amministratore? (s/n): ")
    is_admin = (is_admin_input.lower() == 's')
    add_user(username, password, is_admin)