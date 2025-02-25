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

def generate_risk_report(beach, username):
    """Genera un report PDF per il rischio di una spiaggia."""
    try:
        # Assicura che la directory reports esista
        report_dir = ensure_directory('static/reports')
        
        # Crea un PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font('Arial', 'B', 16)
        
        # Titolo
        beach_name = beach.get('name', 'Spiaggia sconosciuta')
        pdf.cell(0, 10, f'Report di Rischio: {beach_name}', 0, 1, 'C')
        
        # Informazioni sulla spiaggia
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Generato da: {username}', 0, 1)
        pdf.cell(0, 10, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
        
        pdf.ln(10)
        
        # Caratteristiche della spiaggia
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Caratteristiche della spiaggia', 0, 1)
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Lunghezza: {beach.get("length", "N/A")} m', 0, 1)
        pdf.cell(0, 10, f'Larghezza: {beach.get("width", "N/A")} m', 0, 1)
        pdf.cell(0, 10, f'Indice di rischio: {beach.get("risk_index", "N/A")}', 0, 1)
        pdf.cell(0, 10, f'Tasso di erosione: {beach.get("erosion_rate", "N/A")} m/anno', 0, 1)
        
        pdf.ln(10)
        
        # Simulazione di grafico di previsione
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Previsione di erosione', 0, 1)
        
        # Crea un grafico con matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Usa valori di default se i dati non sono disponibili
        try:
            erosion_rate = float(beach.get('erosion_rate', 0))
        except (ValueError, TypeError):
            erosion_rate = 0.5  # valore di default
            
        try:
            initial_width = float(beach.get('width', 100))
        except (ValueError, TypeError):
            initial_width = 50  # valore di default
        
        years = np.arange(2023, 2100)
        widths = np.maximum(0, initial_width - erosion_rate * (years - 2023))
        
        ax.plot(years, widths, 'b-')
        ax.set_xlabel('Anno')
        ax.set_ylabel('Larghezza spiaggia (m)')
        ax.set_title('Previsione di erosione nel tempo')
        ax.grid(True)
        
        # Salva temporaneamente il grafico
        beach_id = beach.get("id", "unknown")
        chart_path = os.path.join(report_dir, f'erosion_chart_{beach_id}.png')
        plt.savefig(chart_path)
        plt.close()
        
        # Aggiungi il grafico al PDF
        pdf.image(chart_path, x=10, y=None, w=180)
        
        # Aggiungi raccomandazioni
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Raccomandazioni', 0, 1)
        
        pdf.set_font('Arial', '', 12)
        if erosion_rate > 0.5:
            pdf.multi_cell(0, 10, 'Questa spiaggia sta subendo un\'erosione significativa. Si raccomanda di considerare misure di mitigazione come ripascimenti periodici o strutture di protezione costiera.')
        else:
            pdf.multi_cell(0, 10, 'Questa spiaggia mostra un tasso di erosione moderato. Si consiglia di monitorare regolarmente le condizioni e pianificare interventi preventivi.')
        
        # Salva il PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f'risk_report_{beach_id}_{timestamp}.pdf'
        pdf_path = os.path.join(report_dir, pdf_filename)
        pdf.output(pdf_path)
        
        # Rimuovi l'immagine temporanea
        if os.path.exists(chart_path):
            os.remove(chart_path)
        
        return pdf_path
    
    except Exception as e:
        print(f"Errore durante la generazione del report di rischio: {str(e)}")
        traceback.print_exc()
        return None

def generate_hazard_report(beach, username):
    """Genera un report PDF per il pericolo di una spiaggia."""
    # Assicura che la directory reports esista
    report_dir = ensure_directory('static/reports')
    
    # Crea un PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font('Arial', 'B', 16)
    
    # Titolo
    beach_name = beach.get('name', 'Spiaggia sconosciuta')
    pdf.cell(0, 10, f'Report di Pericolo: {beach_name}', 0, 1, 'C')
    
    # Informazioni sulla spiaggia
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Generato da: {username}', 0, 1)
    pdf.cell(0, 10, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    
    pdf.ln(10)
    
    # Caratteristiche della spiaggia
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Valutazione del pericolo', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    
    # Dati di esempio - in un'app reale, questi valori verrebbero dal database
    hazard_factors = {
        'Inondazioni': 'Alto',
        'Erosione costiera': 'Moderato',
        'Maremoti': 'Basso',
        'Tempeste': 'Moderato'
    }
    
    for factor, level in hazard_factors.items():
        pdf.cell(0, 10, f'{factor}: {level}', 0, 1)
    
    pdf.ln(10)
    
    # Crea un grafico a barre per i livelli di pericolo
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Livelli di pericolo', 0, 1)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    factors = list(hazard_factors.keys())
    # Converti livelli testuali in valori numerici
    values = [{'Alto': 3, 'Moderato': 2, 'Basso': 1}[level] for level in hazard_factors.values()]
    
    ax.bar(factors, values, color=['red', 'orange', 'blue', 'orange'])
    ax.set_xlabel('Fattori di pericolo')
    ax.set_ylabel('Livello (1=Basso, 2=Moderato, 3=Alto)')
    ax.set_title('Analisi dei fattori di pericolo')
    ax.set_ylim(0, 4)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Salva temporaneamente il grafico
    chart_path = os.path.join(report_dir, f'hazard_chart_{beach.get("id", "unknown")}.png')
    plt.savefig(chart_path)
    plt.close()
    
    # Aggiungi il grafico al PDF
    pdf.image(chart_path, x=10, y=None, w=180)
    
    # Aggiungi raccomandazioni
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Raccomandazioni di sicurezza', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    
    # Raccomandazioni basate sul pericolo principale
    if 'Alto' in hazard_factors.values():
        pdf.multi_cell(0, 10, 'ATTENZIONE: È stato identificato un alto livello di pericolo per questa spiaggia. Si raccomandano misure di protezione immediate e la limitazione dell\'accesso durante condizioni meteorologiche avverse.')
    else:
        pdf.multi_cell(0, 10, 'Si raccomanda il monitoraggio regolare delle condizioni e l\'implementazione di sistemi di allarme tempestivo per i visitatori della spiaggia.')
    
    # Salva il PDF
    pdf_filename = f'hazard_report_{beach.get("id", "unknown")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    pdf_path = os.path.join(report_dir, pdf_filename)
    pdf.output(pdf_path)
    
    # Rimuovi l'immagine temporanea
    if os.path.exists(chart_path):
        os.remove(chart_path)
    
    return pdf_path