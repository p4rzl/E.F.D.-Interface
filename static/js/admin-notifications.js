document.addEventListener('DOMContentLoaded', function() {
    // Seleziona tutte le notifiche amministrative
    const adminNotifications = document.querySelectorAll('.alert-admin');
    
    // Aggiungi un listener per ogni notifica per chiuderla al click
    adminNotifications.forEach(notification => {
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
                notification.remove();
            }
        }, 8000); // Rimuovi dopo 8 secondi (5s visibile + 3s animazione)
    });
});
