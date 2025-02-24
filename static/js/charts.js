// static/js/charts.js
document.addEventListener('DOMContentLoaded', function() {
    // Inizializza i grafici con i dati
    function initCharts() {
        // Grafico rischi
        const riskData = {
            type: 'scatterpolar',
            r: [4, 5, 3, 2], 
            theta: ['Popolazione', 'Economia', 'Ambiente', 'Infrastrutture'],
            fill: 'toself'
        };
        
        Plotly.newPlot('riskChart', [riskData], {
            polar: {
                radialaxis: {range: [0, 5]}
            }
        });

        // Grafico pericoli
        const hazardData = {
            type: 'scatterpolar',
            r: [3, 4, 2, 5],
            theta: ['Erosione', 'Inondazione', 'Tempeste', 'Subsidenza'],
            fill: 'toself'
        };
        
        Plotly.newPlot('hazardChart', [hazardData], {
            polar: {
                radialaxis: {range: [0, 5]}
            }
        });
    }

    initCharts();
});