from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from extensions import db
import secrets
import random
import uuid

# Tabella di associazione per membri del gruppo
group_members = Table('group_members',
    db.Model.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('chat_groups.id'), primary_key=True)
)

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
    
    # Relazione per i messaggi inviati
    messages_sent = relationship('Message', 
                               foreign_keys='Message.sender_id', 
                               back_populates='sender')
    
    # Relazione per i messaggi ricevuti (privati)
    messages_received = relationship('Message', 
                                  foreign_keys='Message.recipient_id', 
                                  back_populates='recipient')
    
    # Relazione per i gruppi creati dall'utente
    groups_created = relationship('ChatGroup', back_populates='creator')
    
    # Relazione per i gruppi di cui l'utente è membro
    groups = relationship('ChatGroup', secondary=group_members, back_populates='members')
    
    # Relazione per le notifiche
    notifications = relationship('Notification', back_populates='user')
    
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
    
    def __repr__(self):
        return f'<User {self.username}>'

class ChatGroup(db.Model):
    __tablename__ = 'chat_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    creator_id = Column(Integer, ForeignKey('users.id'))
    
    # Relazioni
    creator = relationship('User', back_populates='groups_created')
    members = relationship('User', secondary=group_members, back_populates='groups')
    messages = relationship('Message', back_populates='group')
    
    def __repr__(self):
        return f'<ChatGroup {self.name}>'

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Chi invia il messaggio
    sender_id = Column(Integer, ForeignKey('users.id'))
    sender = relationship('User', foreign_keys=[sender_id], back_populates='messages_sent')
    
    # Chi riceve il messaggio (per messaggi privati)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    recipient = relationship('User', foreign_keys=[recipient_id], back_populates='messages_received')
    
    # Gruppo a cui appartiene il messaggio (se è un messaggio di gruppo)
    group_id = Column(Integer, ForeignKey('chat_groups.id'), nullable=True)
    group = relationship('ChatGroup', back_populates='messages')
    
    # Tipo di messaggio (generale, privato, gruppo)
    message_type = Column(String(20), default='general')
    
    # È stato letto?
    is_read = Column(Boolean, default=False)
    
    def __repr__(self):
        return f'<Message {self.id}>'
    
    @property
    def is_private(self):
        return self.message_type == 'private'
    
    @property
    def is_group(self):
        return self.message_type == 'group'
    
    @property
    def is_general(self):
        return self.message_type == 'general'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='notifications')
    
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # 'message', 'group_invitation', ecc.
    
    # Di quale entità si tratta? (ID del messaggio o del gruppo)
    related_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    # Payload JSON per dati aggiuntivi
    data = Column(Text, nullable=True)  # Memorizzato come JSON
    
    def __repr__(self):
        return f'<Notification {self.id}>'

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}={self.value}>'
    
    @classmethod
    def get(cls, key, default=None):
        """Ottiene un valore di configurazione dalla chiave"""
        config = cls.query.filter_by(key=key).first()
        return config.value if config else default
        
    @classmethod
    def set(cls, key, value, description=None):
        """Imposta un valore di configurazione"""
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = cls(key=key, value=value, description=description)
            db.session.add(config)
        db.session.commit()
        return config