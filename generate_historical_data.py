import pandas as pd
import numpy as np

def generate_historical_data():
    years = range(2000, 2024)
    coastal_index = [
        100 + np.random.normal(0, 2) + (year - 2000) * 0.5 
        for year in years
    ]
    
    df = pd.DataFrame({
        'year': years,
        'coastal_index': coastal_index
    })
    
    df.to_csv('data/historical_coastal_data.csv', index=False)

if __name__ == "__main__":
    generate_historical_data()