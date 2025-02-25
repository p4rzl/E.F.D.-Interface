#!/bin/bash

echo "======================================================"
echo "Avvio dell'applicazione per il monitoraggio spiagge"
echo "======================================================"

# Assicuriamoci che setuptools sia installato
python -m pip install setuptools wheel --quiet

# Assicuriamoci che email-validator sia installato
python -m pip install email-validator --quiet

# Verifica se ci sono i dati di esempio
if [ ! -d "data" ] || [ ! -f "data/beaches.csv" ]; then
    echo "[1/2] Creazione delle directory e dei dati di esempio..."
    mkdir -p data/risk data/hazard data/curves
    mkdir -p static/reports static/img/avatars
    
    # Crea i dati di esempio usando la funzione in setup_data.py
    python -c "from setup_data import create_sample_data; create_sample_data()"
    echo "      Dati di esempio creati."
else
    echo "[1/2] Directory e dati già esistenti."
fi

# Avvio dell'applicazione che includerà la creazione del database
echo "[2/2] Avvio dell'applicazione..."
echo "      L'applicazione sarà disponibile a: http://localhost:5000"
echo "      Credenziali predefinite: admin/admin"
echo "======================================================"
python index.py
