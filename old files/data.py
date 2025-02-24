import pandas as pd
from flask.helpers import get_root_path

root_path = get_root_path(__name__)

beaches_data = pd.read_csv(
    root_path + "/data/beaches.csv",
    index_col=0,
    dtype={"Tramo": str, "ID_Municipio": str},
    comment="#",
)
beaches_data[["ph_unit", "stretch"]] = beaches_data.Tramo.str.split("-", expand=True)


def get_ph_units():
    """
    Retrieves the unique physiographic units from the beaches data.

    Returns:
        list: A list of unique physiographic units.
    """
    ph_units = beaches_data["ph_unit"].unique().tolist()

    return ph_units


def get_stretches(ph_unit):
    """
    Retrieves the unique stretches for a given physiographic unit.

    Args:
        ph_unit (str): The physiographic unit identifier.

    Returns:
        list: A list of unique stretches for the given physiographic unit.
    """
    stretches = beaches_data.query("ph_unit == @ph_unit")["stretch"].unique().tolist()

    return stretches


def get_beaches(ph_unit, stretch):
    """
    Retrieves the beaches for a given physiographic unit and stretch.

    Args:
        ph_unit (str): The physiographic unit identifier.
        stretch (str): The stretch identifier.

    Returns:
        dict: A dictionary mapping beach identifiers to beach names.
    """
    beaches = (
        beaches_data.query("ph_unit == @ph_unit and stretch == @stretch")
        .set_index("Identificador")
        .to_dict()["Nombre"]
    )

    return beaches


def get_beach_name(beach):
    """
    Retrieves the name of a beach given its identifier.

    Args:
        beach (str): The beach identifier.

    Returns:
        str: The name of the beach.
    """
    beach_name = beaches_data.query("Identificador == @beach")["Nombre"].item()

    return beach_name


def get_region_name(beach):
    """
    Retrieves the name of the region for a given beach identifier.

    Args:
        beach (str): The beach identifier.

    Returns:
        str: The name of the region.
    """
    ph_unit = get_ph_unit(beach)

    region_name = ""

    match ph_unit[0]:
        case "A":
            region_name = "Almería"
        case "C":
            region_name = "Cádiz"
        case "G":
            region_name = "Granada"
        case "H":
            region_name = "Huelva"
        case "M":
            region_name = "Málaga"
    return region_name


def get_region(ph_unit):
    """
    Retrieves the name of the region for a given physiographic unit.

    Args:
        ph_unit (str): The physiographic unit identifier.

    Returns:
        str: The name of the region.
    """
    region = ""

    match ph_unit[0]:
        case "A":
            region = "Almeria"
        case "C":
            region = "Cadiz"
        case "G":
            region = "Granada"
        case "H":
            region = "Huelva"
        case "M":
            region = "Malaga"

    return region


def get_ph_unit(beach):
    """
    Retrieves the physiographic unit for a given beach identifier.

    Args:
        beach (str): The beach identifier.

    Returns:
        str: The physiographic unit identifier.
    """
    return beach.split("-")[0]


def get_strech(beach):
    """
    Retrieves the stretch for a given beach identifier.

    Args:
        beach (str): The beach identifier.

    Returns:
        str: The stretch identifier.
    """
    return beach.split("-")[1].split("_")[0]


def get_beach(beach):
    """
    Retrieves the beach identifier from a given beach string.

    Args:
        beach (str): The beach string.

    Returns:
        str: The beach identifier.
    """
    return beach.split("-")[1].split("_")[1]
