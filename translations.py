"""
Modulo per la gestione delle traduzioni multilingua
"""

def get_translations(language='it'):
    """
    Restituisce un dizionario di traduzioni per la lingua specificata
    
    Args:
        language (str): Codice della lingua (it, en, es, fr, de)
    
    Returns:
        dict: Dizionario con le traduzioni
    """
    # Dizionario di default in italiano
    translations_it = {
        # Traduzioni per la navbar
        "home": "Home",
        "chat": "Chat",
        "admin": "Admin",
        "login": "Accedi",
        "logout": "Esci",
        "register": "Registrati",
        "profile": "Profilo",
        "dark_mode": "Modalità scura",
        "light_mode": "Modalità chiara",
        
        # Traduzioni per login/registrazione
        "username": "Nome utente",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Conferma password",
        "remember_me": "Ricordami",
        "sign_in": "Accedi",
        "sign_up": "Registrati",
        "no_account": "Non hai un account?",
        "already_registered": "Hai già un account?",
        "select_avatar": "Seleziona un avatar",
        
        # Traduzioni per recupero credenziali
        "forgot_password": "Password dimenticata?",
        "forgot_username": "Nome utente dimenticato?",
        "reset_password": "Reimposta la tua password",
        "recover_username": "Recupera il tuo nome utente",
        "send_reset_link": "Invia link di reset",
        "send_username_reminder": "Invia promemoria username",
        "reset_password_intro": "Inserisci una nuova password per il tuo account.",
        "password_reset_success": "La tua password è stata reimpostata con successo.",
        "enter_new_password": "Inserisci una nuova password",
        "password_requirements": "La password deve contenere almeno 8 caratteri.",
        "passwords_not_match": "Le password non coincidono.",
        
        # Traduzioni per verifica email
        "verify_email": "Verifica la tua email",
        "verification_code": "Codice di verifica",
        "enter_verification_code": "Ti abbiamo inviato un codice di verifica all'indirizzo email fornito durante la registrazione. Inseriscilo qui sotto per verificare il tuo account.",
        "verify_button": "Verifica",
        "resend_code": "Non hai ricevuto il codice?",
        "resend_verification": "Invia di nuovo",
        "code_resent": "Un nuovo codice è stato inviato alla tua email.",
        "email_verified": "Email verificata con successo!",
        "invalid_code": "Codice non valido. Riprova.",
        "expired_code": "Il codice è scaduto. Abbiamo inviato un nuovo codice.",
        
        # Email di verifica
        "verification_email_subject": "Verifica il tuo indirizzo email",
        "verification_email_intro": "Grazie per esserti registrato! Per completare la registrazione, inserisci il seguente codice di verifica nel nostro sito web:",
        "verification_code_valid_for": "Questo codice è valido per",
        "if_you_did_not_register": "Se non hai richiesto la registrazione, puoi ignorare questa email.",
        
        # Email di reset password
        "reset_password_subject": "Reimposta la tua password",
        "reset_password_intro": "Abbiamo ricevuto una richiesta di reset della password per il tuo account. Clicca sul pulsante qui sotto per reimpostare la tua password:",
        "reset_link_valid_for": "Questo link è valido per",
        "if_you_did_not_request_reset": "Se non hai richiesto il reset della password, puoi ignorare questa email.",
        
        # Email di recupero nome utente
        "username_reminder_subject": "Il tuo nome utente",
        "username_reminder_intro": "Hai richiesto il tuo nome utente. Ecco il nome utente associato a questa email:",
        "if_you_did_not_request_username": "Se non hai richiesto il tuo nome utente, puoi ignorare questa email.",
        
        # Unità di tempo
        "hours": "ore",
        "hour": "ora",
        "minutes": "minuti",
        "minute": "minuto",
        
        # Varie
        "hello": "Ciao",
        "regards": "Cordiali saluti",
        "coastal_monitoring_system": "Sistema di Monitoraggio Costiero",
        "cancel": "Annulla",
        "submit": "Invia",
        "continue": "Continua",
        "back": "Indietro",
        "error": "Errore",
        "success": "Successo",
        "warning": "Attenzione",
        "info": "Informazione",
        "loading": "Caricamento in corso...",
        "date": "Data",
        "time": "Ora",
        "generated_by": "Generato da",
        
        # Messaggi per verifica email e reset password
        "user_not_found": "Utente non trovato. Verifica l'indirizzo email.",
        "email_already_verified": "Il tuo account è già stato verificato.",
    }
    
    # Traduzioni in inglese
    translations_en = {
        # Navbar translations
        "home": "Home",
        "chat": "Chat",
        "admin": "Admin",
        "login": "Login",
        "logout": "Logout",
        "register": "Register",
        "profile": "Profile",
        "dark_mode": "Dark Mode",
        "light_mode": "Light Mode",
        
        # Login/registration translations
        "username": "Username",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Confirm password",
        "remember_me": "Remember me",
        "sign_in": "Sign in",
        "sign_up": "Sign up",
        "no_account": "Don't have an account?",
        "already_registered": "Already have an account?",
        "select_avatar": "Select an avatar",
        
        # Credential recovery translations
        "forgot_password": "Forgot password?",
        "forgot_username": "Forgot username?",
        "reset_password": "Reset your password",
        "recover_username": "Recover your username",
        "send_reset_link": "Send reset link",
        "send_username_reminder": "Send username reminder",
        "reset_password_intro": "Enter a new password for your account.",
        "password_reset_success": "Your password has been successfully reset.",
        "enter_new_password": "Enter a new password",
        "password_requirements": "Password must contain at least 8 characters.",
        "passwords_not_match": "Passwords don't match.",
        
        # Email verification translations
        "verify_email": "Verify your email",
        "verification_code": "Verification code",
        "enter_verification_code": "We've sent a verification code to the email address you provided during registration. Enter it below to verify your account.",
        "verify_button": "Verify",
        "resend_code": "Haven't received the code?",
        "resend_verification": "Resend",
        "code_resent": "A new code has been sent to your email.",
        "email_verified": "Email verified successfully!",
        "invalid_code": "Invalid code. Please try again.",
        "expired_code": "The code has expired. We've sent a new code.",
        
        # Verification email
        "verification_email_subject": "Verify your email address",
        "verification_email_intro": "Thank you for registering! To complete your registration, please enter the following verification code on our website:",
        "verification_code_valid_for": "This code is valid for",
        "if_you_did_not_register": "If you didn't request this registration, you can ignore this email.",
        
        # Password reset email
        "reset_password_subject": "Reset your password",
        "reset_password_intro": "We received a request to reset the password for your account. Click the button below to reset your password:",
        "reset_link_valid_for": "This link is valid for",
        "if_you_did_not_request_reset": "If you didn't request a password reset, you can ignore this email.",
        
        # Username recovery email
        "username_reminder_subject": "Your username",
        "username_reminder_intro": "You requested your username. Here's the username associated with this email:",
        "if_you_did_not_request_username": "If you didn't request your username, you can ignore this email.",
        
        # Time units
        "hours": "hours",
        "hour": "hour",
        "minutes": "minutes",
        "minute": "minute",
        
        # Miscellaneous
        "hello": "Hello",
        "regards": "Best regards",
        "coastal_monitoring_system": "Coastal Monitoring System",
        "cancel": "Cancel",
        "submit": "Submit",
        "continue": "Continue",
        "back": "Back",
        "error": "Error",
        "success": "Success",
        "warning": "Warning",
        "info": "Information",
        "loading": "Loading...",
        "date": "Date",
        "time": "Time",
        "generated_by": "Generated by"
    }
    
    # Traduzioni in spagnolo
    translations_es = {
        # Traducciones de la barra de navegación
        "home": "Inicio",
        "chat": "Chat",
        "admin": "Admin",
        "login": "Iniciar sesión",
        "logout": "Cerrar sesión",
        "register": "Registrarse",
        "profile": "Perfil",
        "dark_mode": "Modo oscuro",
        "light_mode": "Modo claro",
        
        # Traducciones para inicio de sesión/registro
        "username": "Nombre de usuario",
        "email": "Correo electrónico",
        "password": "Contraseña",
        "confirm_password": "Confirmar contraseña",
        "remember_me": "Recordarme",
        "sign_in": "Iniciar sesión",
        "sign_up": "Registrarse",
        "no_account": "¿No tienes cuenta?",
        "already_registered": "¿Ya tienes una cuenta?",
        "select_avatar": "Selecciona un avatar",
        
        # Traducciones para recuperación de credenciales
        "forgot_password": "¿Olvidaste tu contraseña?",
        "forgot_username": "¿Olvidaste tu nombre de usuario?",
        "reset_password": "Restablecer tu contraseña",
        "recover_username": "Recuperar tu nombre de usuario",
        "send_reset_link": "Enviar enlace de restablecimiento",
        "send_username_reminder": "Enviar recordatorio de nombre de usuario",
        "reset_password_intro": "Introduce una nueva contraseña para tu cuenta.",
        "password_reset_success": "Tu contraseña ha sido restablecida con éxito.",
        "enter_new_password": "Introduce una nueva contraseña",
        "password_requirements": "La contraseña debe tener al menos 8 caracteres.",
        "passwords_not_match": "Las contraseñas no coinciden.",
        
        # Traducciones para verificación de correo electrónico
        "verify_email": "Verifica tu correo electrónico",
        "verification_code": "Código de verificación",
        "enter_verification_code": "Hemos enviado un código de verificación a la dirección de correo electrónico que proporcionaste durante el registro. Introdúcelo a continuación para verificar tu cuenta.",
        "verify_button": "Verificar",
        "resend_code": "¿No has recibido el código?",
        "resend_verification": "Reenviar",
        "code_resent": "Se ha enviado un nuevo código a tu correo electrónico.",
        "email_verified": "¡Correo electrónico verificado con éxito!",
        "invalid_code": "Código no válido. Inténtalo de nuevo.",
        "expired_code": "El código ha caducado. Hemos enviado un nuevo código.",
        
        # Correo electrónico de verificación
        "verification_email_subject": "Verifica tu dirección de correo electrónico",
        "verification_email_intro": "¡Gracias por registrarte! Para completar tu registro, introduce el siguiente código de verificación en nuestro sitio web:",
        "verification_code_valid_for": "Este código es válido durante",
        "if_you_did_not_register": "Si no has solicitado este registro, puedes ignorar este correo electrónico.",
        
        # Correo electrónico de restablecimiento de contraseña
        "reset_password_subject": "Restablecer tu contraseña",
        "reset_password_intro": "Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. Haz clic en el botón a continuación para restablecer tu contraseña:",
        "reset_link_valid_for": "Este enlace es válido durante",
        "if_you_did_not_request_reset": "Si no has solicitado un restablecimiento de contraseña, puedes ignorar este correo electrónico.",
        
        # Correo electrónico de recuperación de nombre de usuario
        "username_reminder_subject": "Tu nombre de usuario",
        "username_reminder_intro": "Has solicitado tu nombre de usuario. Aquí está el nombre de usuario asociado a este correo electrónico:",
        "if_you_did_not_request_username": "Si no has solicitado tu nombre de usuario, puedes ignorar este correo electrónico.",
        
        # Unidades de tiempo
        "hours": "horas",
        "hour": "hora",
        "minutes": "minutos",
        "minute": "minuto",
        
        # Varios
        "hello": "Hola",
        "regards": "Saludos cordiales",
        "coastal_monitoring_system": "Sistema de Monitoreo Costero",
        "cancel": "Cancelar",
        "submit": "Enviar",
        "continue": "Continuar",
        "back": "Atrás",
        "error": "Error",
        "success": "Éxito",
        "warning": "Advertencia",
        "info": "Información",
        "loading": "Cargando...",
        "date": "Fecha",
        "time": "Hora",
        "generated_by": "Generado por"
    }
    
    # Dizionario di mappatura delle lingue
    language_dict = {
        'it': translations_it,
        'en': translations_en,
        'es': translations_es,
    }
    
    # Dizionario di default in italiano - aggiungiamo altre chiavi necessarie
    translations_it.update({
        # Messaggi di autenticazione
        "user_not_found": "Username non trovato. Controlla e riprova.",
        "account_locked": "Account temporaneamente bloccato. Riprova tra",
        "verify_email_first": "Per favore verifica il tuo indirizzo email prima di accedere.",
        "invalid_password": "Password non valida. Tentativi rimanenti:",
        "remaining_attempts": "tentativi",
        "minutes": "minuti",
        "select_language": "Seleziona lingua",
        "verification_code_sent": "Registrazione completata! Ti abbiamo inviato un codice di verifica via email.",
        "email_send_error": "Non è stato possibile inviare l'email. Contatta l'amministratore.",
        "reset_link_sent": "Ti abbiamo inviato un'email con le istruzioni per reimpostare la password.",
        "username_reminder_sent": "Ti abbiamo inviato un'email con il tuo nome utente.",
        "invalid_reset_link": "Link di reset non valido o scaduto.",
        "expired_reset_link": "Il link di reset è scaduto. Richiedi un nuovo link.",
        "enter_password": "Inserisci una password.",
    })
    
    # Traduzioni in inglese
    translations_en.update({
        "user_not_found": "Username not found. Please check and try again.",
        "account_locked": "Account temporarily locked. Try again in",
        "verify_email_first": "Please verify your email address before logging in.",
        "invalid_password": "Invalid password. Remaining attempts:",
        "remaining_attempts": "attempts",
        "minutes": "minutes",
        "select_language": "Select language",
        "verification_code_sent": "Registration complete! We have sent you a verification code by email.",
        "email_send_error": "Could not send the email. Please contact the administrator.",
        "reset_link_sent": "We have sent you an email with instructions to reset your password.",
        "username_reminder_sent": "We have sent you an email with your username.",
        "invalid_reset_link": "Invalid or expired reset link.",
        "expired_reset_link": "The reset link has expired. Request a new link.",
        "enter_password": "Enter a password.",
    })
    
    # Traduzioni in spagnolo
    translations_es.update({
        "user_not_found": "Nombre de usuario no encontrado. Por favor, comprueba e inténtalo de nuevo.",
        "account_locked": "Cuenta temporalmente bloqueada. Inténtalo de nuevo en",
        "verify_email_first": "Por favor, verifica tu dirección de correo electrónico antes de iniciar sesión.",
        "invalid_password": "Contraseña no válida. Intentos restantes:",
        "remaining_attempts": "intentos",
        "minutes": "minutos",
        "select_language": "Seleccionar idioma",
        "verification_code_sent": "¡Registro completado! Te hemos enviado un código de verificación por correo electrónico.",
        "email_send_error": "No se pudo enviar el correo electrónico. Por favor, contacta con el administrador.",
        "reset_link_sent": "Te hemos enviado un correo electrónico con instrucciones para restablecer tu contraseña.",
        "username_reminder_sent": "Te hemos enviado un correo electrónico con tu nombre de usuario.",
        "invalid_reset_link": "Enlace de restablecimiento no válido o caducado.",
        "expired_reset_link": "El enlace de restablecimiento ha caducado. Solicita un nuevo enlace.",
        "enter_password": "Introduce una contraseña.",
    })
    
    # Aggiungiamo nuove chiavi di traduzione per il processo di registrazione
    translations_it.update({
        # Messaggi di registrazione
        "username_already_used": "Username già in uso. Scegli un altro username.",
        "email_already_registered": "Email già registrata. Utilizza un altro indirizzo email.",
        "registration_error": "Si è verificato un errore durante la registrazione. Riprova.",
    })
    
    # Traduzioni in inglese
    translations_en.update({
        "username_already_used": "Username already in use. Please choose another username.",
        "email_already_registered": "Email already registered. Please use a different email address.",
        "registration_error": "An error occurred during registration. Please try again.",
    })
    
    # Traduzioni in spagnolo
    translations_es.update({
        "username_already_used": "Nombre de usuario ya en uso. Por favor, elige otro nombre de usuario.",
        "email_already_registered": "Correo electrónico ya registrado. Por favor, utiliza otra dirección de correo electrónico.",
        "registration_error": "Ocurrió un error durante el registro. Por favor, inténtalo de nuevo.",
    })
    
    # Restituisci le traduzioni richieste o il default italiano
    return language_dict.get(language, translations_it)

def get_available_languages():
    """Restituisce un dizionario con le lingue disponibili"""
    return {
        'it': 'Italiano',
        'en': 'English',
        'es': 'Español',
    }
