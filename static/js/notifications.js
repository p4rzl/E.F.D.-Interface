document.addEventListener('DOMContentLoaded', function() {
    // Seleziona tutte le notifiche
    const notifications = document.querySelectorAll('.notification');
    
    // Aggiungi un listener per ogni notifica per chiuderla al click
    notifications.forEach(notification => {
        notification.addEventListener('click', function() {
            // Aggiungi classe per l'animazione di uscita
            this.style.opacity = '0';
            this.style.transform = 'translateY(-10px)';
            
            // Rimuovi l'elemento dopo l'animazione
            setTimeout(() => {
                this.remove();
            }, 300);
        });
        
        // Aggiungi un timeout per rimuovere automaticamente la notifica
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateY(-10px)';
                
                // Rimuovi l'elemento dopo l'animazione
                setTimeout(() => {
                    if (notification && notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 8000); // Rimuovi dopo 8 secondi
    });
});
