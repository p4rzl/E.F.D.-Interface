let map;
let currentLayers = new Set();

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    setupControls();
    loadInitialData();
});

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
    });
}

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