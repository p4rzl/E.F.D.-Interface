from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from extensions import db
import secrets
import random

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    avatar_id = Column(Integer, nullable=False, default=1)  # Garantiamo che non sia nullable
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False)
    verification_code = Column(String(6), nullable=True)  # Codice a 6 cifre invece del token
    token_expiration = Column(DateTime, nullable=True)
    reset_password_token = Column(String(100), unique=True, nullable=True)
    reset_token_expiration = Column(DateTime, nullable=True)
    messages = relationship('Message', back_populates='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def increment_failed_attempts(self):
        from flask import current_app
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= current_app.config['MAX_LOGIN_ATTEMPTS']:
            self.lockout_until = datetime.utcnow() + timedelta(minutes=current_app.config['ACCOUNT_LOCKOUT_MINUTES'])
        
        db.session.commit()
    
    def reset_failed_attempts(self):
        if self.failed_login_attempts > 0 or self.lockout_until:
            self.failed_login_attempts = 0
            self.lockout_until = None
            db.session.commit()
    
    def is_locked(self):
        if self.lockout_until and self.lockout_until > datetime.utcnow():
            return True
        elif self.lockout_until:
            # Sblocco automatico dopo che il periodo di blocco è scaduto
            self.lockout_until = None
            db.session.commit()
        return False
    
    def get_lockout_remaining_time(self):
        if not self.lockout_until:
            return 0
        
        delta = self.lockout_until - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 60))
    
    def generate_verification_code(self):
        """Genera un codice di verifica a 6 cifre e imposta la data di scadenza"""
        # Genera un numero casuale a 6 cifre (da 100000 a 999999)
        self.verification_code = str(random.randint(100000, 999999))
        self.token_expiration = datetime.now() + timedelta(hours=24)  # Codice valido per 24 ore
        return self.verification_code
        
    def verify_email_with_code(self, code):
        """Verifica il codice e attiva l'account"""
        if self.verification_code == code and self.token_expiration > datetime.now():
            self.email_verified = True
            self.verification_code = None
            self.token_expiration = None
            return True
        return False
        
    def is_code_expired(self):
        """Verifica se il codice è scaduto"""
        return self.token_expiration and self.token_expiration < datetime.now()
    
    def generate_reset_token(self):
        """Genera un token per il reset della password e imposta la data di scadenza"""
        self.reset_password_token = secrets.token_urlsafe(32)
        self.reset_token_expiration = datetime.now() + timedelta(hours=1)  # Token valido per 1 ora
        return self.reset_password_token
        
    def verify_reset_token(self, token):
        """Verifica il token di reset password"""
        if self.reset_password_token == token and self.reset_token_expiration > datetime.now():
            return True
        return False
        
    def is_reset_token_expired(self):
        """Verifica se il token di reset è scaduto"""
        return self.reset_token_expiration and self.reset_token_expiration < datetime.now()

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='messages')