/* ...existing code... */

// Migliora il supporto per il tema scuro nei popup di Mapbox
function createMapPopup(properties) {
    // Determina se il tema è scuro
    const isDarkTheme = document.body.classList.contains('dark-theme');
    
    // Classe CSS condizionale per il popup
    const themeClass = isDarkTheme ? 'mapboxgl-popup-dark' : '';
    
    const riskClass = properties.risk_index > 0.7 ? 'high-risk' :
                     (properties.risk_index > 0.4 ? 'medium-risk' : 'low-risk');
    
    // Crea il contenuto del popup
    const popupContent = `
        <div class="map-popup ${themeClass}">
            <h3>${properties.name}</h3>
            <div class="popup-details">
                <div class="popup-detail">
                    <span class="detail-label">Lunghezza:</span>
                    <span class="detail-value">${properties.length ? Math.round(properties.length) + ' m' : 'N/A'}</span>
                </div>
                <div class="popup-detail">
                    <span class="detail-label">Larghezza:</span>
                    <span class="detail-value">${properties.width ? Math.round(properties.width) + ' m' : 'N/A'}</span>
                </div>
                <div class="popup-detail">
                    <span class="detail-label">Indice di Rischio:</span>
                    <span class="detail-value risk-indicator ${riskClass}">
                        ${properties.risk_index ? properties.risk_index.toFixed(2) : 'N/A'}
                    </span>
                </div>
                <div class="popup-detail">
                    <span class="detail-label">Tasso di Erosione:</span>
                    <span class="detail-value">${properties.erosion_rate ? properties.erosion_rate.toFixed(2) + ' m/anno' : 'N/A'}</span>
                </div>
            </div>
            <div class="popup-actions">
                <a href="/risk-report?beach=${properties.id}" class="popup-action">Report di Rischio</a>
                <a href="/hazard-report?beach=${properties.id}" class="popup-action">Report di Pericolo</a>
            </div>
        </div>
    `;
    
    return popupContent;
}

// Sovrascrive la funzione per creare popup in Mapbox
function setupMapPopups(map, layer) {
    // Aggiungi CSS per supportare il tema scuro nei popup
    const style = document.createElement('style');
    style.textContent = `
        .mapboxgl-popup-content {
            background-color: var(--bg-color);
            color: var(--text-color);
            border-radius: var(--border-radius);
            padding: 15px;
            box-shadow: var(--shadow-standard);
            transition: background-color 0.3s, color 0.3s;
        }
        
        .mapboxgl-popup-tip {
            border-top-color: var(--bg-color);
            transition: border-color 0.3s;
        }
        
        body.dark-theme .mapboxgl-popup-content {
            background-color: var(--bg-color-secondary);
            border: 1px solid var(--border-color);
        }
        
        body.dark-theme .mapboxgl-popup-tip {
            border-top-color: var(--bg-color-secondary);
        }
        
        .map-popup h3 {
            margin-top: 0;
            color: var(--primary-color);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }
        
        .popup-details {
            margin-bottom: 15px;
        }
        
        .popup-detail {
            margin: 5px 0;
            display: flex;
            justify-content: space-between;
        }
        
        .detail-label {
            font-weight: 500;
            color: var(--text-color);
        }
        
        .detail-value {
            font-weight: 700;
        }
        
        .risk-indicator {
            padding: 2px 6px;
            border-radius: 3px;
        }
        
        .high-risk {
            background-color: rgba(231, 76, 60, 0.2);
            color: #e74c3c;
        }
        
        .medium-risk {
            background-color: rgba(241, 196, 15, 0.2);
            color: #f39c12;
        }
        
        .low-risk {
            background-color: rgba(46, 204, 113, 0.2);
            color: #27ae60;
        }
        
        body.dark-theme .high-risk {
            background-color: rgba(231, 76, 60, 0.3);
            color: #ff6b6b;
        }
        
        body.dark-theme .medium-risk {
            background-color: rgba(241, 196, 15, 0.3);
            color: #ffda79;
        }
        
        body.dark-theme .low-risk {
            background-color: rgba(46, 204, 113, 0.3);
            color: #2ecc71;
        }
        
        .popup-actions {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
        }
        
        .popup-action {
            background-color: var(--primary-color);
            color: white;
            text-decoration: none;
            padding: 6px 10px;
            border-radius: var(--border-radius);
            font-size: 0.85rem;
            transition: all 0.2s;
            text-align: center;
            flex: 0.48;
        }
        
        .popup-action:hover {
            background-color: var(--primary-color-dark);
            transform: translateY(-2px);
        }
    `;
    document.head.appendChild(style);
    
    // Setup click event per i popup
    map.on('click', layer, (e) => {
        const properties = e.features[0].properties;
        
        new mapboxgl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(createMapPopup(properties))
            .addTo(map);
    });
    
    // Cambia il cursore quando si passa sopra una spiaggia
    map.on('mouseenter', layer, () => {
        map.getCanvas().style.cursor = 'pointer';
    });
    
    map.on('mouseleave', layer, () => {
        map.getCanvas().style.cursor = '';
    });
}

/* ...existing code... */
