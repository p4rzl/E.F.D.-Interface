from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from flask import current_app
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256:260000')
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def update_last_login(self):
        self.last_login = datetime.now(timezone.utc)
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()

    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= current_app.config['MAX_LOGIN_ATTEMPTS']:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=current_app.config['LOCKOUT_TIME'])
        db.session.commit()

    def is_locked(self):
        if not self.locked_until:
            return False
        
        now = datetime.now(timezone.utc)
        if now < self.locked_until:
            return True
            
        self.locked_until = None
        self.failed_login_attempts = 0
        db.session.commit()
        return False

    def __repr__(self):
        return f'<User {self.username}>'