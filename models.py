from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    avatar_id = Column(String(20), default='1')
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime, nullable=True)
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

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='messages')