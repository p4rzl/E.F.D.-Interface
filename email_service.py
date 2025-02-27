import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import render_template, url_for, current_app
import requests  # Per Brevo API

class EmailService:
    def __init__(self, app=None):
        self.app = app
        self.service_type = None
        
    def init_app(self, app):
        self.app = app
        
        # Determina il tipo di servizio da usare
        self.service_type = app.config.get('EMAIL_SERVICE_TYPE', os.environ.get('EMAIL_SERVICE_TYPE', 'console'))
        
        # Setup specifico per Brevo/Sendinblue
        if self.service_type == 'brevo':
            self.brevo_api_key = app.config.get('BREVO_API_KEY', os.environ.get('BREVO_API_KEY'))
            self.from_email = app.config.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'))
            self.from_name = app.config.get('MAIL_DEFAULT_NAME', os.environ.get('MAIL_DEFAULT_NAME', 'Sistema Spiagge'))
            
            if not self.brevo_api_key:
                logging.warning("Brevo non configurato correttamente. EMAIL_SERVICE_TYPE impostato su 'console'")
                self.service_type = 'console'
        
        # Setup per Gmail
        elif self.service_type == 'gmail':
            self.smtp_server = "smtp.gmail.com"
            self.smtp_port = 587
            self.gmail_user = app.config.get('GMAIL_USER', os.environ.get('GMAIL_USER'))
            self.gmail_password = app.config.get('GMAIL_APP_PASSWORD', os.environ.get('GMAIL_APP_PASSWORD'))
            self.from_email = self.gmail_user
            
            if not self.gmail_user or not self.gmail_password:
                logging.warning("Gmail non configurato correttamente. EMAIL_SERVICE_TYPE impostato su 'console'")
                self.service_type = 'console'
        
        # Setup per il salvataggio su file
        elif self.service_type == 'file':
            self.log_dir = app.config.get('EMAIL_LOG_DIR', os.environ.get('EMAIL_LOG_DIR', 'logs'))
            if not os.path.exists(self.log_dir):
                try:
                    os.makedirs(self.log_dir)
                except Exception as e:
                    logging.error(f"Impossibile creare la directory per i log delle email: {e}")
                    self.service_type = 'console'
                    
    def send_verification_email(self, user, verification_code):
        """Invia email di verifica all'utente utilizzando il servizio configurato"""
        subject = 'Verifica il tuo indirizzo email'
        html_content = render_template('email/verify_email.html',
                                      user=user, 
                                      verification_code=verification_code)
                                      
        if self.service_type == 'brevo':
            return self._send_via_brevo(user.email, subject, html_content, verification_code)
        elif self.service_type == 'gmail':
            return self._send_via_gmail(user.email, subject, html_content, verification_code)
        elif self.service_type == 'file':
            return self._save_to_file(user.email, subject, html_content, verification_code)
        else:  # default: console
            return self._print_to_console(user.email, subject, verification_code)
    
    def send_password_reset_email(self, user, reset_url):
        """Invia email per il reset della password"""
        subject = 'Reset della tua password'
        html_content = render_template('email/reset_password.html',
                                      user=user, 
                                      reset_url=reset_url)
                                      
        if self.service_type == 'brevo':
            return self._send_via_brevo(user.email, subject, html_content, reset_url)
        elif self.service_type == 'gmail':
            return self._send_via_gmail(user.email, subject, html_content, reset_url)
        elif self.service_type == 'file':
            return self._save_to_file(user.email, subject, html_content, reset_url)
        else:  # default: console
            return self._print_to_console(user.email, subject, reset_url)
            
    def send_username_reminder_email(self, user):
        """Invia email con il promemoria dello username"""
        subject = 'Il tuo nome utente'
        html_content = render_template('email/username_reminder.html',
                                      user=user)
        username = user.username
                                      
        if self.service_type == 'brevo':
            return self._send_via_brevo(user.email, subject, html_content, username)
        elif self.service_type == 'gmail':
            return self._send_via_gmail(user.email, subject, html_content, username)
        elif self.service_type == 'file':
            return self._save_to_file(user.email, subject, html_content, username)
        else:  # default: console
            return self._print_to_console(user.email, subject, f"Username: {username}")

    def _send_via_brevo(self, to_email, subject, html_content, verification_code):
        """Invia email usando l'API di Brevo (ex Sendinblue)"""
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            
            payload = {
                "sender": {
                    "name": self.from_name,
                    "email": self.from_email
                },
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_content
            }
            
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": self.brevo_api_key
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 201:
                print(f"Email inviata con successo a {to_email} tramite Brevo")
                return True
            else:
                print(f"Errore nell'invio dell'email via Brevo: {response.text}")
                return self._print_to_console(to_email, subject, verification_code)
                
        except Exception as e:
            print(f"Errore durante l'invio dell'email via Brevo: {str(e)}")
            return self._print_to_console(to_email, subject, verification_code)
    
    def _send_via_gmail(self, to_email, subject, html_content, verification_code):
        """Invia email usando Gmail SMTP"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            # Converti il contenuto HTML in una parte MIME
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Connessione al server SMTP di Gmail
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()  # Sicurezza TLS
                server.ehlo()
                # Accesso con le credenziali (richiede password app)
                server.login(self.gmail_user, self.gmail_password)
                # Invio email
                server.sendmail(self.from_email, to_email, message.as_string())
            
            print(f"Email inviata con successo a {to_email}")
            return True
                
        except Exception as e:
            print(f"Errore durante l'invio dell'email via Gmail: {str(e)}")
            # Fallback alla console in caso di errore
            return self._print_to_console(to_email, subject, verification_code)
    
    def _save_to_file(self, to_email, subject, html_content, verification_code):
        """Salva l'email in un file di log"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.log_dir}/email_{timestamp}_{to_email.split('@')[0]}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"""
                <!-- Email per: {to_email} -->
                <!-- Oggetto: {subject} -->
                <!-- Codice di verifica: {verification_code} -->
                <!-- Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} -->
                
                {html_content}
                """)
                
            # Salva anche un JSON con i dati essenziali per facile accesso
            with open(f"{self.log_dir}/verification_codes.json", 'a') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "email": to_email,
                    "verification_code": verification_code
                }, f)
                f.write('\n')  # Aggiungi una nuova riga per ogni record
                
            print(f"\n==== EMAIL SALVATA ====")
            print(f"Destinatario: {to_email}")
            print(f"Codice di verifica: {verification_code}")
            print(f"File: {filename}")
            print(f"========================\n")
            return True
            
        except Exception as e:
            print(f"Errore durante il salvataggio dell'email: {str(e)}")
            # Fallback alla console in caso di errore
            return self._print_to_console(to_email, subject, verification_code)
    
    def _print_to_console(self, to_email, subject, verification_code):
        """Stampa il codice di verifica nella console"""
        print("\n==== CODICE DI VERIFICA ====")
        print(f"Destinatario: {to_email}")
        print(f"Oggetto: {subject}")
        print(f"Codice: {verification_code}")
        print("============================\n")
        return True

# Istanza globale del servizio email
email_service = EmailService()
