from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username obbligatorio"),
        Length(min=3, max=20, message="L'username deve essere tra 3 e 20 caratteri"),
        Regexp(r'^[\w]+$', message="L'username può contenere solo lettere, numeri e underscore")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password obbligatoria")
    ])
    submit = SubmitField('Accedi')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username obbligatorio"),
        Length(min=3, max=20, message="L'username deve essere tra 3 e 20 caratteri"),
        Regexp(r'^[\w]+$', message="L'username può contenere solo lettere, numeri e underscore")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password obbligatoria"),
        Length(min=8, message="La password deve essere di almeno 8 caratteri"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$', 
               message="La password deve contenere almeno una lettera e un numero")
    ])
    confirm_password = PasswordField('Conferma Password', validators=[
        DataRequired(message="Conferma password obbligatoria"),
        EqualTo('password', message="Le password non coincidono")
    ])
    submit = SubmitField('Registrati')

    def validate_username(self, field):
        from index import User
        if User.query.filter_by(username=field.data.lower()).first():
            raise ValidationError('Username già in uso')
    
    def validate_password(self, field):
        if field.data.lower() in [self.username.data.lower()]:
            raise ValidationError('La password non può contenere username')