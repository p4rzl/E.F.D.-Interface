from base64 import b64encode
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from flask.helpers import get_root_path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
from pathlib import Path
import time
import uuid
from xhtml2pdf import pisa
import jinja2
from flask import current_app
from translations import get_translations

root_path = get_root_path(__name__)

# Carica i pesi per rischi e pericoli
risk_weights = pd.read_csv(
    root_path + "/data/risk/risk_weights.csv", 
    comment="#", 
    index_col=0
)

hazard_weights = pd.read_csv(
    root_path + "/data/hazard/hazard_weights.csv",
    comment="#",
    index_col=0
)

def get_risk_report(mode, data):
    env = Environment(loader=FileSystemLoader(root_path + "/templates"))
    
    df = pd.DataFrame(dict(
        r=[
            data["ei"]["risk_value"] * risk_weights.loc["ei", "weight"],
            data["economia"]["risk_value"] * risk_weights.loc["economia", "weight"],
            data["poblacion"]["risk_value"] * risk_weights.loc["poblacion", "weight"],
            data["zp"]["risk_value"] * risk_weights.loc["zp", "weight"]
        ],
        theta=[
            "Rischio per punti di importanza speciale",
            "Danni economici", 
            "Danni alla popolazione",
            "Rischi ambientali"
        ]
    ))
    
    fig = px.line_polar(df, r="r", theta="theta", line_close=True)
    fig.update_traces(fill="toself")

    template_vars = {"data": data}
    template_vars.update({
        "interactive_image": fig.to_html(full_html=False) if mode == "interactive" else None,
        "encoded_image": "data:image/svg;base64," + b64encode(fig.to_image(format="svg")).decode() if mode == "static" else None,
        "mode": mode
    })

    template = env.get_template("risk_template.html")
    html_content = template.render(template_vars)

    return HTML(string=html_content).write_pdf() if mode == "static" else html_content

def get_hazard_report(mode, data):
    env = Environment(loader=FileSystemLoader(root_path + "/templates"))
    data_numeric, data_str = get_hazard_numeric_values(data)
    
    df = create_hazard_dataframe(data_numeric)
    fig = create_hazard_plot(df)

    template_vars = {
        "data": data_str,
        "interactive_image": fig.to_html(full_html=False) if mode == "interactive" else None,
        "encoded_image": "data:image/svg;base64," + b64encode(fig.to_image(format="svg")).decode() if mode == "static" else None,
        "mode": mode
    }

    template = env.get_template("hazard_template.html")
    html_content = template.render(template_vars)

    return HTML(string=html_content).write_pdf() if mode == "static" else html_content

def get_hazard_numeric_values(s):
    data = {}
    data_str = {
        "beach": s["info"]["beach"],
        "region": s["info"]["region"]
    }

    for index, value in s["peligrosidad"].items():
        try:
            data[index] = float(value)
            data_str[index] = f"{float(value):.2g}"
        except:
            data_str[index] = value

    return data, data_str

def create_hazard_dataframe(data):
    df_list = []
    
    # Dataframe principale per la peligrosidad
    df_list.append(pd.DataFrame(dict(
        r=[
            data["flood_depth"] * hazard_weights.loc["flood_depth", "weight"],
            data.get("dry_beach_lost_rel", 0) * hazard_weights.loc["dry_beach_lost_rel", "weight"],
            data.get("coastal_erosion_mean", 0) * hazard_weights.loc["coastal_erosion_mean", "weight"],
            data["flood_area_rel"] * hazard_weights.loc["flood_area_rel", "weight"]
        ],
        theta=[
            "Quota di inondazione",
            "Spiaggia secca persa",
            "Erosione costiera", 
            "Area inondata relativa"
        ],
        Legenda=["Pericolo"]*4
    )))
    
    return pd.concat(df_list)

def create_hazard_plot(df):
    fig = px.line_polar(df, r="r", theta="theta", line_close=True, color="Legenda",
                        color_discrete_sequence=["lightblue", "brown", "orange", "blue", "grey"])
    fig.update_traces(fill="toself")
    fig.update_layout(legend=dict(x=0, y=1, font=dict(size=8)))
    return fig

def get_beaches_graph(data):
    # Implementa la visualizzazione grafica delle spiagge
    rp = int(data["info"]["rp"])
    
    # Carica i dati
    df_beaches = pd.read_csv("data/beaches.csv")
    
    # Crea il grafico
    fig = go.Figure()
    
    # Aggiungi i dati delle spiagge
    fig.add_scatter(
        x=df_beaches["length"],
        y=df_beaches["width"],
        mode="markers",
        marker=dict(size=10),
        text=df_beaches["name"],
        name="Spiagge"
    )
    
    fig.update_layout(
        title=f"Dimensioni spiagge - Periodo di ritorno {rp}",
        xaxis_title="Lunghezza (m)",
        yaxis_title="Larghezza (m)"
    )
    
    return fig.to_html()

def ensure_directory(path):
    """Assicura che una directory esista, creandola se necessario."""
    os.makedirs(path, exist_ok=True)
    return path

def create_pdf(template_path, output_path, context_data):
    """
    Crea un PDF dal template HTML e lo salva nel percorso specificato
    Con gestione errori migliorata e logging dettagliato
    """
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('pdf_generator')
    
    # Verifica percorsi file
    logger.debug(f"Template path: {template_path}")
    logger.debug(f"Output path: {output_path}")
    
    if not os.path.exists(template_path):
        logger.error(f"Il template {template_path} non esiste!")
        return False
    
    # Crea directory di output se non esiste
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Carica il template HTML
        with open(template_path, 'r', encoding='utf-8') as template_file:
            html_template = template_file.read()
            logger.debug(f"Template caricato, lunghezza: {len(html_template)} bytes")
        
        # Prepara l'ambiente Jinja2 con filtri sicuri
        env = jinja2.Environment(autoescape=True)
        
        # Registra filtri personalizzati
        def safe_int(value):
            if value is None:
                return 0
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        
        def safe_format(format_str, value):
            if value is None:
                return "N/A"
            try:
                return format_str % float(value)
            except (ValueError, TypeError):
                return "N/A"
        
        env.filters['int'] = safe_int
        env.filters['format'] = safe_format
        
        # Registra anche i filtri di default
        env.filters['default'] = lambda value, default_value: default_value if value is None else value
        
        # Crea il template e renderizza il contenuto
        template = env.from_string(html_template)
        html_content = template.render(**context_data)
        logger.debug(f"HTML renderizzato, lunghezza: {len(html_content)} bytes")
        
        # Salva HTML renderizzato per debug
        debug_html_path = output_path.replace('.pdf', '_debug.html')
        with open(debug_html_path, "w", encoding='utf-8') as debug_file:
            debug_file.write(html_content)
        logger.debug(f"HTML di debug salvato in: {debug_html_path}")
        
        # Converti HTML in PDF con gestione errori migliorata
        with open(output_path, "wb") as output_file:
            # Configura le opzioni per pisa
            pdf_options = {
                "encoding": "UTF-8",
                "warn": True,
                "xhtml": True,
                "debug": 1  # Abilita il debug
            }
            
            pisa_status = pisa.CreatePDF(
                src=html_content,      # HTML da convertire
                dest=output_file,      # File di output
                encoding='utf-8',
                **pdf_options
            )
        
        # Controlla se ci sono errori
        if pisa_status.err:
            logger.error(f"Errore pisa: {pisa_status.err}")
            # Stampa i log degli errori
            for msg in pisa_status.log:
                if msg[0] == 'error':
                    logger.error(f"PDF Error: {msg[1]}")
            return False
        
        return True
    except Exception as e:
        import traceback
        logger.error(f"Eccezione durante la generazione del PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return False

from pdf_generator import generate_pdf_report

def generate_risk_report(beach_data, username, language='it'):
    """
    Genera un report di rischio per la spiaggia specificata,
    con supporto multilingua e gestione errori migliorata
    """
    # Utilizziamo il nuovo generatore PDF centralizzato
    return generate_pdf_report('risk', beach_data, username, language)

def generate_hazard_report(beach_data, username, language='it'):
    """
    Genera un report di pericolo per la spiaggia specificata,
    con supporto multilingua e gestione errori migliorata
    """
    # Utilizziamo il nuovo generatore PDF centralizzato
    return generate_pdf_report('hazard', beach_data, username, language)