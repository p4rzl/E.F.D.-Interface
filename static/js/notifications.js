document.addEventListener('DOMContentLoaded', function() {
    // Trova tutte le notifiche presenti nella pagina
    const notifications = document.querySelectorAll('.notification');
    
    // Per ogni notifica, imposta un timer per nasconderla
    notifications.forEach(notification => {
        // Determina il tempo di visualizzazione in base al tipo di notifica
        let displayTime = 5000; // Default 5 secondi
        if (notification.classList.contains('error')) {
            displayTime = 8000; // Errori mostrati più a lungo (8 secondi)
        } else if (notification.classList.contains('success')) {
            displayTime = 5000; // Successi mostrati per 5 secondi
        }
        
        // Imposta il timer per far scomparire la notifica
        setTimeout(() => {
            notification.classList.add('fade-out');
            
            // Rimuovi la notifica dal DOM dopo l'animazione
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, displayTime);
    });
});
