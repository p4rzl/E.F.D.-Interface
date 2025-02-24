import dash
from dash.dependencies import Input, Output
from flask import session

from .layout import (
    get_beaches_select,
    get_hazard_table,
    get_layers,
    get_map_bounds,
    get_risk_table,
    get_stretches,
)


def register_callbacks(app):
    """
    Registers the callbacks for the Dash application.

    Args:
        app (dash.Dash): The Dash application instance.
    """

    @app.callback(
        [
            Output("stretch", "data"),
            Output("beach", "data"),
            Output("beach", "value"),
            Output("map", "children"),
            Output("alert", "hide"),
            Output("map", "viewport"),
            Output("risk_table", "children"),
            Output("hazard_table", "children"),
        ],
        [
            Input("ph_unit", "value"),
            Input("stretch", "value"),
            Input("beach", "value"),
            Input("r_period", "value"),
        ],
    )
    def update_layers(ph_unit, stretch, beach, r_period):
        """
        Updates the layers, tables, and map based on the selected inputs.

        Args:
            ph_unit (str): The selected physiographic unit.
            stretch (str): The selected stretch.
            beach (str): The selected beach.
            r_period (str): The selected return period.

        Returns:
            tuple: A tuple containing the updated data for stretches, beaches, map layers, alert visibility, map viewport, risk table, and hazard table.
        """
        ctx = dash.callback_context

        if not ctx.triggered:
            trigger_id = None
        else:
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id in ["ph_unit", "stretch", None]:
            beaches, next_beach = get_beaches_select(ph_unit, stretch)

            layers, alert, _, data = get_layers(next_beach, r_period, app)

            risk_table = get_risk_table(data)
            hazard_table = get_hazard_table(data)

            session["data"] = {
                key: df.to_json(orient="split") for key, df in data.items()
            }

            return (
                get_stretches(ph_unit),
                beaches,
                next_beach,
                layers,
                alert,
                get_map_bounds(next_beach, r_period, app),
                risk_table,
                hazard_table,
            )
        elif trigger_id == "beach":
            layers, alert, _, data = get_layers(beach, r_period, app)

            risk_table = get_risk_table(data)
            hazard_table = get_hazard_table(data)

            session["data"] = {
                key: df.to_json(orient="split") for key, df in data.items()
            }

            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                layers,
                alert,
                get_map_bounds(beach, r_period, app),
                risk_table,
                hazard_table,
            )
        else:
            layers, alert, _, data = get_layers(beach, r_period, app)

            risk_table = get_risk_table(data)
            hazard_table = get_hazard_table(data)

            session["data"] = {
                key: df.to_json(orient="split") for key, df in data.items()
            }

            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                layers,
                alert,
                dash.no_update,
                risk_table,
                hazard_table,
            )
