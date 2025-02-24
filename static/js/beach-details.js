function showBeachDetails(beachId) {
    fetch(`/api/beach/${beachId}`)
        .then(response => response.json())
        .then(data => {
            const modal = createModal(data);
            document.body.appendChild(modal);
        })
        .catch(error => console.error('Errore nel caricamento dei dettagli:', error));
}

function createModal(beachData) {
    const modal = document.createElement('div');
    modal.className = 'beach-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${beachData.name}</h3>
            <div class="beach-details">
                <p><strong>Lunghezza:</strong> ${beachData.length} m</p>
                <p><strong>Larghezza:</strong> ${beachData.width} m</p>
                <p><strong>Indice di Rischio:</strong> ${beachData.risk_index}</p>
                <p><strong>Tasso di Erosione:</strong> ${beachData.erosion_rate} m/anno</p>
            </div>
            <div id="beachChart"></div>
            <button onclick="this.parentElement.parentElement.remove()">Chiudi</button>
        </div>
    `;
    return modal;
}