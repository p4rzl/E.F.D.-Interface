from base64 import b64encode
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from flask.helpers import get_root_path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

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