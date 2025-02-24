// Inizializzazione mappa
const mapboxToken = document.getElementById('map').dataset.token;
mapboxgl.accessToken = mapboxToken;

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/satellite-v9',
    center: [-3.0878, 36.7477],
    zoom: 12,
    preserveDrawingBuffer: true
});

map.on('load', () => {
    // Aggiungi controlli base
    map.addControl(new mapboxgl.NavigationControl());
    map.addControl(new mapboxgl.FullscreenControl());
    
    // Aggiungi sorgenti dati
    map.addSource('coastlines', {
        type: 'geojson',
        data: {
            type: 'FeatureCollection',
            features: []
        }
    });
    
    map.addSource('risk-areas', {
        type: 'geojson',
        data: {
            type: 'FeatureCollection',
            features: []
        }
    });

    // Aggiungi layer linea costiera
    map.addLayer({
        'id': 'coastline-layer',
        'type': 'line',
        'source': 'coastlines',
        'layout': {
            'line-join': 'round',
            'line-cap': 'round',
            'visibility': 'visible'
        },
        'paint': {
            'line-color': '#00ff00',
            'line-width': 3,
            'line-opacity': 0.8
        }
    });

    // Aggiungi layer rischio
    map.addLayer({
        'id': 'risk-layer',
        'type': 'fill',
        'source': 'risk-areas',
        'layout': {
            'visibility': 'visible'
        },
        'paint': {
            'fill-color': [
                'interpolate',
                ['linear'],
                ['get', 'risk_value'],
                0, '#096',
                50, '#ffff00',
                100, '#ff0000'
            ],
            'fill-opacity': 0.6,
            'fill-outline-color': '#000'
        }
    });

    // Aggiungi controlli personalizzati
    map.addControl(new TimeControl(), 'bottom-left');
    map.addControl(new LegendControl(), 'top-right');

    // Carica dati iniziali
    updatePredictedData(2023);
});

function updatePredictedData(year) {
    fetch(`/api/prediction/${year}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            
            // Aggiorna layer costiera
            if (map.getSource('coastlines')) {
                map.getSource('coastlines').setData({
                    type: 'FeatureCollection',
                    features: data.coastline_features || []
                });
            }
            
            // Aggiorna layer rischio
            if (map.getSource('risk-areas')) {
                map.getSource('risk-areas').setData({
                    type: 'FeatureCollection',
                    features: data.risk_features || []
                });
            }

            // Aggiorna legenda con fattore di predizione
            updatePredictionFactor(data.prediction_factor);
        })
        .catch(error => {
            console.error('Error loading data:', error);
        });
}