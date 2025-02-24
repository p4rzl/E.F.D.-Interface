import json
from pathlib import Path

import dash
import dash_leaflet as dl
import dash_mantine_components as dmc
import geopandas
import pandas as pd
from dash import html
from dash_iconify import DashIconify
from flask.helpers import get_root_path

from .data import (
    get_beach_name,
    get_beaches,
    get_ph_unit,
    get_ph_units,
    get_region_name,
    get_strech,
    get_stretches,
)

root_path = get_root_path(__name__)

roi_relative_folder = "roi"
roi_path = roi_relative_folder + "/{beach}/{rp}/roi.geojson"

# data_sources_relative_folder = "data_sources/"
risk_relative_folder = "risk/"

relative_path = root_path + "/../../../"
results_folder = relative_path + "datos_riesgo"


basemaps = {
    "Satélite": "clgc5fnj6001l01tahdp7f9cu",
    # "Topobatimetría": "clilstsgf00jc01pfawmb6w5p",
}

# url = (
#     "https://api.mapbox.com/styles/v1/marcussanta/{id_map}"
#     "/tiles/{{z}}/{{x}}/{{y}}"
#     "?access_token=" + open(root_path + "/.mapbox_token").read()
# )

url = (
    "https://api.mapbox.com/v4/mapbox.satellite/{{z}}/{{x}}/{{y}}@2x.jpg90?access_token="
    + open(root_path + "/.mapbox_token").read()
)

attribution = """
© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a>
© <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a>
<strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>
Improve this map</a></strong>
"""

common_layout = dict(
    margin=dict(t=0, b=0, l=0, r=30),
    showlegend=False,
    modebar={"orientation": "v"},
)

common_config = dict(
    displayModeBar=True,
)

risk_weights = pd.read_csv(
    root_path + "/data/risk/risk_weights.csv", comment="#", index_col=0
)


def get_layout(dash_app):
    """
    Generates the layout for the Dash application.

    Args:
        dash_app (dash.Dash): The Dash application instance.

    Returns:
        dmc.MantineProvider: The layout wrapped in a MantineProvider for styling.
    """
    CONTENT_STYLE = {
        "margin-top": "1rem",
        "margin-left": "2rem",
        "margin-right": "2rem",
    }

    alert = dmc.Alert(
        "Hay capas que faltan para esta playa",
        title="¡Aviso!",
        color="red",
        hide=True,
        id="alert",
    )

    r_period = [
        dmc.Text(
            [
                "Período de retorno",
                html.A(
                    dmc.ActionIcon(
                        DashIconify(icon="mdi:report-box-outline"),
                        id="action-icon",
                        variant="filled",
                        color="primary",
                    ),
                    href="/app/riesgo/beaches-graph",
                    target="_blank",
                ),
            ],
            className="mantine-ittua2",
            m="lg",
            id="r_period-label",
        ),
        dmc.SegmentedControl(
            data=[{"label": x, "value": x} for x in ["10", "30", "50", "100", "500"]],
            value="10",
            color="purple",
            m="lg",
            id="r_period",
        ),
    ]

    ph_units = get_ph_units()
    ph_unit = dmc.Select(
        label="Unidad fisiográfica",
        value="A01",
        data=[{"value": x, "label": x} for x in ph_units],
        m="lg",
        id="ph_unit",
    )

    default_stretches = get_stretches("A01")
    stretch = dmc.Select(
        label="Tramo",
        value=default_stretches[0],
        data=default_stretches,
        m="lg",
        id="stretch",
    )

    default_beaches = get_beaches_select("A01", "001")
    beach = dmc.Select(
        label="Playa",
        value=default_beaches[1],
        data=default_beaches[0],
        m="lg",
        id="beach",
    )

    m = dl.MapContainer(
        center=(37, -4),
        zoom=7,
        style={
            "width": "100%",
            "height": "80vh",
        },
        id="map",
    )

    risk_table = dmc.Table(
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        m="lg",
        id="risk_table",
    )

    hazard_table = dmc.Table(
        striped=True,
        highlightOnHover=True,
        withTableBorder=True,
        m="lg",
        id="hazard_table",
    )

    layout = dmc.Grid(
        children=[
            dmc.GridCol(dmc.Title("Riesgo y Peligrosidad", order=1), span=12),
            dmc.GridCol(dmc.Divider(variant="solid"), span=12),
            dmc.GridCol(html.Div(m), span=8),
            dmc.GridCol(
                [
                    alert,
                    *r_period,
                    ph_unit,
                    stretch,
                    beach,
                    dmc.Space(h=8),
                    risk_table,
                    dmc.Space(h=4),
                    hazard_table,
                ],
                span=4,
            ),
        ],
        style=CONTENT_STYLE,
    )

    return dmc.MantineProvider(
        theme={
            "fontFamily": "'Inter', sans-serif",
            "primaryColor": "indigo",
            "headings": {
                "fontFamily": "Roboto, sans-serif",
                "sizes": {
                    "h1": {
                        "fontSize": 30,
                    },
                },
            },
        },
        children=layout,
    )


def get_layers(beach, rp, dash_app):
    """
    Retrieves the layers for the map based on the specified beach and return period.

    Args:
        beach (str): The beach identifier.
        rp (str): The return period.
        dash_app (dash.Dash): The Dash application instance.

    Returns:
        list: A list containing the layers, hide_alert flag, GeoDataFrames, and data.
    """
    layers = []
    gdfs = {}
    data = {}

    hide_alert = True

    basemap_checked = True
    for name, id_map in basemaps.items():
        layers.append(
            dl.BaseLayer(
                dl.TileLayer(
                    url=url.format(id_map=id_map),
                    attribution=attribution,
                    tileSize=512,
                    maxZoom=19,
                    zoomOffset=-1,
                    opacity=0.6,
                ),
                name=name,
                checked=basemap_checked,
            )
        )
        basemap_checked = True

    # if hide_alert:
    data["info"] = pd.Series()

    local_assets_path = dash_app.config.assets_folder

    data["info"]["beach"] = get_beach_name(beach)
    data["info"]["region"] = get_region_name(beach)
    data["info"]["rp"] = rp
    data["info"]["assets_folder"] = local_assets_path

    roi = geopandas.read_file(local_assets_path + roi_path.format(beach=beach, rp=rp))

    # assets_path = dash_app.config.assets_url_path + "/"

    # Poblacion layer
    # layer_poblacion, poblacion_data = poblacion(
    #     beach,
    #     rp,
    #     assets_path,
    #     data_sources_relative_folder,
    #     risk_relative_folder,
    # )
    folder = risk_relative_folder + f"{beach}/{rp}/"
    filename = folder + "poblacion"

    layer_poblacion = filename + ".geojson"
    poblacion_data = filename + "-data.csv"

    add_layer(
        layers,
        layer_poblacion,
        dash_app,
        "Población",
        "dark_gray",
        0.5,
        stroke_color="dark_gray",
        stroke_opacity=0.5,
    )

    poblacion_layer_file = local_assets_path + layer_poblacion
    poblacion_data_file = local_assets_path + poblacion_data

    if not Path(poblacion_layer_file).exists():
        hide_alert = False
    else:
        gdfs["poblacion"] = geopandas.read_file(poblacion_layer_file)

    if not Path(poblacion_data_file).exists():
        hide_alert = False
    else:
        data["poblacion"] = pd.read_csv(poblacion_data_file, index_col=0).squeeze(
            "columns"
        )

    # EI layer
    # layer_ei, ei_data = ei(
    #     roi,
    #     beach,
    #     rp,
    #     assets_path,
    #     data_sources_relative_folder,
    #     risk_relative_folder,
    # )
    folder = risk_relative_folder + f"{beach}/{rp}/"
    filename = folder + "ei"

    layer_ei = filename + ".geojson"
    ei_data = filename + "-data.csv"

    add_layer(
        layers,
        layer_ei,
        dash_app,
        "Especial importancia",
        "red",
        0.5,
        stroke_color="red",
        stroke_opacity=0.5,
    )
    hide_alert = False

    ei_layer_file = local_assets_path + layer_ei
    ei_data_file = local_assets_path + ei_data

    if not Path(ei_layer_file).exists():
        hide_alert = False
    else:
        gdfs["ei"] = geopandas.read_file(ei_layer_file)

    if not Path(ei_layer_file).exists():
        hide_alert = False
    else:
        data["ei"] = pd.read_csv(ei_data_file, index_col=0).squeeze("columns")

    # ZP layer
    # layer_zp, zp_data = zp(
    #     roi,
    #     gdfs["ei"],
    #     beach,
    #     rp,
    #     assets_path,
    #     data_sources_relative_folder,
    #     risk_relative_folder,
    # )
    folder = risk_relative_folder + f"{beach}/{rp}/"
    filename = folder + "medio_ambiente"

    layer_zp = filename + ".geojson"
    zp_data = filename + "-data.csv"

    add_layer(
        layers,
        layer_zp,
        dash_app,
        "Zonas protegidas",
        "green",
        0.5,
        stroke_color="green",
        stroke_opacity=0.5,
    )
    hide_alert = False

    zp_layer_file = local_assets_path + layer_zp
    zp_data_file = local_assets_path + zp_data

    if not Path(zp_layer_file).exists():
        hide_alert = False
    else:
        gdfs["zp"] = geopandas.read_file(zp_layer_file)

    if not Path(zp_layer_file).exists():
        hide_alert = False
    else:
        data["zp"] = pd.read_csv(zp_data_file, index_col=0).squeeze("columns")

    # Economia layer
    # layer_economia, economia_data = economia(
    #     roi,
    #     beach,
    #     rp,
    #     assets_path,
    #     data_sources_relative_folder,
    #     risk_relative_folder,
    #     results_folder,
    # )

    folder = risk_relative_folder + f"{beach}/{rp}/"
    filename = folder + "economia"

    layer_economia = filename + ".geojson"
    economia_data = filename + "-data.csv"

    add_layer(
        layers,
        layer_economia,
        dash_app,
        "Economía",
        "blue",
        0.5,
        stroke_color="blue",
        stroke_opacity=0.5,
    )
    hide_alert = False

    economia_layer_file = local_assets_path + layer_economia
    economia_data_file = local_assets_path + economia_data

    if not Path(economia_layer_file).exists():
        hide_alert = False
    else:
        gdfs["economia"] = geopandas.read_file(economia_layer_file)

    if not Path(economia_layer_file).exists():
        hide_alert = False
    else:
        data["economia"] = pd.read_csv(economia_data_file, index_col=0).squeeze(
            "columns"
        )

    # Peligrosidad layer
    # peligrosidad_data = peligrosidad(
    #     beach,
    #     rp,
    #     assets_path,
    #     data_sources_relative_folder,
    #     risk_relative_folder,
    #     results_folder,
    # )
    filename = folder + "peligrosidad"
    peligrosidad_data = filename + "-data.csv"

    peligrosidad_data_file = local_assets_path + peligrosidad_data

    if not Path(peligrosidad_data_file).exists():
        hide_alert = False
    else:
        data["peligrosidad"] = pd.read_csv(peligrosidad_data_file, index_col=0).squeeze(
            "columns"
        )

    # ROI layer
    add_layer(
        layers,
        roi_path.format(beach=beach, rp=rp),
        dash_app,
        "Región de interés",
        "yellow",
        0.1,
        stroke_color="yellow",
        stroke_opacity=0.1,
    )
    hide_alert = False

    ph_unit = get_ph_unit(beach)
    stretch = get_strech(beach)

    # Linea orilla layer
    add_layer(
        layers,
        (
            "results_analysis/01_Linea_orilla_2100/"
            f"{ph_unit}/{ph_unit}-{stretch}/l_orilla_ini_{beach}.geojson"
        ),
        dash_app,
        "Línea orilla inicial",
        "blue",
        0.6,
    )
    hide_alert = False

    add_layer(
        layers,
        (
            "results_analysis/05_Linea_nivel_medio_2100/"
            f"{ph_unit}/{ph_unit}-{stretch}/l_nivel_m_ini_{beach}.geojson"
        ),
        dash_app,
        "Línea nivel medio",
        "blue",
        0.6,
    )
    hide_alert = True

    return [
        dl.LayersControl(layers, collapsed=False),
        hide_alert,
        gdfs,
        data,
    ]


def get_beaches_select(ph_unit, stretch):
    """
    Retrieves the available beaches for the specified physiographic unit and stretch.

    Args:
        ph_unit (str): The physiographic unit identifier.
        stretch (str): The stretch identifier.

    Returns:
        tuple: A tuple containing a list of beach options and the default beach.
    """
    beaches = get_beaches(ph_unit, stretch)

    if beaches:
        return [
            {"value": value, "label": label} for value, label in beaches.items()
        ], next(iter(beaches))
    else:
        return [
            {"value": value, "label": label} for value, label in beaches.items()
        ], None


def get_map_bounds(beach, rp, dash_app):
    """
    Retrieves the map bounds for the specified beach and return period.

    Args:
        beach (str): The beach identifier.
        rp (str): The return period.
        dash_app (dash.Dash): The Dash application instance.

    Returns:
        dict: A dictionary containing the map bounds and transition type.
    """
    return_bounds = dash.no_update

    roi_pathfile = dash_app.config.assets_folder + roi_path.format(beach=beach, rp=rp)

    if Path(roi_pathfile).exists():
        roi = geopandas.read_file(roi_pathfile)
        bounds = [
            [roi.bounds.miny.item(), roi.bounds.minx.item()],
            [roi.bounds.maxy.item(), roi.bounds.maxx.item()],
        ]
        return_bounds = {"bounds": bounds, "transition": "flyToBounds"}

    # return_bounds = {
    #     "center": [40.7128, -74.0060],  # Ejemplo de coordenadas
    #     "zoom": 12,  # Ejemplo de nivel de zoom
    # }

    return return_bounds


def get_empty_graph(message="Loading...", fontsize=18):
    """
    Generates an empty graph layout with a loading message.

    Args:
        message (str): The loading message to display.
        fontsize (int): The font size of the loading message.

    Returns:
        dict: A dictionary containing the layout configuration for the empty graph.
    """
    empty = {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "annotations": [
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": fontsize},
            }
        ],
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"t": 0, "b": 0, "l": 20, "r": 30},
        "modebar": {"orientation": "v"},
        "coloraxis_colorbar_x": -0.15,
    }

    empty.update(common_layout)

    return {"layout": empty}


def get_risk_table(data):
    """
    Generates the risk table based on the provided data.

    Args:
        data (dict): The data containing risk information.

    Returns:
        list: A list of HTML elements representing the risk table.
    """
    risk_table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Riesgo"),
                    html.Th(""),
                    html.Th(
                        html.A(
                            dmc.ActionIcon(
                                DashIconify(icon="mdi:report-box-outline"),
                                id="action-icon",
                                variant="filled",
                                color="primary",
                            ),
                            href="/app/riesgo/risk-report",
                            target="_blank",
                        ),
                    ),
                ]
            )
        )
    ]

    risk_poblacion = data["poblacion"]["risk"]
    risk_economia = data["economia"]["risk"]
    risk_ei = data["ei"]["risk"]
    risk_zp = data["zp"]["risk"]

    risk_row1 = html.Tr(
        [
            html.Td("Población"),
            html.Td(f"{int(float(data['poblacion']['npr']))} hab."),
            html.Td(risk_poblacion),
        ]
    )
    risk_row2 = html.Tr(
        [
            html.Td("Economía"),
            html.Td(f"{float(data['economia']['cost']):.2f}€"),
            html.Td(risk_economia),
        ]
    )
    risk_row3 = html.Tr(
        [html.Td("Puntos de especial importancia"), html.Td(), html.Td(risk_ei)]
    )
    risk_row4 = html.Tr([html.Td("Medio ambiente"), html.Td(), html.Td(risk_zp)])

    risk_table_body = [html.Tbody([risk_row1, risk_row2, risk_row3, risk_row4])]

    risk_values = {
        "Nulo": 0,
        "Muy bajo": 1,
        "Bajo": 2,
        "Medio": 3,
        "Alto": 4,
        "Muy alto": 5,
    }

    risk_total_value = int(
        (
            risk_values[risk_poblacion] * risk_weights.loc["poblacion", "weight"]  # type: ignore
            + risk_values[risk_economia] * risk_weights.loc["economia", "weight"]  # type: ignore
            + risk_values[risk_ei] * risk_weights.loc["ei", "weight"]  # type: ignore
            + risk_values[risk_zp] * risk_weights.loc["zp", "weight"]  # type: ignore
        )
    )

    total_risk = [
        clave for clave in risk_values.keys() if risk_values[clave] == risk_total_value
    ][0]

    data["poblacion"]["risk_value"] = risk_values[risk_poblacion]
    data["economia"]["risk_value"] = risk_values[risk_economia]
    data["ei"]["risk_value"] = risk_values[risk_ei]
    data["zp"]["risk_value"] = risk_values[risk_zp]

    data["risk"] = pd.Series()
    data["risk"]["total"] = total_risk
    data["risk"]["total_value"] = risk_total_value

    risk_table_footer = [
        html.Tfoot(
            html.Tr(
                [
                    html.Th("TOTAL"),
                    html.Th(""),
                    html.Th(total_risk),
                ]
            )
        )
    ]

    content = risk_table_header + risk_table_body + risk_table_footer

    return content


def get_hazard_table(data):
    """
    Generates the hazard table based on the provided data.

    Args:
        data (dict): The data containing hazard information.

    Returns:
        list: A list of HTML elements representing the hazard table.
    """
    hazard_table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Peligrosidad"),
                    html.Th(
                        html.A(
                            dmc.ActionIcon(
                                DashIconify(icon="mdi:report-box-outline"),
                                id="action-icon",
                                variant="filled",
                                color="primary",
                            ),
                            href="/app/riesgo/hazard-report",
                            target="_blank",
                        ),
                    ),
                ]
            )
        )
    ]

    hazard_dry_beach_lost = data["peligrosidad"]["hazard_dry_beach_lost"]
    hazard_coastal_erosion = data["peligrosidad"]["hazard_coastal_erosion"]
    hazard_flood = data["peligrosidad"]["hazard_flood"]
    total_hazard = data["peligrosidad"]["total_hazard"]

    risk_row1 = html.Tr(
        [
            html.Td("Área seca perdida"),
            html.Td(hazard_dry_beach_lost),
        ]
    )
    risk_row2 = html.Tr(
        [
            html.Td("Retroceso de la costa"),
            html.Td(hazard_coastal_erosion),
        ]
    )
    risk_row3 = html.Tr([html.Td("Inundación"), html.Td(hazard_flood)])

    hazard_table_body = [html.Tbody([risk_row1, risk_row2, risk_row3])]

    hazard_table_footer = [
        html.Tfoot(
            html.Tr(
                [
                    html.Th("TOTAL"),
                    html.Th(total_hazard),
                ]
            )
        )
    ]

    hazard_values = {
        "Muy leve": 0,
        "Leve": 1,
        "Moderada": 2,
        "Alta": 3,
        "Muy alta": 4,
    }

    data["peligrosidad"]["dry_beach_lost_value"] = hazard_values[hazard_dry_beach_lost]
    data["peligrosidad"]["coastal_erosion_value"] = hazard_values[
        hazard_coastal_erosion
    ]
    data["peligrosidad"]["flood_value"] = hazard_values[hazard_flood]

    content = hazard_table_header + hazard_table_body + hazard_table_footer

    return content


def add_layer(
    layers,
    data,
    dash_app,
    name,
    color,
    opacity,
    checked=True,
    stroke_color="white",
    stroke_opacity=0.2,
):
    """
    Adds a layer to the map.

    Args:
        layers (list): The list of existing layers.
        data (str or GeoDataFrame): The data for the layer.
        dash_app (dash.Dash): The Dash application instance.
        name (str): The name of the layer.
        color (str): The fill color of the layer.
        opacity (float): The fill opacity of the layer.
        checked (bool): Whether the layer is checked by default.
        stroke_color (str): The stroke color of the layer.
        stroke_opacity (float): The stroke opacity of the layer.

    Returns:
        bool: A flag indicating whether to hide the alert.
    """
    hide_alert = True
    layer = None
    source = {}

    if not Path(dash_app.config.assets_folder + data).exists():
        hide_alert = False
    else:
        source = {
            "url": dash_app.get_relative_path(
                "/" + dash_app.config.assets_url_path + "/" + data
            )
        }
        # source = dash_app.config.assets_folder + data

    if hide_alert:
        layer = dl.Overlay(
            dl.GeoJSON(
                **source,
                # data=source,
                options={
                    "style": {
                        "color": stroke_color,
                        "opacity": stroke_opacity,
                        "fillColor": color,
                        "fillOpacity": opacity,
                    }
                },
            ),
            name=name,
            checked=checked,
        )

        layers.append(layer)

    return hide_alert
