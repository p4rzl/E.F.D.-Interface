import io

import pandas as pd
from flask import current_app as app
from flask import send_file, session

from .reports import get_beaches_graph, get_hazard_report, get_risk_report


@app.route(app.config["context_path"] + "/risk-report")
def risk_report():
    data = get_data()

    if data:
        return str(get_risk_report("interactive", data))
    else:
        return "<h1>Error</h1>"


@app.route(app.config["context_path"] + "/hazard-report")
def hazard_report():
    data = get_data()

    if data:
        return str(get_hazard_report("interactive", data))
    else:
        return "<h1>Error</h1>"


@app.route(app.config["context_path"] + "/risk-pdf")
def risk_pdf():
    data = get_data()

    if data:
        return send_file(
            io.BytesIO(get_risk_report("static", data)),  # type: ignore
            mimetype="application/pdf",
            as_attachment=True,
            download_name="risk-report.pdf",
        )
    else:
        return "<h1>Error</h1>"


@app.route(app.config["context_path"] + "/hazard-pdf")
def hazard_pdf():
    data = get_data()

    if data:
        return send_file(
            io.BytesIO(get_hazard_report("static", data)),  # type: ignore
            mimetype="application/pdf",
            as_attachment=True,
            download_name="hazard-report.pdf",
        )
    else:
        return "<h1>Error</h1>"


@app.route(app.config["context_path"] + "/beaches-graph")
def beaches_graph():
    data = get_data()

    if data:
        return get_beaches_graph(data)
    else:
        return "<h1>Error</h1>"


def get_data():
    session_data = session.get("data", {})

    data = {
        key: pd.read_json(
            io.StringIO(df_json), orient="split", typ="series", convert_dates=False
        )
        for key, df_json in session_data.items()
    }

    return data
