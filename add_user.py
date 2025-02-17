from index import db, User, app

def add_user(username, password):
    with app.app_context():
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Utente {username} aggiunto con successo!")

if __name__ == "__main__":
    username = input("Inserisci username: ")
    password = input("Inserisci password: ")
    add_user(username, password)