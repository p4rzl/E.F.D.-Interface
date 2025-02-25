// static/js/charts.js

document.addEventListener('DOMContentLoaded', function() {
    // Funzione globale per mostrare i grafici di una spiaggia
    window.showBeachCharts = function(beachId) {
        // Trova i dati della spiaggia
        const beach = beachesData.find(b => b.id == beachId);
        
        if (!beach) {
            console.error('Spiaggia non trovata: ', beachId);
            return;
        }
        
        // Implementazione dei grafici
        // In un'implementazione reale, questi dati verrebbero caricati dinamicamente
        const years = Array.from({length: 78}, (_, i) => 2023 + i);
        
        // Simula dati di erosione (in un'implementazione reale, questi verrebbero dai dati)
        const erosionRate = beach.erosion_rate || 0;
        const erosionData = years.map(year => {
            // Simula erosione progressiva
            const yearsPassed = year - 2023;
            return Math.max(0, (beach.width || 100) - (erosionRate * yearsPassed));
        });
        
        // Crea il grafico
        const ctx = document.getElementById('erosionChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: years,
                    datasets: [{
                        label: 'Larghezza della spiaggia (m)',
                        data: erosionData,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Larghezza (m)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Anno'
                            }
                        }
                    }
                }
            });
        }
    };
});