from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Ricordami')
    submit = SubmitField('Accedi')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=4, max=20)
    ])
    
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=30)
    ])
    
    confirm_password = PasswordField('Conferma Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])
    
    avatar_id = HiddenField('Avatar ID', default="1")
    
    submit = SubmitField('Registrati')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username già in uso. Scegli un altro username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email già registrata. Usa un\'altra email.')