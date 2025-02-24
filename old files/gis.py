import uuid
import warnings
from pathlib import Path

import geopandas
import pandas as pd
from rasterstats import zonal_stats

polys = ["Polygon", "MultiPolygon"]
lines = ["LineString", "MultiLineString", "LinearRing"]
points = ["Point", "MultiPoint"]


def compute_intersection(gdf, roi):
    gdf["uuid"] = gdf.apply(lambda _: uuid.uuid4(), axis=1)
    gdf["uuid"] = gdf["uuid"].astype(str)

    gdf = gdf.reset_index()

    puntos = gdf["geometry"].apply(lambda geom: geom.geom_type in points)
    lineas = gdf["geometry"].apply(lambda geom: geom.geom_type in lines)
    poligonos = gdf["geometry"].apply(lambda geom: geom.geom_type in polys)

    points_check = gdf.geom_type.isin(points).any()
    lines_check = gdf.geom_type.isin(lines).any()
    polys_check = gdf.geom_type.isin(polys).any()

    if points_check:
        intersection = gdf.loc[puntos].overlay(roi, how="intersection")
        intersection_merged = pd.merge(
            gdf.loc[puntos], intersection, on="uuid", how="left"
        )

        gdf.loc[puntos, "percentage"] = 100

    if lines_check:
        intersection = gdf.loc[lineas].overlay(roi, how="intersection")
        intersection_merged = pd.merge(
            gdf.loc[lineas], intersection, on="uuid", how="left"
        )

        gdf.loc[lineas, "percentage"] = (
            intersection_merged["geometry_y"].length
            / intersection_merged["geometry_x"].length
        ) * 100

    if polys_check:
        intersection = gdf.loc[poligonos].overlay(roi, how="intersection")
        intersection_merged = pd.merge(
            gdf.loc[poligonos], intersection, on="uuid", how="left"
        )

        gdf.loc[poligonos, "percentage"] = (
            intersection_merged["geometry_y"].area
            / intersection_merged["geometry_x"].area
        ) * 100

    if not gdf.empty:
        gdf = gdf.query("percentage > 0")

    return gdf


def compute_stats(gdf, layer):
    # https://pythonhosted.org/rasterstats/manual.html#zonal-statistics
    gdf = gdf[~(gdf["geometry"].is_empty | gdf["geometry"].isna())]

    if not gdf.empty:
        stats = pd.DataFrame(
            zonal_stats(
                gdf,
                layer,
                stats=["min", "max", "mean", "count", "sum"],
                prefix="stats_",
                all_touched=True,
            )
        )
    else:
        stats = pd.DataFrame()

    return stats


def clip_roi(layer_path, roi, relative_path, rp, beach):
    return_code = 0

    try:
        gdf = geopandas.read_file(layer_path)
        gdf = fix_crs(gdf, relative_path.parts[-1])

        gdfs = split_geometries(gdf)
        mixed_geometries = True if len(gdfs) > 1 else False

        empty_intersections = []
        for geometry, gdf in gdfs.items():
            if mixed_geometries:
                suffix = f"_{geometry}"
            else:
                suffix = ""

            intersection = gdf.overlay(roi, how="intersection")

            if intersection.empty:
                empty_intersections.append(True)
            else:
                empty_intersections.append(False)

            output_path = Path(f"{relative_path}/{beach}/{rp}")
            output_path.mkdir(exist_ok=True, parents=True)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                intersection.to_file(
                    output_path / (layer_path.stem + suffix + ".geojson"),
                    driver="GeoJSON",
                )

        if all(empty_intersections):
            return_code = 1

    except Exception:
        return_code = -1

    return return_code


def split_geometries(gdf):
    polys_check = gdf.geom_type.isin(polys).any()
    lines_check = gdf.geom_type.isin(lines).any()
    points_check = gdf.geom_type.isin(points).any()

    gdfs = {}
    if polys_check:
        gdfs["polys"] = gdf[gdf["geometry"].apply(lambda geom: geom.geom_type in polys)]

    if lines_check:
        gdfs["lines"] = gdf[gdf["geometry"].apply(lambda geom: geom.geom_type in lines)]

    if points_check:
        gdfs["points"] = gdf[
            gdf["geometry"].apply(lambda geom: geom.geom_type in points)
        ]

    return gdfs


def fix_crs(gdf, data_source, filename=""):
    match data_source:
        case "btn25" | "catastro" | "edar" | "ei" | "malla_estadistica" | "usos_jda":
            crs = "25830"
        case "depuradoras":
            crs = "4258"
        case "pol_costa" | "results_iccoast":
            crs = "4326"
        case "rt":
            crs = "4258"
        case "zp":
            if "censoaguas" in filename.lower():
                crs = "4326"
            else:
                crs = "4258"

    gdf = gdf.set_crs(crs, allow_override=True)

    gdf = gdf.to_crs("25830")

    return gdf
