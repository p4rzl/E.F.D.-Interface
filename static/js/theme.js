// static/js/theme.js

document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    const iconElement = themeToggle ? themeToggle.querySelector('i') : null;
    
    // Applica il tema iniziale
    document.body.classList.toggle('dark-theme', currentTheme === 'dark');
    
    // Aggiorna l'icona se esiste
    if (iconElement) {
        iconElement.className = currentTheme === 'dark' 
            ? 'fas fa-sun' 
            : 'fas fa-moon';
    }
    
    // Gestione dell'evento di cambio tema
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const isDark = document.body.classList.toggle('dark-theme');
            const theme = isDark ? 'dark' : 'light';
            
            // Salva in localStorage
            localStorage.setItem('theme', theme);
            
            // Aggiorna l'icona
            if (iconElement) {
                iconElement.className = isDark 
                    ? 'fas fa-sun' 
                    : 'fas fa-moon';
            }
            
            // Emetti un evento custom per notificare il cambio tema
            document.dispatchEvent(new CustomEvent('themeChanged', {
                detail: {
                    theme: theme
                }
            }));
        });
    }
    
    // Applica il tema per i report
    const reportContainer = document.querySelector('.report-container');
    if (reportContainer) {
        // Per assicurarsi che il cambio di tema funzioni nei report
        const applyThemeToReport = function() {
            const theme = localStorage.getItem('theme') || 'light';
            document.body.classList.toggle('dark-theme', theme === 'dark');
        };
        
        // Applica il tema all'avvio
        applyThemeToReport();
        
        // Ascolta eventuali cambi di tema
        window.addEventListener('storage', function(e) {
            if (e.key === 'theme') {
                applyThemeToReport();
            }
        });
    }
});