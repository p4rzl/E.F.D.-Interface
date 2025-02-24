document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const icon = themeToggle.querySelector('i');
    
    // Controlla se c'è una preferenza salvata
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Aggiorna l'icona
    if (currentTheme === 'dark') {
        icon.classList.replace('fa-moon', 'fa-sun');
    }
    
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        // Cambia il tema
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Cambia l'icona
        if (newTheme === 'dark') {
            icon.classList.replace('fa-moon', 'fa-sun');
        } else {
            icon.classList.replace('fa-sun', 'fa-moon');
        }
    });

    // Apply theme to timeline and legend
    const applyThemeToElements = () => {
        const theme = document.documentElement.getAttribute('data-theme');
        const timeline = document.querySelector('.time-control');
        const legend = document.querySelector('.legend');

        if (timeline) {
            timeline.style.backgroundColor = theme === 'dark' ? '#1a1a1a' : '#fff';
            timeline.style.color = theme === 'dark' ? '#fff' : '#000';
        }

        if (legend) {
            legend.style.backgroundColor = theme === 'dark' ? '#1a1a1a' : '#fff';
            legend.style.color = theme === 'dark' ? '#fff' : '#000';
        }
    };

    // Apply theme on load
    applyThemeToElements();

    // Apply theme on theme change
    themeToggle.addEventListener('click', applyThemeToElements);
});
