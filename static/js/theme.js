/**
 * Script migliorato per gestire il cambio tema con transizioni più fluide
 * e preservazione delle preferenze utente
 */
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle ? themeToggle.querySelector('i') : null;
    
    // Variabile per tracciare lo stato corrente del tema
    let isDarkTheme = localStorage.getItem('darkTheme') === 'true';
    
    // Imposta il tema iniziale al caricamento della pagina
    if (isDarkTheme) {
        document.body.classList.add('dark-theme');
        if (themeIcon) themeIcon.className = 'fas fa-sun';
    } else {
        if (themeIcon) themeIcon.className = 'fas fa-moon';
    }
    
    /**
     * Applica il tema con transizione graduale
     * @param {boolean} dark - Se true applica tema scuro, altrimenti tema chiaro
     */
    function applyTheme(dark) {
        // Salva la preferenza
        localStorage.setItem('darkTheme', dark);
        isDarkTheme = dark;
        
        // Prepara l'animazione
        document.body.classList.add('theme-transitioning');
        
        // Aggiungi overlay temporaneo per la transizione
        const overlay = document.createElement('div');
        overlay.className = 'theme-transition-overlay';
        overlay.style.opacity = '0';
        document.body.appendChild(overlay);
        
        // Fase 1: fade-in dell'overlay
        requestAnimationFrame(() => {
            overlay.style.opacity = '0.12'; // Opacità leggera per non accecare l'utente
            
            setTimeout(() => {
                // Fase 2: applica il tema sotto l'overlay
                if (dark) {
                    document.body.classList.add('dark-theme');
                    if (themeIcon) themeIcon.className = 'fas fa-sun';
                } else {
                    document.body.classList.remove('dark-theme');
                    if (themeIcon) themeIcon.className = 'fas fa-moon';
                }

                // Fase 2.5: Invia un evento personalizzato per aggiornare la mappa
                const event = new CustomEvent('themeChanged', {
                    detail: {
                        theme: dark ? 'dark' : 'light'
                    }
                });
                document.dispatchEvent(event);
                
                // Fase 3: fade-out dell'overlay ed eliminazione
                setTimeout(() => {
                    overlay.style.opacity = '0';
                    
                    setTimeout(() => {
                        document.body.removeChild(overlay);
                        document.body.classList.remove('theme-transitioning');
                    }, 350); // Durata del fade-out
                }, 100); // Piccola pausa per applicare il tema
            }, 150); // Durata del fade-in
        });
    }
    
    // Gestisci il click sul pulsante tema
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            // Toggle del tema
            applyTheme(!isDarkTheme);
        });
    }
    
    // Preferenze utente da sistema operativo (rispetto del prefers-color-scheme)
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Se l'utente non ha impostato una preferenza, usa quella del sistema
    if (localStorage.getItem('darkTheme') === null) {
        applyTheme(prefersDark.matches);
    }
    
    // Ascolta cambiamenti nelle preferenze di sistema
    prefersDark.addEventListener('change', (e) => {
        // Cambia il tema solo se l'utente non ha impostato una preferenza manuale
        if (localStorage.getItem('darkThemeManual') !== 'true') {
            applyTheme(e.matches);
        }
    });
    
    // Quando si clicca manualmente, imposta flag per ignorare preferenze sistema
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            localStorage.setItem('darkThemeManual', 'true');
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