<<<<<<< HEAD
let map;
let currentLayers = new Set();
=======
const mapboxToken = document.getElementById('map').dataset.token;
mapboxgl.accessToken = mapboxToken;
>>>>>>> b6266728e6482190fbe7ceb37343527cae9bd1e2

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    setupControls();
    loadInitialData();
});

<<<<<<< HEAD
function initMap() {
    mapboxgl.accessToken = document.getElementById('map').dataset.token;
    
    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/light-v10',
        center: [-3.0878, 36.7477],
        zoom: 12
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-left');
    map.addControl(new mapboxgl.FullscreenControl(), 'top-left');
}

function setupControls() {
    const yearSlider = document.getElementById('yearSlider');
    const yearValue = document.getElementById('yearValue');
    const layerSelect = document.getElementById('layerSelect');

    yearSlider.addEventListener('input', (e) => {
        yearValue.textContent = e.target.value;
        updateMapData(e.target.value);
    });

    layerSelect.addEventListener('change', (e) => {
        updateVisibleLayers(e.target.value);
=======
map.on('load', () => {
    map.addControl(new mapboxgl.NavigationControl());
    map.addControl(new mapboxgl.FullscreenControl());
    
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
>>>>>>> b6266728e6482190fbe7ceb37343527cae9bd1e2
    });
}

<<<<<<< HEAD
function updateMapData(year) {
    fetch(`/api/prediction/${year}`)
        .then(response => response.json())
        .then(data => {
            updateLayers(data);
            updateTable(data);
        })
        .catch(error => console.error('Errore nel caricamento dei dati:', error));
}

function updateTable(data) {
    const table = document.getElementById('beachesTable');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    data.beaches.forEach(beach => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${beach.name}</td>
            <td>${beach.length.toFixed(1)}</td>
            <td>${beach.width.toFixed(1)}</td>
            <td>${beach.risk_index.toFixed(2)}</td>
            <td>${beach.erosion_rate.toFixed(2)}</td>
            <td>
                <button class="action-button" 
                        onclick="showBeachDetails('${beach.id}')">
                    Dettagli
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}
=======
    map.addControl(new TimeControl(), 'bottom-left');
    map.addControl(new LegendControl(), 'top-right');

    loadGeoJSONFiles();
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

function loadGeoJSONFiles() {
    fetch('/api/geojson_files')
        .then(response => response.json())
        .then(files => {
            files.forEach(file => {
                fetch(file)
                    .then(response => response.json())
                    .then(data => {
                        const sourceId = `geojson-${file}`;
                        map.addSource(sourceId, {
                            type: 'geojson',
                            data: data
                        });
                        map.addLayer({
                            id: `layer-${file}`,
                            type: 'line',
                            source: sourceId,
                            paint: {
                                'line-color': '#ff0000',
                                'line-width': 2
                            }
                        });
                    });
            });
        });
}

class LegendControl {
    onAdd(map) {
        this._map = map;
        this._container = document.createElement('div');
        this._container.className = 'mapboxgl-ctrl legend';
        this._container.innerHTML = `
            <h4>Legend</h4>
            <div><span class="legend-color" style="background-color: #00ff00;"></span> Coastlines</div>
            <div><span class="legend-color" style="background-color: #ff0000;"></span> Risk Areas</div>
        `;
        return this._container;
    }

    onRemove() {
        this._container.parentNode.removeChild(this._container);
        this._map = undefined;
    }
}

class TimeControl {
    onAdd(map) {
        this._map = map;
        this._container = document.createElement('div');
        this._container.className = 'mapboxgl-ctrl time-control';
        this._container.innerHTML = `
            <div class="time-label">Year: <span id="year-label">2023</span></div>
            <input id="year-slider" class="time-slider" type="range" min="2023" max="2100" step="1" value="2023">
        `;

        this._container.querySelector('#year-slider').addEventListener('input', (e) => {
            const year = e.target.value;
            document.getElementById('year-label').textContent = year;
            updatePredictedData(year);
        });

        return this._container;
    }

    onRemove() {
        this._container.parentNode.removeChild(this._container);
        this._map = undefined;
    }
}
>>>>>>> b6266728e6482190fbe7ceb37343527cae9bd1e2
