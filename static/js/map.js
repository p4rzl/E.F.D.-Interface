mapboxgl.accessToken = '{{ mapbox_token }}';
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/navigation-night-v1',
    center: [-3.073377, 36.746367], // Coordinate iniziali basate sui tuoi dati
    zoom: 12
});

// Aggiungi controlli
map.addControl(new mapboxgl.NavigationControl());
map.addControl(new mapboxgl.FullscreenControl());

// Carica i dati quando la mappa è pronta
map.on('load', () => {
    // Aggiungi linee della costa
    map.addSource('coastlines', {
        type: 'geojson',
        data: '/data/results_analysis/01_Linea_orilla_2100/A01/A01-001/l_orilla_ini_A01-001_01.geojson'
    });
    
    map.addLayer({
        'id': 'coastline-layer',
        'type': 'line',
        'source': 'coastlines',
        'layout': {},
        'paint': {
            'line-color': '#00ff00',
            'line-width': 2
        }
    });

    // Aggiungi aree ROI
    map.addSource('roi', {
        type: 'geojson',
        data: '/data/roi/A01-001_01/50/roi.geojson'
    });

    map.addLayer({
        'id': 'roi-layer',
        'type': 'fill',
        'source': 'roi',
        'layout': {},
        'paint': {
            'fill-color': '#ff0000',
            'fill-opacity': 0.3
        }
    });

    // Aggiungi livelli di rischio
    map.addSource('risk', {
        type: 'geojson',
        data: '/data/risk/A01-001_01/50/economia.geojson'
    });

    map.addLayer({
        'id': 'risk-layer',
        'type': 'fill',
        'source': 'risk',
        'layout': {},
        'paint': {
            'fill-color': '#0000ff',
            'fill-opacity': 0.3
        }
    });
});