/**
 * Gestore del tema chiaro/scuro
 */
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
        // Applica il tema salvato all'avvio
        const savedTheme = localStorage.getItem('theme') || 'light';
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        }
        
        // Gestisci il click sul toggle
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            
            // Aggiorna l'icona
            this.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
            
            // Salva la preferenza nel localStorage
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            
            // Notifica alla mappa di aggiornare lo stile (se presente)
            const themeEvent = new CustomEvent('themeChanged', {
                detail: {
                    theme: isDark ? 'dark' : 'light'
                }
            });
            document.dispatchEvent(themeEvent);
            
            // Aggiorna i grafici se presenti
            updateChartsTheme(isDark);
        });
    }
    
    // Funzione per aggiornare il tema dei grafici se presenti
    function updateChartsTheme(isDark) {
        if (window.chartInstances && typeof Chart !== 'undefined') {
            const chartIds = window.chartInstances.split(',');
            
            chartIds.forEach(id => {
                const chart = Chart.getChart(id.trim());
                if (chart) {
                    // Imposta i colori per il tema corrente
                    const textColor = isDark ? '#ecf0f1' : '#333333';
                    const gridColor = isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)';
                    
                    // Aggiorna i colori del grafico
                    if (chart.options.scales && chart.options.scales.r) {
                        chart.options.scales.r.angleLines.color = gridColor;
                        chart.options.scales.r.grid.color = gridColor;
                        chart.options.scales.r.pointLabels.color = textColor;
                        chart.options.scales.r.ticks.color = textColor;
                    }
                    
                    if (chart.options.plugins && chart.options.plugins.legend) {
                        chart.options.plugins.legend.labels.color = textColor;
                    }
                    
                    chart.update();
                }
            });
        }
    }
});