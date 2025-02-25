// static/js/map.js

// Inizializzazione della mappa
document.addEventListener('DOMContentLoaded', function() {
    if (!mapboxToken) {
        console.error('Token Mapbox non trovato');
        return;
    }

    mapboxgl.accessToken = mapboxToken;
    
    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/satellite-v9', // Passa a satellite view come negli old files
        center: [1.2921, 41.1177], // Coordinate approssimative della Spagna orientale
        zoom: 9
    });

    map.addControl(new mapboxgl.NavigationControl());

    // Statistiche predittive
    const statsContainer = document.createElement('div');
    statsContainer.className = 'prediction-stats';
    statsContainer.innerHTML = `
        <h3>Statistiche Previsionali</h3>
        <div id="predictionStats">
            <p>Anno: <span id="statYear">2023</span></p>
            <p>Riduzione media larghezza: <span id="statWidthReduction">0.0</span> m</p>
            <p>Aumento medio rischio: <span id="statRiskIncrease">0.0</span></p>
            <p>Spiagge critiche: <span id="statCritical">0</span>/<span id="statTotal">0</span></p>
        </div>
    `;
    document.querySelector('.map-controls').appendChild(statsContainer);

    // Aggiungi layer quando la mappa è caricata
    map.on('load', function() {
        // Aggiungi il layer delle spiagge se abbiamo i dati GeoJSON
        if (beachesGeoJSON) {
            map.addSource('beaches', {
                type: 'geojson',
                data: beachesGeoJSON
            });

            map.addLayer({
                id: 'beaches-layer',
                type: 'fill',
                source: 'beaches',
                paint: {
                    'fill-color': [
                        'interpolate',
                        ['linear'],
                        ['get', 'risk_index'],
                        0, '#0080ff',  // blu per rischio basso
                        0.5, '#ffff00', // giallo per rischio medio
                        1.0, '#ff0000'  // rosso per rischio alto
                    ],
                    'fill-opacity': 0.6,
                    'fill-outline-color': '#000'
                }
            });
            
            // Aggiungi anche il contorno delle spiagge
            map.addLayer({
                id: 'beaches-outline',
                type: 'line',
                source: 'beaches',
                paint: {
                    'line-color': '#000',
                    'line-width': 2
                }
            });

            // Aggiungi popup per le spiagge
            map.on('click', 'beaches-layer', function(e) {
                const properties = e.features[0].properties;
                
                // Controlla se le proprietà esistono prima di usarle
                const name = properties.name || 'Spiaggia sconosciuta';
                const length = properties.length ? Number(properties.length).toFixed(1) + ' m' : 'N/A';
                const width = properties.width ? Number(properties.width).toFixed(1) + ' m' : 'N/A';
                const riskIndex = properties.risk_index ? Number(properties.risk_index).toFixed(2) : 'N/A';
                
                // Aggiungi classe di colore in base al rischio
                let riskClass = '';
                let riskText = '';
                
                if (properties.risk_index) {
                    const risk = Number(properties.risk_index);
                    if (risk < 0.4) {
                        riskClass = 'risk-low';
                        riskText = 'basso';
                    } else if (risk < 0.7) {
                        riskClass = 'risk-medium';
                        riskText = 'medio';
                    } else {
                        riskClass = 'risk-high';
                        riskText = 'alto';
                    }
                }
                
                // Stato di erosione
                let erosionState = '';
                if (properties.width) {
                    const width = Number(properties.width);
                    if (width < 5) {
                        erosionState = '<p class="critical-warning">Stato critico!</p>';
                    } else if (width < 10) {
                        erosionState = '<p class="warning">Attenzione: erosione significativa</p>';
                    }
                }
                
                const popup = new mapboxgl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <h3>${name}</h3>
                        <p>Lunghezza: ${length}</p>
                        <p>Larghezza: ${width}</p>
                        <p>Indice di rischio: <span class="${riskClass}">${riskIndex} (${riskText})</span></p>
                        ${erosionState}
                        <button class="popup-button" onclick="showBeachDetails('${properties.id || 0}')">Dettagli</button>
                    `)
                    .addTo(map);
            });

            // Cambia il cursore quando si passa sopra il layer delle spiagge
            map.on('mouseenter', 'beaches-layer', function() {
                map.getCanvas().style.cursor = 'pointer';
            });

            map.on('mouseleave', 'beaches-layer', function() {
                map.getCanvas().style.cursor = '';
            });
            
            // Zoom alla prima spiaggia disponibile
            if (beachesGeoJSON.features && beachesGeoJSON.features.length > 0) {
                const firstFeature = beachesGeoJSON.features[0];
                const bounds = new mapboxgl.LngLatBounds();
                
                if (firstFeature.geometry && firstFeature.geometry.type === 'Polygon') {
                    firstFeature.geometry.coordinates[0].forEach(coord => {
                        bounds.extend(coord);
                    });
                    
                    map.fitBounds(bounds, {
                        padding: 50,
                        maxZoom: 15
                    });
                }
            }
        }
        
        // Aggiungi il layer dell'economia se disponibile
        if (economyGeoJSON) {
            map.addSource('economy', {
                type: 'geojson',
                data: economyGeoJSON
            });

            map.addLayer({
                id: 'economy-layer',
                type: 'fill',
                source: 'economy',
                layout: {
                    'visibility': 'none'
                },
                paint: {
                    'fill-color': '#4287f5',
                    'fill-opacity': 0.5,
                    'fill-outline-color': '#2463cc'
                }
            });
        }
        
        // Aggiungi il layer dei pericoli se disponibile
        if (hazardsGeoJSON) {
            map.addSource('hazards', {
                type: 'geojson',
                data: hazardsGeoJSON
            });

            map.addLayer({
                id: 'hazards-layer',
                type: 'fill',
                source: 'hazards',
                layout: {
                    'visibility': 'none'
                },
                paint: {
                    'fill-color': '#e74c3c',
                    'fill-opacity': 0.5,
                    'fill-outline-color': '#c0392b'
                }
            });
        }

        // Aggiungi la legenda
        const legend = document.createElement('div');
        legend.className = 'map-legend';
        legend.innerHTML = `
            <h4>Legenda</h4>
            <div>
                <span class="legend-color" style="background-color: #0080ff"></span> Rischio basso
            </div>
            <div>
                <span class="legend-color" style="background-color: #ffff00"></span> Rischio medio
            </div>
            <div>
                <span class="legend-color" style="background-color: #ff0000"></span> Rischio alto
            </div>
        `;
        document.querySelector('.map-container').appendChild(legend);
    });

    // Gestione del selettore di layer
    document.getElementById('layerSelect').addEventListener('change', function(e) {
        const layerType = e.target.value;
        
        // Nascondi tutti i layer
        if (map.getLayer('beaches-layer')) {
            map.setLayoutProperty('beaches-layer', 'visibility', 'none');
            map.setLayoutProperty('beaches-outline', 'visibility', 'none');
        }
        if (map.getLayer('economy-layer')) {
            map.setLayoutProperty('economy-layer', 'visibility', 'none');
        }
        if (map.getLayer('hazards-layer')) {
            map.setLayoutProperty('hazards-layer', 'visibility', 'none');
        }
        
        // Mostra il layer selezionato o tutti
        if (layerType === 'all') {
            if (map.getLayer('beaches-layer')) {
                map.setLayoutProperty('beaches-layer', 'visibility', 'visible');
                map.setLayoutProperty('beaches-outline', 'visibility', 'visible');
            }
            if (map.getLayer('economy-layer')) {
                map.setLayoutProperty('economy-layer', 'visibility', 'visible');
            }
            if (map.getLayer('hazards-layer')) {
                map.setLayoutProperty('hazards-layer', 'visibility', 'visible');
            }
        } else if (layerType === 'beaches' && map.getLayer('beaches-layer')) {
            map.setLayoutProperty('beaches-layer', 'visibility', 'visible');
            map.setLayoutProperty('beaches-outline', 'visibility', 'visible');
        } else if (layerType === 'risk' && map.getLayer('economy-layer')) {
            map.setLayoutProperty('economy-layer', 'visibility', 'visible');
        } else if (layerType === 'hazard' && map.getLayer('hazards-layer')) {
            map.setLayoutProperty('hazards-layer', 'visibility', 'visible');
        }
    });

    // Migliora la gestione dello slider degli anni
    const yearSlider = document.getElementById('yearSlider');
    const yearValue = document.getElementById('yearValue');
    
    yearSlider.addEventListener('input', function(e) {
        const year = parseInt(e.target.value);
        yearValue.textContent = year;
    });
    
    yearSlider.addEventListener('change', function(e) {
        const year = parseInt(e.target.value);
        yearValue.textContent = year;
        
        // Mostra indicatore di caricamento
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.innerHTML = 'Caricamento previsioni...';
        document.querySelector('.map-controls').appendChild(loadingIndicator);
        
        // Carica e aggiorna i dati per l'anno selezionato
        fetch(`/api/map-data?year=${year}`)
            .then(response => response.json())
            .then(data => {
                // Rimuovi l'indicatore di caricamento
                document.querySelector('.loading-indicator').remove();
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                // Aggiorna i dati della tabella con i valori previsti
                updateTableWithPredictions(data);
                
                // Aggiorna i dati della mappa
                if (data.geojson && map.getSource('beaches')) {
                    map.getSource('beaches').setData(data.geojson);
                }
                
                // Aggiorna le statistiche predittive
                updatePredictionStats(data.stats);
                
                // Evidenzia l'anno corrente nella UI
                highlightCurrentYear(year);
            })
            .catch(error => {
                // Rimuovi l'indicatore di caricamento in caso di errore
                if (document.querySelector('.loading-indicator')) {
                    document.querySelector('.loading-indicator').remove();
                }
                console.error('Errore nel caricamento delle previsioni:', error);
                showError('Errore nel caricamento delle previsioni');
            });
    });
    
    // Funzione per mostrare errori
    function showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'map-error';
        errorElement.textContent = message;
        
        document.querySelector('.map-container').appendChild(errorElement);
        
        // Rimuovi dopo 5 secondi
        setTimeout(() => {
            if (errorElement.parentNode) {
                errorElement.parentNode.removeChild(errorElement);
            }
        }, 5000);
    }
    
    // Funzione per evidenziare l'anno corrente
    function highlightCurrentYear(year) {
        const yearHighlight = document.getElementById('yearHighlight') || document.createElement('div');
        yearHighlight.id = 'yearHighlight';
        
        // Determina la classe in base al confronto con l'anno attuale
        const currentYear = new Date().getFullYear();
        let yearClass = 'year-future';
        let yearStatus = 'Previsione futura';
        
        if (year < currentYear) {
            yearClass = 'year-past';
            yearStatus = 'Dati storici';
        } else if (year === currentYear) {
            yearClass = 'year-current';
            yearStatus = 'Anno corrente';
        }
        
        yearHighlight.className = `year-indicator ${yearClass}`;
        yearHighlight.innerHTML = `<strong>${yearStatus}</strong>: ${year}`;
        
        const controlsContainer = document.querySelector('.map-controls');
        if (!document.getElementById('yearHighlight')) {
            controlsContainer.appendChild(yearHighlight);
        }
    }
    
    // Funzione per aggiornare le statistiche predittive
    function updatePredictionStats(stats) {
        if (!stats) return;
        
        document.getElementById('statYear').textContent = stats.year;
        document.getElementById('statWidthReduction').textContent = stats.avg_width_reduction.toFixed(2);
        document.getElementById('statRiskIncrease').textContent = stats.avg_risk_increase.toFixed(4);
        document.getElementById('statCritical').textContent = stats.critically_eroded;
        document.getElementById('statTotal').textContent = stats.total_beaches;
    }
});

// Funzione per aggiornare la tabella con i dati di previsione
function updateTableWithPredictions(data) {
    const table = document.getElementById('beachesTable');
    if (!table || !data.beaches) return;
    
    const tbody = table.querySelector('tbody');
    
    // Svuota la tabella
    tbody.innerHTML = '';
    
    // Popola la tabella con i nuovi dati
    data.beaches.forEach(beach => {
        const row = document.createElement('tr');
        
        // Aggiungi classe in base alla larghezza
        if (beach.width < 5) {
            row.classList.add('critical-beach');
        } else if (beach.width < 10) {
            row.classList.add('warning-beach');
        }
        
        // Nome spiaggia
        const nameCell = document.createElement('td');
        nameCell.textContent = beach.name || 'N/A';
        row.appendChild(nameCell);
        
        // Lunghezza
        const lengthCell = document.createElement('td');
        lengthCell.textContent = beach.length !== null ? parseFloat(beach.length).toFixed(1) : 'N/A';
        row.appendChild(lengthCell);
        
        // Larghezza
        const widthCell = document.createElement('td');
        widthCell.textContent = beach.width !== null ? parseFloat(beach.width).toFixed(1) : 'N/A';
        row.appendChild(widthCell);
        
        // Indice di rischio
        const riskCell = document.createElement('td');
        if (beach.risk_index !== null) {
            const risk = parseFloat(beach.risk_index).toFixed(2);
            riskCell.textContent = risk;
            
            // Aggiungi classe di colore in base al rischio
            if (risk < 0.4) {
                riskCell.classList.add('risk-low');
            } else if (risk < 0.7) {
                riskCell.classList.add('risk-medium');
            } else {
                riskCell.classList.add('risk-high');
            }
        } else {
            riskCell.textContent = 'N/A';
        }
        row.appendChild(riskCell);
        
        // Erosione
        const erosionCell = document.createElement('td');
        erosionCell.textContent = beach.erosion_rate !== null ? parseFloat(beach.erosion_rate).toFixed(2) : 'N/A';
        row.appendChild(erosionCell);
        
        // Pulsante dettagli
        const actionCell = document.createElement('td');
        const detailsButton = document.createElement('button');
        detailsButton.className = 'action-button';
        detailsButton.textContent = 'Dettagli';
        detailsButton.onclick = function() {
            showBeachDetails(beach.id);
        };
        actionCell.appendChild(detailsButton);
        row.appendChild(actionCell);
        
        tbody.appendChild(row);
    });
}

// Funzione per mostrare i dettagli di una spiaggia
window.showBeachDetails = function(beachId) {
    // Trova i dati della spiaggia
    const beach = beachesData.find(b => b.id == beachId);
    
    if (!beach) {
        console.error('Spiaggia non trovata: ', beachId);
        return;
    }
    
    // Crea una finestra modale per mostrare i dettagli
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>${beach.name || 'Spiaggia sconosciuta'}</h2>
            <div class="beach-details">
                <div class="beach-info">
                    <p><strong>Lunghezza:</strong> ${beach.length !== null ? parseFloat(beach.length).toFixed(1) + ' m' : 'N/A'}</p>
                    <p><strong>Larghezza:</strong> ${beach.width !== null ? parseFloat(beach.width).toFixed(1) + ' m' : 'N/A'}</p>
                    <p><strong>Indice di rischio:</strong> ${beach.risk_index !== null ? parseFloat(beach.risk_index).toFixed(2) : 'N/A'}</p>
                    <p><strong>Tasso di erosione:</strong> ${beach.erosion_rate !== null ? parseFloat(beach.erosion_rate).toFixed(2) + ' m/anno' : 'N/A'}</p>
                </div>
                <div class="charts-container">
                    <h3>Previsioni di erosione</h3>
                    <canvas id="erosionChart"></canvas>
                </div>
                <div class="actions">
                    <button onclick="window.open('/risk-report?beach=${beachId}', '_blank')">Report Rischio</button>
                    <button onclick="window.open('/hazard-report?beach=${beachId}', '_blank')">Report Pericolo</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Chiudi la modale quando si clicca sulla X
    modal.querySelector('.close').addEventListener('click', function() {
        document.body.removeChild(modal);
    });
    
    // Chiudi la modale quando si clicca fuori
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            document.body.removeChild(modal);
        }
    });
    
    // Crea il grafico di erosione
    showBeachCharts(beachId);
};