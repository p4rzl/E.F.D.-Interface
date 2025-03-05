// static/js/map.js

// Funzioni per la mappa

document.addEventListener('DOMContentLoaded', function() {
    // Verifica che l'elemento mappa esista prima di inizializzare
    const mapElement = document.getElementById('map');
    if (!mapElement) {
        console.error("Elemento mappa non trovato nel DOM");
        return;
    }

    // Verifica che mapboxToken sia definito
    if (typeof mapboxToken === 'undefined') {
        console.error("Token di Mapbox non definito");
        return;
    }

    try {
        // Inizializza la mappa Mapbox
        mapboxgl.accessToken = mapboxToken;
        
        const map = new mapboxgl.Map({
            container: 'map',
            style: 'mapbox://styles/mapbox/light-v11',
            center: [1.391, 41.07], // Centro approssimativo area Tarragona
            zoom: 10
        });

        // Salva lo stato attuale dei layer e l'ultimo layer selezionato
        let currentLayerVisibility = {
            'beaches-fill': true,
            'beaches-outline': true,
            'economy-layer': false,
            'hazards-layer': false
        };
        
        // Salva il layer selezionato a livello globale
        let selectedLayer = 'beaches';
        
        // Gestione errori di caricamento mappa
        map.on('error', function(e) {
            console.error('Errore di Mapbox:', e);
        });
        
        // Calcola e aggiorna le statistiche iniziali
        calculateAndSetInitialStatistics();
        
        // Verifica lo stato di caricamento della mappa
        map.on('load', function() {
            console.log('Mappa caricata con successo');
            
            // Variabile per tracciare se è necessario fare zoom sui dati
            let needsFitBounds = true;
            
            // Carica i dati GeoJSON se disponibili
            if (typeof beachesGeoJSON !== 'undefined' && beachesGeoJSON) {
                loadBeachesLayer(map, beachesGeoJSON);
                // Zoom automatico sui dati delle spiagge dopo il caricamento
                if (needsFitBounds && beachesGeoJSON.features && beachesGeoJSON.features.length > 0) {
                    fitMapToBounds(map, beachesGeoJSON);
                    needsFitBounds = false; // Lo facciamo solo una volta
                }
            } else {
                console.warn('Dati GeoJSON delle spiagge non disponibili');
            }
            
            if (typeof economyGeoJSON !== 'undefined' && economyGeoJSON) {
                loadEconomyLayer(map, economyGeoJSON);
                // Se non abbiamo già fatto lo zoom, proviamo con questi dati
                if (needsFitBounds && economyGeoJSON.features && economyGeoJSON.features.length > 0) {
                    fitMapToBounds(map, economyGeoJSON);
                    needsFitBounds = false;
                }
            }
            
            if (typeof hazardsGeoJSON !== 'undefined' && hazardsGeoJSON) {
                loadHazardsLayer(map, hazardsGeoJSON);
                // Se non abbiamo ancora fatto lo zoom, proviamo con questi dati
                if (needsFitBounds && hazardsGeoJSON.features && hazardsGeoJSON.features.length > 0) {
                    fitMapToBounds(map, hazardsGeoJSON);
                    needsFitBounds = false;
                }
            }
            
            // Imposta il valore iniziale per il layer
            const layerSelect = document.getElementById('layerSelect');
            if (layerSelect) {
                selectedLayer = layerSelect.value; // Imposta il layer iniziale
                toggleLayerVisibility(map, layerSelect.value);
                
                // Gestione cambio layer
                layerSelect.addEventListener('change', function() {
                    selectedLayer = this.value; // Aggiorna il layer selezionato
                    toggleLayerVisibility(map, this.value);
                });
            }
            
            // Gestione slider anni
            const yearSlider = document.getElementById('yearSlider');
            const yearValue = document.getElementById('yearValue');
            const yearDisplay = document.getElementById('year-display');
            
            if (yearSlider && yearValue) {
                yearSlider.addEventListener('input', function() {
                    const year = parseInt(this.value);
                    yearValue.textContent = year;
                    if (yearDisplay) yearDisplay.textContent = year;
                    updateMapData(map, year);
                });
            }
        });
        
        // Ascoltatore per cambio tema
        document.addEventListener('themeChanged', function(e) {
            const isDark = e.detail.theme === 'dark';
            
            // Salva lo stato attuale dei layer prima del cambio stile
            if (map.getLayer('beaches-fill')) {
                currentLayerVisibility['beaches-fill'] = map.getLayoutProperty('beaches-fill', 'visibility') === 'visible';
            }
            if (map.getLayer('beaches-outline')) {
                currentLayerVisibility['beaches-outline'] = map.getLayoutProperty('beaches-outline', 'visibility') === 'visible';
            }
            if (map.getLayer('economy-layer')) {
                currentLayerVisibility['economy-layer'] = map.getLayoutProperty('economy-layer', 'visibility') === 'visible';
            }
            if (map.getLayer('hazards-layer')) {
                currentLayerVisibility['hazards-layer'] = map.getLayoutProperty('hazards-layer', 'visibility') === 'visible';
            }
            
            // Cambia lo stile della mappa
            map.setStyle(isDark ? 'mapbox://styles/mapbox/dark-v11' : 'mapbox://styles/mapbox/light-v11');
            
            // Dopo il cambio stile, ripristina i layer
            map.once('style.load', function() {
                // Ricarica tutti i layer
                if (typeof beachesGeoJSON !== 'undefined' && beachesGeoJSON) {
                    loadBeachesLayer(map, beachesGeoJSON);
                }
                
                if (typeof economyGeoJSON !== 'undefined' && economyGeoJSON) {
                    loadEconomyLayer(map, economyGeoJSON);
                }
                
                if (typeof hazardsGeoJSON !== 'undefined' && hazardsGeoJSON) {
                    loadHazardsLayer(map, hazardsGeoJSON);
                }
                
                // Aggiungi un ritardo per assicurarsi che i layer siano caricati
                setTimeout(() => {
                    // Ripristina la visibilità dei layer corretta
                    toggleLayerVisibility(map, selectedLayer);
                    
                    // Riassocia gli eventi di click
                    addBeachClickHandlers(map);
                }, 100);
            });
        });
        
        // Verifica il tema attuale e imposta lo stile della mappa
        const isDarkTheme = document.body.classList.contains('dark-theme');
        if (isDarkTheme) {
            map.setStyle('mapbox://styles/mapbox/dark-v11');
        }
    } catch (error) {
        console.error('Errore nell\'inizializzazione della mappa:', error);
        
        // Aggiungi un messaggio di errore visibile all'utente
        const mapContainer = document.querySelector('.map-container');
        if (mapContainer) {
            const errorMessage = document.createElement('div');
            errorMessage.className = 'map-error-message';
            errorMessage.innerHTML = `
                <div class="error-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Impossibile caricare la mappa. Ricarica la pagina o contatta l'amministratore.</p>
                </div>
            `;
            mapContainer.appendChild(errorMessage);
        }
    }
    
    // Ascoltatore per cambio tema
    document.addEventListener('themeChanged', function(e) {
        // Controlla se la mappa è stata inizializzata
        if (typeof map === 'undefined' || !map) return;
        
        const isDark = e.detail.theme === 'dark';
        
        try {
            // Salva lo stato attuale della mappa
            const currentState = {
                center: map.getCenter(),
                zoom: map.getZoom(),
                pitch: map.getPitch(),
                bearing: map.getBearing(),
                // Salva la visibilità di tutti i layer
                layers: []
            };
            
            // Salva la visibilità dei layer
            if (map.getLayer('beaches-fill')) {
                currentState.layers.push({
                    id: 'beaches-fill',
                    visibility: map.getLayoutProperty('beaches-fill', 'visibility') === 'visible'
                });
            }
            if (map.getLayer('beaches-outline')) {
                currentState.layers.push({
                    id: 'beaches-outline',
                    visibility: map.getLayoutProperty('beaches-outline', 'visibility') === 'visible'
                });
            }
            if (map.getLayer('economy-layer')) {
                currentState.layers.push({
                    id: 'economy-layer',
                    visibility: map.getLayoutProperty('economy-layer', 'visibility') === 'visible'
                });
            }
            if (map.getLayer('hazards-layer')) {
                currentState.layers.push({
                    id: 'hazards-layer',
                    visibility: map.getLayoutProperty('hazards-layer', 'visibility') === 'visible'
                });
            }
            
            // Aggiungiamo anche un log per debug
            console.log("Cambio tema mappa:", isDark ? 'dark' : 'light', "Layer salvati:", currentState.layers);
            
            // Cambia lo stile della mappa
            map.setStyle(isDark ? 'mapbox://styles/mapbox/dark-v11' : 'mapbox://styles/mapbox/light-v11');
            
            // Dopo il cambio stile, ripristina lo stato della mappa
            map.once('style.load', function() {
                console.log("Nuovo stile mappa caricato, ripristino dati...");
                
                // Ripristina view
                map.setCenter(currentState.center);
                map.setZoom(currentState.zoom);
                map.setPitch(currentState.pitch);
                map.setBearing(currentState.bearing);
                
                // Ricarica tutti i layer
                if (typeof beachesGeoJSON !== 'undefined' && beachesGeoJSON) {
                    loadBeachesLayer(map, beachesGeoJSON);
                }
                
                if (typeof economyGeoJSON !== 'undefined' && economyGeoJSON) {
                    loadEconomyLayer(map, economyGeoJSON);
                }
                
                if (typeof hazardsGeoJSON !== 'undefined' && hazardsGeoJSON) {
                    loadHazardsLayer(map, hazardsGeoJSON);
                }
                
                // Ripristina la visibilità dei layer
                setTimeout(() => {
                    currentState.layers.forEach(layer => {
                        if (map.getLayer(layer.id)) {
                            map.setLayoutProperty(
                                layer.id, 
                                'visibility', 
                                layer.visibility ? 'visible' : 'none'
                            );
                        }
                    });
                    
                    // Ripristina i gestori di eventi
                    if (map.getLayer('beaches-fill')) {
                        addBeachClickHandlers(map);
                    }
                    
                    console.log("Ripristino dati mappa completato");
                }, 100);
            });
        } catch (error) {
            console.error("Errore durante l'aggiornamento del tema della mappa:", error);
        }
    });
});

// Calcola e imposta le statistiche iniziali
function calculateAndSetInitialStatistics() {
    if (!beachesData || !Array.isArray(beachesData)) return;
    
    // Calcola la larghezza media
    let totalWidth = 0;
    let countWidth = 0;
    let totalRisk = 0;
    let countRisk = 0;
    let criticalBeaches = 0;
    
    beachesData.forEach(beach => {
        if (beach.width != null && !isNaN(beach.width)) {
            totalWidth += parseFloat(beach.width);
            countWidth++;
            
            if (beach.width < 5) {
                criticalBeaches++;
            }
        }
        
        if (beach.risk_index != null && !isNaN(beach.risk_index)) {
            totalRisk += parseFloat(beach.risk_index);
            countRisk++;
        }
    });
    
    const avgWidth = countWidth > 0 ? totalWidth / countWidth : 0;
    const avgRisk = countRisk > 0 ? totalRisk / countRisk : 0;
    
    // Aggiorna i valori nel pannello informativo
    const avgWidthEl = document.getElementById('avg-width');
    const avgRiskEl = document.getElementById('avg-risk');
    const criticalBeachesEl = document.getElementById('critical-beaches');
    
    if (avgWidthEl) avgWidthEl.textContent = avgWidth.toFixed(1) + ' m';
    if (avgRiskEl) avgRiskEl.textContent = avgRisk.toFixed(2);
    if (criticalBeachesEl) criticalBeachesEl.textContent = criticalBeaches;
}

// Funzione per caricare il layer delle spiagge
function loadBeachesLayer(map, geojson) {
    console.log('Caricamento layer spiagge');
    
    // Rimuovi la fonte e i layer se già esistono
    if (map.getSource('beaches')) {
        if (map.getLayer('beaches-fill')) map.removeLayer('beaches-fill');
        if (map.getLayer('beaches-outline')) map.removeLayer('beaches-outline');
        map.removeSource('beaches');
    }

    // Aggiungi la fonte
    map.addSource('beaches', {
        type: 'geojson',
        data: geojson
    });
    
    // Aggiungi layer per il riempimento delle spiagge
    map.addLayer({
        'id': 'beaches-fill',
        'type': 'fill',
        'source': 'beaches',
        'layout': {
            'visibility': 'visible'
        },
        'paint': {
            'fill-color': [
                'interpolate',
                ['linear'],
                ['get', 'risk_index'],
                0, '#2ecc71', // Verde per rischio basso
                0.5, '#f1c40f', // Giallo per rischio medio
                1, '#e74c3c'  // Rosso per rischio alto
            ],
            'fill-opacity': 0.7
        }
    });
    
    // Aggiungi layer per il contorno delle spiagge
    map.addLayer({
        'id': 'beaches-outline',
        'type': 'line',
        'source': 'beaches',
        'layout': {
            'visibility': 'visible'
        },
        'paint': {
            'line-color': '#000',
            'line-width': 1
        }
    });
    
    // Aggiungi popup alle spiagge
    addBeachClickHandlers(map);
    
    console.log('Layer spiagge caricato con successo');
}

// Funzione separata per aggiungere i gestori di eventi di click con popup migliorati
function addBeachClickHandlers(map) {
    console.log('Configurazione gestori di eventi per le spiagge');
    
    // Prima rimuovi eventuali eventi preesistenti per evitare duplicati
    map.off('click', 'beaches-fill');
    map.off('mouseenter', 'beaches-fill');
    map.off('mouseleave', 'beaches-fill');
    
    // Rimuoviamo l'event listener globale che potrebbe bloccare i click sulle spiagge
    map.off('click');
    
    // Variabile globale per tenere traccia del popup attivo
    let activePopup = null;
    
    // Aggiungi popup alle spiagge - questo evento deve essere registrato PRIMA dell'evento globale
    map.on('click', 'beaches-fill', function(e) {
        console.log('Click su spiaggia rilevato');
        
        if (!e.features || e.features.length === 0) {
            console.log('Nessuna caratteristica trovata nel click');
            return;
        }
        
        // Chiudi il popup attivo se esiste
        if (activePopup) {
            activePopup.remove();
            activePopup = null;
        }
        
        const properties = e.features[0].properties;
        console.log('Spiaggia cliccata:', properties);
        
        // Formatta i valori con le unità appropriate
        const length = properties.length ? parseFloat(properties.length).toFixed(1) + ' m' : 'N/A';
        const width = properties.width ? parseFloat(properties.width).toFixed(1) + ' m' : 'N/A';
        const riskIndex = properties.risk_index ? parseFloat(properties.risk_index).toFixed(2) : 'N/A';
        const erosionRate = properties.erosion_rate ? parseFloat(properties.erosion_rate).toFixed(2) + ' m/anno' : 'N/A';
        
        // Determina la classe di rischio per colore
        let riskClass = '';
        if (properties.risk_index) {
            const risk = parseFloat(properties.risk_index);
            if (risk < 0.33) riskClass = 'low-risk';
            else if (risk < 0.66) riskClass = 'medium-risk';
            else riskClass = 'high-risk';
        }
        
        // Crea contenuto popup migliorato
        const content = `
            <h3>${properties.name || 'Spiaggia'}</h3>
            <p><strong>Lunghezza:</strong> <span>${length}</span></p>
            <p><strong>Larghezza:</strong> <span>${width}</span></p>
            <p><strong>Indice di Rischio:</strong> <span class="${riskClass}">${riskIndex}</span></p>
            <p><strong>Tasso di Erosione:</strong> <span>${erosionRate}</span></p>
            <div class="popup-buttons">
                <button class="popup-button popup-button-risk" onclick="window.location.href='/risk-report?beach=${properties.id}'">
                    <i class="fas fa-chart-line"></i> Report Rischio
                </button>
                <button class="popup-button popup-button-hazard" onclick="window.location.href='/hazard-report?beach=${properties.id}'">
                    <i class="fas fa-exclamation-triangle"></i> Report Pericolo
                </button>
            </div>
        `;
        
        // Crea e mostra il popup con animazione
        activePopup = new mapboxgl.Popup({
            closeButton: true,
            closeOnClick: false,
            className: 'beach-popup',
            maxWidth: '320px'
        })
            .setLngLat(e.lngLat)
            .setHTML(content)
            .addTo(map);
            
        // Aggiungi event listener per rimuovere il riferimento quando il popup viene chiuso
        activePopup.on('close', function() {
            activePopup = null;
        });
        
        // Previeni la propagazione dell'evento alla mappa
        e.stopPropagation();
    });
    
    // Chiudi il popup quando si clicca sulla mappa (fuori da un popup) - questo evento deve essere dopo
    map.on('click', function(e) {
        // Non far nulla se il click è stato già elaborato da un'altra funzione
        if (e.defaultPrevented) return;
        
        console.log('Click su mappa (non spiaggia)');
        if (activePopup) {
            activePopup.remove();
            activePopup = null;
        }
    });
    
    // Cambia il cursore quando è sopra una spiaggia
    map.on('mouseenter', 'beaches-fill', function() {
        map.getCanvas().style.cursor = 'pointer';
    });
    
    map.on('mouseleave', 'beaches-fill', function() {
        map.getCanvas().style.cursor = '';
    });
    
    console.log('Gestori di eventi configurati');
}

// Funzione per caricare il layer economia
function loadEconomyLayer(map, geojson) {
    console.log('Caricamento layer economia');
    
    // Rimuovi la fonte se già esiste
    if (map.getSource('economy')) {
        if (map.getLayer('economy-layer')) map.removeLayer('economy-layer');
        map.removeSource('economy');
    }
    
    if (!geojson) {
        console.warn('Dati economia non disponibili');
        return;
    }
    
    // Aggiungi fonte e layer
    map.addSource('economy', {
        type: 'geojson',
        data: geojson
    });
    
    map.addLayer({
        'id': 'economy-layer',
        'type': 'fill',
        'source': 'economy',
        'layout': {
            'visibility': 'none'
        },
        'paint': {
            'fill-color': '#3498db',
            'fill-opacity': 0.5
        }
    });
    
    console.log('Layer economia caricato con successo');
}

// Funzione per caricare il layer pericoli
function loadHazardsLayer(map, geojson) {
    console.log('Caricamento layer pericoli');
    
    // Rimuovi la fonte se già esiste
    if (map.getSource('hazards')) {
        if (map.getLayer('hazards-layer')) map.removeLayer('hazards-layer');
        map.removeSource('hazards');
    }
    
    if (!geojson) {
        console.warn('Dati pericoli non disponibili');
        return;
    }
    
    // Aggiungi fonte e layer
    map.addSource('hazards', {
        type: 'geojson',
        data: geojson
    });
    
    map.addLayer({
        'id': 'hazards-layer',
        'type': 'fill',
        'source': 'hazards',
        'layout': {
            'visibility': 'none'
        },
        'paint': {
            'fill-color': '#e74c3c',
            'fill-opacity': 0.5
        }
    });
    
    console.log('Layer pericoli caricato con successo');
}

// Funzione per cambiare la visibilità dei layer
function toggleLayerVisibility(map, layerSelection) {
    console.log('Cambio layer a:', layerSelection);
    
    // Nascondi tutti i layer prima
    if (map.getLayer('beaches-fill')) {
        map.setLayoutProperty('beaches-fill', 'visibility', 'none');
    }
    if (map.getLayer('beaches-outline')) {
        map.setLayoutProperty('beaches-outline', 'visibility', 'none');
    }
    if (map.getLayer('economy-layer')) {
        map.setLayoutProperty('economy-layer', 'visibility', 'none');
    }
    if (map.getLayer('hazards-layer')) {
        map.setLayoutProperty('hazards-layer', 'visibility', 'none');
    }
    
    // Mostra solo i layer selezionati
    switch (layerSelection) {
        case 'beaches':
            if (map.getLayer('beaches-fill')) {
                map.setLayoutProperty('beaches-fill', 'visibility', 'visible');
            }
            if (map.getLayer('beaches-outline')) {
                map.setLayoutProperty('beaches-outline', 'visibility', 'visible');
            }
            break;
        case 'risk':
            if (map.getLayer('economy-layer')) {
                map.setLayoutProperty('economy-layer', 'visibility', 'visible');
            }
            break;
        case 'hazard':
            if (map.getLayer('hazards-layer')) {
                map.setLayoutProperty('hazards-layer', 'visibility', 'visible');
            }
            break;
        case 'all':
            if (map.getLayer('beaches-fill')) {
                map.setLayoutProperty('beaches-fill', 'visibility', 'visible');
            }
            if (map.getLayer('beaches-outline')) {
                map.setLayoutProperty('beaches-outline', 'visibility', 'visible');
            }
            if (map.getLayer('economy-layer')) {
                map.setLayoutProperty('economy-layer', 'visibility', 'visible');
            }
            if (map.getLayer('hazards-layer')) {
                map.setLayoutProperty('hazards-layer', 'visibility', 'visible');
            }
            break;
    }
    
    console.log('Visibilità layer aggiornata');
}

// Funzione per aggiornare i dati della mappa in base all'anno
function updateMapData(map, year) {
    console.log('Aggiornamento dati mappa per anno:', year);
    
    // Mostra indicatore di caricamento
    const mapContainer = document.querySelector('.map-container');
    if (mapContainer) {
        let loadingIndicator = mapContainer.querySelector('.loading-indicator');
        if (!loadingIndicator) {
            loadingIndicator = document.createElement('div');
            loadingIndicator.className = 'loading-indicator';
            loadingIndicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Caricamento...';
            loadingIndicator.style.position = 'absolute';
            loadingIndicator.style.top = '10px';
            loadingIndicator.style.left = '50%';
            loadingIndicator.style.transform = 'translateX(-50%)';
            loadingIndicator.style.padding = '5px 10px';
            loadingIndicator.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            loadingIndicator.style.color = 'white';
            loadingIndicator.style.borderRadius = '4px';
            loadingIndicator.style.zIndex = '1000';
            mapContainer.appendChild(loadingIndicator);
        } else {
            loadingIndicator.style.display = 'block';
        }
    }
    
    fetch(`/api/map-data?year=${year}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Errore API: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Errore nel caricamento dei dati:', data.error);
                return;
            }
            
            // Aggiorna i dati della mappa
            if (map.getSource('beaches')) {
                map.getSource('beaches').setData(data.geojson);
                
                // Dopo aver aggiornato i dati, adatta la vista se necessario
                // Ma solo se c'è stata una modifica significativa nei dati
                if (year > 2030 || year < 2020) { // Solo per cambiamenti significativi
                    fitMapToBounds(map, data.geojson);
                }
            } else if (data.geojson) {
                // Se la fonte non esiste ancora, ricrea il layer
                loadBeachesLayer(map, data.geojson);
                
                // Ripristina la visibilità corretta del layer
                toggleLayerVisibility(map, selectedLayer);
                
                // Adatta la vista ai nuovi dati
                fitMapToBounds(map, data.geojson);
            }
            
            // Aggiorna anche la tabella delle spiagge se esiste
            updateBeachesTable(data.beaches);
            
            // Aggiorna le statistiche
            updateStatistics(data.stats);
            
            console.log('Dati mappa aggiornati con successo');
        })
        .catch(error => {
            console.error('Errore nella richiesta API:', error);
        })
        .finally(() => {
            // Nascondi indicatore di caricamento
            const mapContainer = document.querySelector('.map-container');
            if (mapContainer) {
                const loadingIndicator = mapContainer.querySelector('.loading-indicator');
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
            }
        });
}

// Funzione per adattare la vista della mappa ai confini di un GeoJSON
function fitMapToBounds(map, geojson) {
    if (!geojson || !geojson.features || geojson.features.length === 0) {
        console.warn('Impossibile adattare la vista: dati GeoJSON non validi');
        return;
    }
    
    try {
        // Calcoliamo i confini (bounds) del GeoJSON
        const bounds = new mapboxgl.LngLatBounds();
        
        // Iteriamo su tutte le features nel GeoJSON
        geojson.features.forEach(feature => {
            // Gestiamo diverse geometrie
            if (feature.geometry && feature.geometry.coordinates) {
                if (feature.geometry.type === 'Polygon') {
                    // Per i poligoni, iteriamo su tutte le coordinate dell'anello esterno
                    feature.geometry.coordinates[0].forEach(coord => {
                        bounds.extend(coord);
                    });
                } else if (feature.geometry.type === 'MultiPolygon') {
                    // Per i multipoligoni, iteriamo su tutti i poligoni
                    feature.geometry.coordinates.forEach(polygon => {
                        polygon[0].forEach(coord => {
                            bounds.extend(coord);
                        });
                    });
                } else if (feature.geometry.type === 'Point') {
                    bounds.extend(feature.geometry.coordinates);
                } else if (feature.geometry.type === 'LineString') {
                    feature.geometry.coordinates.forEach(coord => {
                        bounds.extend(coord);
                    });
                } else if (feature.geometry.type === 'MultiLineString') {
                    feature.geometry.coordinates.forEach(line => {
                        line.forEach(coord => {
                            bounds.extend(coord);
                        });
                    });
                }
            }
        });
        
        // Se abbiamo coordinate valide, zoom sui bounds
        if (!bounds.isEmpty()) {
            console.log('Adattamento della vista ai dati GeoJSON');
            
            // Aggiungiamo un padding per un po' di spazio intorno
            map.fitBounds(bounds, {
                padding: { top: 50, bottom: 50, left: 50, right: 50 },
                maxZoom: 15, // Limita lo zoom massimo
                duration: 1000 // Animazione di 1 secondo
            });
        } else {
            console.warn('Bounds vuoti, impossibile adattare la vista');
        }
    } catch (error) {
        console.error('Errore durante il calcolo dei bounds:', error);
    }
}

// Funzione per aggiornare la tabella delle spiagge
function updateBeachesTable(beaches) {
    const table = document.getElementById('beachesTable');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    
    beaches.forEach(beach => {
        const row = document.createElement('tr');
        
        const nameCell = document.createElement('td');
        nameCell.textContent = beach.name || 'N/A';
        
        const lengthCell = document.createElement('td');
        lengthCell.textContent = beach.length ? parseFloat(beach.length).toFixed(1) : 'N/A';
        
        const widthCell = document.createElement('td');
        widthCell.textContent = beach.width ? parseFloat(beach.width).toFixed(1) : 'N/A';
        
        const riskCell = document.createElement('td');
        riskCell.textContent = beach.risk_index ? parseFloat(beach.risk_index).toFixed(2) : 'N/A';
        
        const erosionCell = document.createElement('td');
        erosionCell.textContent = beach.erosion_rate ? parseFloat(beach.erosion_rate).toFixed(2) : 'N/A';
        
        const actionsCell = document.createElement('td');
        
        // Link per report di rischio
        const riskLink = document.createElement('a');
        riskLink.className = 'action-button';
        riskLink.href = `/risk-report?beach=${beach.id}`;
        riskLink.innerHTML = '<i class="fas fa-chart-line"></i> Rischio';
        actionsCell.appendChild(riskLink);
        
        // Link per report di pericolo
        const hazardLink = document.createElement('a');
        hazardLink.className = 'action-button action-button-secondary';
        hazardLink.href = `/hazard-report?beach=${beach.id}`;
        hazardLink.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Pericolo';
        actionsCell.appendChild(hazardLink);
        
        row.appendChild(nameCell);
        row.appendChild(lengthCell);
        row.appendChild(widthCell);
        row.appendChild(riskCell);
        row.appendChild(erosionCell);
        row.appendChild(actionsCell);
        
        tbody.appendChild(row);
    });
}

// Mostra dettagli di una spiaggia
function showBeachDetails(beachId) {
    if (!beachId) {
        console.error('ID spiaggia mancante');
        return;
    }
    
    // Reindirizza a pagina di report rischio
    window.location.href = `/risk-report?beach=${beachId}`;
}

// Aggiorna il pannello statistiche
function updateStatistics(stats) {
    if (!stats) return;
    
    const avgWidthEl = document.getElementById('avg-width');
    const avgRiskEl = document.getElementById('avg-risk');
    const criticalBeachesEl = document.getElementById('critical-beaches');
    
    if (avgWidthEl && stats.avg_width_reduction !== undefined) {
        let originalWidth = parseFloat(avgWidthEl.textContent);
        if (isNaN(originalWidth)) {
            // Estrai il numero dalla stringa "XX m"
            const match = avgWidthEl.textContent.match(/([0-9.]+)/);
            originalWidth = match ? parseFloat(match[1]) : 0;
        }
        const newAvgWidth = Math.max(0, originalWidth - stats.avg_width_reduction).toFixed(1);
        avgWidthEl.textContent = newAvgWidth + ' m';
    }
    
    if (avgRiskEl && stats.avg_risk_increase !== undefined) {
        let originalRisk = parseFloat(avgRiskEl.textContent);
        if (isNaN(originalRisk)) {
            // Se il valore è NaN, prova a estrarlo come numero
            const match = avgRiskEl.textContent.match(/([0-9.]+)/);
            originalRisk = match ? parseFloat(match[1]) : 0;
        }
        const newAvgRisk = Math.min(1, originalRisk + stats.avg_risk_increase).toFixed(2);
        avgRiskEl.textContent = newAvgRisk;
    }
    
    if (criticalBeachesEl && stats.critically_eroded !== undefined) {
        criticalBeachesEl.textContent = stats.critically_eroded;
    }
}

// Ridefiniamo la funzione showBeachDetails in modo che sia disponibile globalmente
window.showBeachDetails = function(beachId) {
    if (!beachId) {
        console.error('ID spiaggia mancante');
        return;
    }
    
    console.log('Visualizzazione dettagli spiaggia:', beachId);
    window.location.href = `/risk-report?beach=${beachId}`;
};