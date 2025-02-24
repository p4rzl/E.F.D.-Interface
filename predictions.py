from sklearn.linear_model import LinearRegression
import pandas as pd
import numpy as np
import os
import json

class CoastalPredictor:
    def __init__(self):
        self.base_path = 'data/results_analysis'
        self.risk_path = 'data/risk'
    
    def get_data_for_year(self, year):
        period = self._get_period(year)
        return {
            'coastline': self._get_coastline_data(period),
            'risk': self._get_risk_data(year),
            'prediction_factor': self._calculate_prediction(year)
        }
    
    def _get_period(self, year):
        # Converte l'anno in periodo (01-12)
        return str(min(int((year - 2023) / 10) + 1, 12)).zfill(2)
        
    def _get_coastline_data(self, period):
        coastline_path = f'{self.base_path}/01_Linea_orilla_2100/A01/A01-001/l_orilla_ini_A01-001_{period}.geojson'
        return self._load_geojson(coastline_path)
    
    def _get_risk_data(self, year):
        risk_files = [
            f'{self.risk_path}/A01-001_01/{year}/economia.geojson',
            f'{self.risk_path}/A01-001_01/{year}/poblacion.geojson'
        ]
        return self._merge_risk_data(risk_files)
    
    def _merge_risk_data(self, files):
        merged_features = []
        for file in files:
            data = self._load_geojson(file)
            if data and 'features' in data:
                merged_features.extend(data['features'])
        return {'type': 'FeatureCollection', 'features': merged_features}
    
    def _load_geojson(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {'type': 'FeatureCollection', 'features': []}
    
    def _calculate_prediction(self, year):
        historical_data = self._load_historical_data()
        X = historical_data['year'].values.reshape(-1, 1)
        y = historical_data['value'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        prediction = model.predict(np.array([[year]]))
        return prediction[0]
    
    def _load_historical_data(self):
        historical_data_path = 'data/historical_coastal_data.csv'
        if os.path.exists(historical_data_path):
            return pd.read_csv(historical_data_path)
        return pd.DataFrame({'year': [], 'value': []})
