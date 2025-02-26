from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, validators
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Ricordami')
    submit = SubmitField('Accedi')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        validators.DataRequired(), 
        validators.Length(min=4, max=80)
    ])
    
    email = StringField('Email', validators=[
        validators.DataRequired(), 
        validators.Email()
    ])
    
    password = PasswordField('Password', validators=[
        validators.DataRequired(),
        validators.Length(min=6)
    ])
    
    confirm_password = PasswordField('Conferma Password', validators=[
        validators.DataRequired(),
        validators.EqualTo('password', message='Le password devono coincidere')
    ])
    
    avatar_id = SelectField('Avatar', coerce=int, choices=[(i, f'Avatar {i}') for i in range(1, 9)], default=1)
    
    submit = SubmitField('Registrati')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username già in uso. Scegli un altro username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email già registrata. Usa un\'altra email.')