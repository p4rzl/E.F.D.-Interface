# Applicazione di Monitoraggio Spiagge

## Installazione

1. Clona questo repository e installa le dipendenze:
```bash
git clone https://github.com/p4rzl/spagna-login.git
cd spagna-login
chmod +x install_dependencies.sh
./install_dependencies.sh
```

## Avvio dell'applicazione

Hai due opzioni per avviare l'applicazione:

### Opzione 1: Avvio diretto
```bash
python index.py
```

### Opzione 2: Avvio con controlli (consigliato per il primo avvio)
```bash
chmod +x run.sh
./run.sh
```

L'applicazione sarà disponibile all'indirizzo http://localhost:5000

### Account predefinito:
- Username: admin
- Password: admin (o il valore specificato nella variabile d'ambiente ADMIN_PASSWORD)

## Struttura del Progetto

- `index.py` - File principale dell'applicazione Flask
- `models.py` - Definizione dei modelli di dati
- `extensions.py` - Configurazione delle estensioni Flask
- `forms.py` - Definizione dei form per login e registrazione
- `reports.py` - Generazione report PDF
- `setup_data.py` - Creazione dei dati di esempio
- `data/` - Directory contenente i dati delle spiagge e altri dati
- `static/` - File statici (CSS, JS, immagini)
- `templates/` - Template HTML

## Configurazione

Le variabili di ambiente sono configurate nel file `.env`:

- `SECRET_KEY`: Chiave segreta per la generazione dei token di sicurezza
- `ADMIN_PASSWORD`: Password per l'account amministratore
- `FLASK_ENV`: Ambiente di esecuzione ('development' o 'production')
- `MAPBOX_TOKEN`: Token per l'API di Mapbox

## Funzionalità

- Dashboard interattiva per la visualizzazione dei dati delle spiagge
- Visualizzazione della mappa con dati geospaziali
- Simulazione di erosione delle spiagge con una timeline dal 2023 al 2100
- Generazione di report PDF
- Chat in tempo reale tra utenti
- Pannello di amministrazione per la gestione degli utenti

## Note di Sviluppo

I messaggi della chat vengono automaticamente cancellati dopo 3 giorni per ottimizzare le prestazioni.
