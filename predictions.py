from sklearn.linear_model import LinearRegression
import pandas as pd
import numpy as np
import os
import json

class CoastalPredictor:
    def __init__(self):
        self.base_path = 'data/results_analysis'
        self.risk_path = 'data/risk'
        self.historical_data_path = 'data/historical_coastal_data.csv'
        self.model = self._train_model()
    
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
        if year <= 2023:
            return 0  # Nessuna predizione per gli anni passati
        future_years = np.array([[year]])
        predicted_index = self.model.predict(future_years)
        return predicted_index[0]

    def _train_model(self):
        df = pd.read_csv(self.historical_data_path)
        X = df[['year']]
        y = df['coastal_index']
        model = LinearRegression()
        model.fit(X, y)
        return model

    def predict_future_data(self, year):
        return self._calculate_prediction(year)
