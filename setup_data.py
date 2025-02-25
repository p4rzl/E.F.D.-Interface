import os
import json
import pandas as pd
import numpy as np

def ensure_directory(path):
    """Assicura che una directory esista, creandola se necessario."""
    os.makedirs(path, exist_ok=True)
    return path

def create_sample_data():
    """Crea la struttura delle directory e dei file di esempio per l'applicazione."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Crea le directory necessarie
    data_dir = ensure_directory(os.path.join(base_dir, 'data'))
    risk_dir = ensure_directory(os.path.join(data_dir, 'risk'))
    hazard_dir = ensure_directory(os.path.join(data_dir, 'hazard'))
    curves_dir = ensure_directory(os.path.join(data_dir, 'curves'))
    reports_dir = ensure_directory(os.path.join(base_dir, 'static', 'reports'))
    
    # Crea un file CSV di esempio per le spiagge
    beaches_data = pd.DataFrame({
        'id': range(1, 6),
        'name': ['Spiaggia Dorada', 'Spiaggia San Sebastian', 'Spiaggia Barceloneta', 'Spiaggia Sitges', 'Spiaggia Tarragona'],
        'length': [1200, 850, 1100, 950, 1500],
        'width': [45, 30, 35, 40, 50],
        'risk_index': [0.65, 0.45, 0.75, 0.55, 0.35],
        'erosion_rate': [0.8, 0.5, 1.2, 0.7, 0.4]
    })
    
    beaches_data.to_csv(os.path.join(data_dir, 'beaches.csv'), index=False)
    
    # Crea file CSV di esempio per pesi rischio
    risk_weights = pd.DataFrame({
        'weight': [0.3, 0.4, 0.3],
        'value': [0.65, 0.75, 0.45]
    }, index=['Economico', 'Sociale', 'Ambientale'])
    
    # Assicura la directory risk esista
    ensure_directory(os.path.join(data_dir, 'risk'))
    risk_weights.to_csv(os.path.join(data_dir, 'risk', 'risk_weights.csv'))
    
    # Crea file CSV di esempio per pesi hazard
    hazard_weights = pd.DataFrame({
        'weight': [0.4, 0.3, 0.3],
        'value': [0.8, 0.6, 0.5]
    }, index=['Erosione', 'Inondazione', 'Tempeste'])
    
    # Assicura la directory hazard esista
    ensure_directory(os.path.join(data_dir, 'hazard'))
    hazard_weights.to_csv(os.path.join(data_dir, 'hazard', 'hazard_weights.csv'))
    
    # Crea un file GeoJSON di esempio per le spiagge
    beaches_geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Aggiungi feature per ogni spiaggia
    for i, beach in beaches_data.iterrows():
        # Crea un poligono semplice con coordinate vicine ma leggermente diverse
        base_lon = 1.29 + (i * 0.02)
        base_lat = 41.11 + (i * 0.01)
        
        feature = {
            "type": "Feature",
            "properties": {
                "id": int(beach['id']),
                "name": beach['name'],
                "length": float(beach['length']),
                "width": float(beach['width']),
                "risk_index": float(beach['risk_index']),
                "erosion_rate": float(beach['erosion_rate'])
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [base_lon, base_lat],
                    [base_lon + 0.01, base_lat],
                    [base_lon + 0.01, base_lat + 0.01],
                    [base_lon, base_lat + 0.01],
                    [base_lon, base_lat]
                ]]
            }
        }
        
        beaches_geojson["features"].append(feature)
    
    # Salva il GeoJSON delle spiagge
    with open(os.path.join(data_dir, 'beaches.geojson'), 'w') as f:
        json.dump(beaches_geojson, f)
    
    # Crea un GeoJSON di esempio per economia e rischio
    economy_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Zona Economica 1",
                    "value": 0.75
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [1.28, 41.10],
                        [1.32, 41.10],
                        [1.32, 41.13],
                        [1.28, 41.13],
                        [1.28, 41.10]
                    ]]
                }
            }
        ]
    }
    
    hazards_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Zona Pericolo 1",
                    "value": 0.85
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [1.29, 41.11],
                        [1.33, 41.11],
                        [1.33, 41.14],
                        [1.29, 41.14],
                        [1.29, 41.11]
                    ]]
                }
            }
        ]
    }
    
    # Salva i GeoJSON di economia e rischio
    with open(os.path.join(risk_dir, 'economia.geojson'), 'w') as f:
        json.dump(economy_geojson, f)
    
    with open(os.path.join(risk_dir, 'peligrosidad.geojson'), 'w') as f:
        json.dump(hazards_geojson, f)
    
    # Crea un file CSV di esempio per curve di erosione
    for i in range(1, 6):
        years = range(2023, 2101)
        erosion_rate = beaches_data.iloc[i-1]['erosion_rate']
        initial_width = beaches_data.iloc[i-1]['width']
        
        widths = [max(0, initial_width - erosion_rate * (year - 2023)) for year in years]
        
        curve_data = pd.DataFrame({
            'year': years,
            'width': widths
        })
        
        curve_data.to_csv(os.path.join(curves_dir, f'beach_{i}_erosion.csv'), index=False)
    
    print("Struttura di directory e dati di esempio creati con successo!")

if __name__ == "__main__":
    create_sample_data()
