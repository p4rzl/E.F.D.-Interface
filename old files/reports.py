from base64 import b64encode

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from flask.helpers import get_root_path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

root_path = get_root_path(__name__)

risk_weights = pd.read_csv(
    root_path + "/data/risk/risk_weights.csv", comment="#", index_col=0
)
hazard_weights = pd.read_csv(
    root_path + "/data/hazard/hazard_weights.csv", comment="#", index_col=0
)


def get_risk_report(mode, data):
    env = Environment(loader=FileSystemLoader(root_path + "/templates"))

    df = pd.DataFrame(
        dict(
            r=[
                data["ei"]["risk_value"] * risk_weights.loc["ei", "weight"],
                data["economia"]["risk_value"] * risk_weights.loc["economia", "weight"],
                data["poblacion"]["risk_value"]
                * risk_weights.loc["poblacion", "weight"],
                data["zp"]["risk_value"] * risk_weights.loc["zp", "weight"],
            ],
            theta=[
                "Riesgo a puntos de especial importancia",
                "Daños para la economía",
                "Daños para la población",
                "Riesgos al medio ambiente",
            ],
        )
    )
    fig = px.line_polar(df, r="r", theta="theta", line_close=True)
    fig.update_traces(fill="toself")

    img_interactive = fig.to_html(full_html=False)
    img_static = b64encode(fig.to_image(format="svg")).decode()

    template_vars = {"data": data}

    data["economia"]["cost"] = f"{float(data['economia']['cost']):.2f}"
    data["poblacion"]["npr"] = f"{int(float(data['poblacion']['npr']))}"

    match mode:
        case "static":
            template_vars.update(
                {"encoded_image": "data:image/svg;base64," + img_static}
            )
        case "interactive":
            template_vars.update({"interactive_image": img_interactive})

    template_vars.update({"mode": mode})

    template = env.get_template("risk_template.html")
    html_content = template.render(template_vars)

    match mode:
        case "static":
            return HTML(string=html_content).write_pdf()
        case "interactive":
            return html_content


def get_hazard_report(mode, data):
    env = Environment(loader=FileSystemLoader(root_path + "/templates"))

    data, data_str = get_hazard_numeric_values(data)

    df = pd.DataFrame(
        dict(
            r=[
                data["flood_depth"] * hazard_weights.loc["flood_depth", "weight"],
                data["dry_beach_lost_rel"]
                * hazard_weights.loc["dry_beach_lost_rel", "weight"],
                data["coastal_erosion_mean"]
                * hazard_weights.loc["coastal_erosion_mean", "weight"],
                data["flood_area_rel"] * hazard_weights.loc["flood_area_rel", "weight"],
            ],
            theta=[
                "Cota de inundación",
                "Playa seca perdida",
                "Erosión costera",
                "Área inundada relativa",
            ],
            Leyenda="Peligrosidad",
        )
    )

    df_nmm = pd.DataFrame(
        dict(
            r=[
                data["flood_depth"]
                * data["slr"]
                * 0.01
                * hazard_weights.loc["flood_depth", "weight"],
                0,
                0,
                0,
            ],
            theta=[
                "Cota de inundación",
                "Playa seca perdida",
                "Erosión costera",
                "Área inundada relativa",
            ],
            Leyenda="Nivel medio del mar",
        )
    )

    df_ma = pd.DataFrame(
        dict(
            r=[
                (
                    data["flood_depth"] * data["slr"] * 0.01
                    + data["flood_depth"] * data["ma"] * 0.01
                )
                * hazard_weights.loc["flood_depth", "weight"],
                0,
                0,
                0,
            ],
            theta=[
                "Cota de inundación",
                "Playa seca perdida",
                "Erosión costera",
                "Área inundada relativa",
            ],
            Leyenda="Marea astronómica",
        )
    )

    df_cc = pd.DataFrame(
        dict(
            r=[
                data["flood_depth"] * hazard_weights.loc["flood_depth", "weight"],
                0,
                0,
                0,
            ],
            theta=[
                "Cota de inundación",
                "Playa seca perdida",
                "Erosión costera",
                "Área inundada relativa",
            ],
            Leyenda="Nivel asociado a condiciones climáticas",
        )
    )

    df_suelos = pd.DataFrame(
        dict(
            r=[
                0,
                0,
                0,
                data["low_permeability"]
                * data["flood_area_rel"]
                * hazard_weights.loc["flood_area_rel", "weight"],
            ],
            theta=[
                "Cota de inundación",
                "Playa seca perdida",
                "Erosión costera",
                "Área inundada relativa",
            ],
            Leyenda="Suelos de baja permeabilidad",
        )
    )

    df = pd.concat([df, df_cc, df_ma, df_nmm, df_suelos], axis=0)

    fig = px.line_polar(
        df,
        r="r",
        theta="theta",
        line_close=True,
        color="Leyenda",
        color_discrete_sequence=["lightblue", "brown", "orange", "blue", "grey"],
    )

    fig.update_traces(fill="toself")
    fig.update_layout(
        legend=dict(
            x=0,
            y=1,
            font=dict(size=8),
        )
    )

    img_interactive = fig.to_html(full_html=False)
    img_static = b64encode(fig.to_image(format="svg")).decode()

    template_vars = {"data": data_str}

    match mode:
        case "static":
            template_vars.update(
                {"encoded_image": "data:image/svg;base64," + img_static}  # type: ignore
            )  # type: ignore
        case "interactive":
            template_vars.update({"interactive_image": img_interactive})

    template_vars.update({"mode": mode})  # type: ignore

    template = env.get_template("hazard_template.html")
    html_content = template.render(template_vars)

    match mode:
        case "static":
            return HTML(string=html_content).write_pdf()
        case "interactive":
            return html_content


def get_hazard_numeric_values(s):
    data = {}
    data_str = {
        "beach": s["info"]["beach"],
        "region": s["info"]["region"],
    }

    for index, value in s["peligrosidad"].items():
        try:
            new_value = float(value)
            new_value_str = "{:.2g}".format(new_value)

            data[index] = new_value
        except Exception:
            new_value_str = value

        data_str[index] = new_value_str

    return data, data_str


def get_beaches_graph(data):
    rp = int(data["info"]["rp"])  # noqa: F841

    df_resultados = pd.read_excel(
        data["info"]["assets_folder"] + "resultados_riesgo.xlsx"
    )

    x = np.linspace(0, 5, 100)
    y = np.linspace(0, 5, 101)

    [X, Y] = np.meshgrid(x, y)
    f = (np.sin(np.pi * X / 10) * np.sin(np.pi * Y / 10)) ** 2

    risk_values = {
        "Nulo": 0,
        "Muy bajo": 1,
        "Bajo": 2,
        "Medio": 3,
        "Alto": 4,
        "Muy alto": 5,
    }

    df_resultados = df_resultados.assign(
        total_risk_value=df_resultados["poblacion"].map(risk_values)
        * risk_weights.loc["poblacion", "weight"]
        + df_resultados["economia"].map(risk_values)
        * risk_weights.loc["economia", "weight"]
        + df_resultados["ei"].map(risk_values) * risk_weights.loc["ei", "weight"]
        + df_resultados["medio_ambiente"].map(risk_values)
        * risk_weights.loc["zp", "weight"]
    )

    conditions = [
        (df_resultados["total_risk_value"] >= 0)
        & (df_resultados["total_risk_value"] < 1),
        (df_resultados["total_risk_value"] >= 1)
        & (df_resultados["total_risk_value"] < 2),
        (df_resultados["total_risk_value"] >= 2)
        & (df_resultados["total_risk_value"] < 3),
        (df_resultados["total_risk_value"] >= 3)
        & (df_resultados["total_risk_value"] < 4),
        (df_resultados["total_risk_value"] >= 4)
        & (df_resultados["total_risk_value"] < 5),
        (df_resultados["total_risk_value"] >= 5)
        & (df_resultados["total_risk_value"] < 6),
    ]

    df_resultados["total_risk"] = np.select(conditions, risk_values.keys())  # type: ignore

    hazard_values = {
        "Muy leve": 0,
        "Leve": 1,
        "Moderada": 2,
        "Alta": 3,
        "Muy alta": 4,
    }

    df_resultados = df_resultados.assign(
        total_hazard_value=df_resultados["hazard_flood"].map(hazard_values)
        * hazard_weights.loc["total_flood", "weight"]
        + df_resultados["hazard_dry_beach_lost"].map(hazard_values)
        * hazard_weights.loc["dry_beach_lost_rel", "weight"]
        + df_resultados["hazard_coastal_erosion"].map(hazard_values)
        * hazard_weights.loc["coastal_erosion_mean", "weight"]
    )

    columns = [
        "rp",
        "beach",
        "total_risk",
        "total_risk_value",
        "total_hazard",
        "total_hazard_value",
    ]

    df_resultados = df_resultados[columns]
    df_resultados = df_resultados.dropna(subset=columns)

    contour = go.Contour(x=x, y=y, z=f, hoverinfo="skip")
    data = [contour]

    fig = go.Figure(
        data=data,
        layout=go.Layout(title=go.layout.Title(text=f"Período de retorno {rp}")),
    )

    df_resultados_filtered = df_resultados.query("rp == @rp")

    df_resultados_filtered = (
        df_resultados_filtered.reset_index()
        .groupby(["total_risk_value", "total_hazard_value"])
        .agg(
            {
                "beach": lambda x: "<br>".join(x),
                "total_risk": "first",
                "total_hazard": "first",
            }
        )
        .reset_index()
    )

    fig.add_scatter(
        x=df_resultados_filtered["total_risk_value"],
        y=df_resultados_filtered["total_hazard_value"],
        hoverinfo="text",
        hovertext="<b>Riesgo:</b> "
        + df_resultados_filtered["total_risk"]
        + "<br><b>Peligrosidad:</b> "
        + df_resultados_filtered["total_hazard"]
        + "<br><b>Playas:</b><br>"
        + df_resultados_filtered["beach"],
        mode="markers",
        marker=dict(size=12, color="white"),
    )

    return fig.to_html()
