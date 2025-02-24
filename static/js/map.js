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
    map.addControl(new mapboxgl.NavigationControl());
    map.addControl(new mapboxgl.FullscreenControl());

    loadAllGeoJSONFiles().then(geojsonData => {
        geojsonData.forEach((data, index) => {
            const sourceId = `geojson-source-${index}`;
            const layerId = `geojson-layer-${index}`;

            map.addSource(sourceId, {
                type: 'geojson',
                data: data
            });

            map.addLayer({
                id: layerId,
                type: 'line',
                source: sourceId,
                layout: {
                    'line-join': 'round',
                    'line-cap': 'round',
                    'visibility': 'visible'
                },
                paint: {
                    'line-color': '#00ff00',
                    'line-width': 3,
                    'line-opacity': 0.8
                }
            });
        });
    });

    map.addControl(new TimeControl(), 'bottom-left');
    map.addControl(new LegendControl(), 'top-right');

    updatePredictedData(2023);
});

function loadAllGeoJSONFiles() {
    return fetch('/api/load_geojson_files')
        .then(response => response.json())
        .then(data => data.geojson_files)
        .catch(error => {
            console.error('Error loading GeoJSON files:', error);
            return [];
        });
}

function updatePredictedData(year) {
    fetch(`/api/prediction/${year}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }

            if (map.getSource('coastlines')) {
                map.getSource('coastlines').setData({
                    type: 'FeatureCollection',
                    features: data.coastline_features || []
                });
            }

            if (map.getSource('risk-areas')) {
                map.getSource('risk-areas').setData({
                    type: 'FeatureCollection',
                    features: data.risk_features || []
                });
            }

            updatePredictionFactor(data.prediction_factor);
        })
        .catch(error => {
            console.error('Error loading data:', error);
        });
}

class TimeControl {
    onAdd(map) {
        this.map = map;
        this.container = document.createElement('div');
        this.container.className = 'time-control-container';

        this.label = document.createElement('div');
        this.label.className = 'time-label';
        this.label.textContent = 'Anno: 2023';
        this.container.appendChild(this.label);

        this.slider = document.createElement('input');
        this.slider.type = 'range';
        this.slider.min = 2023;
        this.slider.max = 2100;
        this.slider.value = 2023;
        this.slider.className = 'time-slider';
        this.slider.addEventListener('input', (e) => {
            const year = e.target.value;
            this.label.textContent = `Anno: ${year}`;
            updatePredictedData(year);
        });
        this.container.appendChild(this.slider);

        return this.container;
    }

    onRemove() {
        this.container.parentNode.removeChild(this.container);
        this.map = undefined;
    }
}

class LegendControl {
    onAdd(map) {
        this.map = map;
        this.container = document.createElement('div');
        this.container.className = 'map-legend';

        const legendTitle = document.createElement('h4');
        legendTitle.textContent = 'Legenda';
        this.container.appendChild(legendTitle);

        const legendItems = [
            { color: '#00ff00', label: 'Linea costiera' },
            { color: '#ff0000', label: 'Aree di rischio' }
        ];

        legendItems.forEach(item => {
            const legendItem = document.createElement('div');
            legendItem.className = 'legend-item';

            const colorBox = document.createElement('div');
            colorBox.className = 'color-box';
            colorBox.style.backgroundColor = item.color;
            legendItem.appendChild(colorBox);

            const label = document.createElement('span');
            label.textContent = item.label;
            legendItem.appendChild(label);

            this.container.appendChild(legendItem);
        });

        return this.container;
    }

    onRemove() {
        this.container.parentNode.removeChild(this.container);
        this.map = undefined;
    }
}

function updatePredictionFactor(factor) {
    const predictionElement = document.createElement('div');
    predictionElement.className = 'prediction';
    predictionElement.textContent = `Fattore di predizione: ${factor}`;
    document.querySelector('.map-legend').appendChild(predictionElement);
}
