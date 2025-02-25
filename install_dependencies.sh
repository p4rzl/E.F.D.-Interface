#!/bin/bash

echo "======================================================"
echo "Installazione delle dipendenze per l'applicazione"
echo "======================================================"

# Aggiorna pip e installa setuptools
echo "[1/5] Aggiornamento di pip e strumenti di base..."
python -m pip install --upgrade pip setuptools wheel

# Installa dipendenze di base
echo "[2/5] Installazione dipendenze di base..."
pip install flask flask-login flask-sqlalchemy flask-wtf python-dotenv email-validator flask-socketio

# Installa altre dipendenze
echo "[3/5] Installazione dipendenze per elaborazione dati e visualizzazione..."
pip install pandas numpy matplotlib plotly fpdf reportlab pillow jinja2

echo "[4/5] Creazione delle directory necessarie per i dati..."
# Crea le directory necessarie
mkdir -p data/risk
mkdir -p data/hazard
mkdir -p data/curves
mkdir -p static/reports
mkdir -p static/img/avatars

# Se non esiste il file .env, creane uno di esempio
if [ ! -f .env ]; then
    echo "[5/5] Creazione file .env di esempio..."
    echo "SECRET_KEY=una_chiave_segreta_molto_lunga_e_complessa" > .env
    echo "ADMIN_PASSWORD=admin" >> .env
    echo "FLASK_ENV=development" >> .env
    echo "MAPBOX_TOKEN=pk.eyJ1IjoicDRyemwiLCJhIjoiY203ZWw3emd5MGN0eDJrc2V0eTdpcWN2ZCJ9.4VJRSR4REamVL1Qdw1wVdA" >> .env
else
    echo "[5/5] File .env già esistente, saltato..."
fi

echo "======================================================"
echo "Installazione completata!"
echo "Per avviare l'applicazione, esegui: python index.py"
echo "======================================================"
