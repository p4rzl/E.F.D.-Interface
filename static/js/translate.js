/**
 * Script di traduzione migliorato - risolve problemi di ritorno all'italiano e flickering
 */

// Variabili globali
let translationInProgress = false;

// Attendi che il DOM sia completamente caricato
document.addEventListener('DOMContentLoaded', function() {
    // Recupera la lingua salvata
    const savedLanguage = localStorage.getItem('selectedLanguage') || 'it';
    
    // Imposta la lingua attiva nel menu
    updateActiveLanguage(savedLanguage);
    
    // Gestione click sul pulsante lingua per mostrare/nascondere dropdown
    document.addEventListener('click', function(e) {
        const languageToggle = e.target.closest('#language-toggle');
        if (languageToggle) {
            e.preventDefault();
            const dropdown = languageToggle.closest('.language-selector').querySelector('.language-dropdown');
            if (dropdown) {
                dropdown.classList.toggle('show');
                
                // Chiudi il dropdown quando si clicca altrove
                if (dropdown.classList.contains('show')) {
                    setTimeout(() => {
                        document.addEventListener('click', function closeMenu(event) {
                            if (!event.target.closest('.language-selector')) {
                                dropdown.classList.remove('show');
                                document.removeEventListener('click', closeMenu);
                            }
                        });
                    }, 10);
                }
            }
        }
        
        // Gestione click sulle opzioni di lingua
        const languageOption = e.target.closest('.language-option');
        if (languageOption && !translationInProgress) {
            e.preventDefault();
            const lang = languageOption.getAttribute('data-lang');
            if (lang) {
                // Salva la lingua selezionata
                localStorage.setItem('selectedLanguage', lang);
                
                // Aggiorna l'interfaccia
                updateActiveLanguage(lang);
                
                // Chiudi il dropdown
                const dropdown = languageOption.closest('.language-dropdown');
                if (dropdown) {
                    dropdown.classList.remove('show');
                }
                
                // Gestione traduzione
                handleLanguageChange(lang);
            }
        }
    });
    
    // Se c'è una lingua salvata diversa dall'italiano, applicala
    if (savedLanguage && savedLanguage !== 'it') {
        setTimeout(() => {
            handleLanguageChange(savedLanguage);
        }, 1000);
    }
    
    // Inizializza il cookie forzato per tornare all'italiano
    setCookie('googtrans', '/it/it', 1);
});

/**
 * Gestisce il cambio di lingua mostrando un overlay e applicando la traduzione
 */
function handleLanguageChange(lang) {
    // Previeni operazioni multiple contemporanee
    if (translationInProgress) return;
    translationInProgress = true;
    
    // Mostra overlay di caricamento
    showTranslationOverlay(lang !== 'it');
    
    // Gestione diversa per italiano vs altre lingue
    if (lang === 'it') {
        // Per l'italiano, rimuoviamo la traduzione di Google e ricarichiamo
        removeCookies();
        setCookie('googtrans', '/it/it', 1);
        
        setTimeout(() => {
            // Nascondi l'overlay prima del reload per un'esperienza più fluida
            hideTranslationOverlay();
            location.reload();
        }, 500);
    } else {
        // Per altre lingue, applica la traduzione di Google
        setCookie('googtrans', '/it/' + lang, 1);
        
        // Trova e usa il selettore di Google Translate
        setTimeout(() => {
            const selectElement = document.querySelector('.goog-te-combo');
            if (selectElement) {
                selectElement.value = lang;
                selectElement.dispatchEvent(new Event('change'));
                
                // Rimuovi l'overlay dopo un breve ritardo
                setTimeout(() => {
                    hideTranslationOverlay();
                    translationInProgress = false;
                }, 1200); // Attendi che la traduzione si completi
            } else {
                // Se non troviamo il selettore, ricarica la pagina con il nuovo cookie impostato
                console.error("Elemento select di Google Translate non trovato");
                hideTranslationOverlay();
                location.reload();
            }
        }, 300);
    }
}

/**
 * Aggiorna lo stile degli elementi lingua nel menu
 */
function updateActiveLanguage(lang) {
    // Aggiorna opzioni del menu
    document.querySelectorAll('.language-option').forEach(option => {
        option.classList.remove('active');
    });
    
    document.querySelectorAll(`.language-option[data-lang="${lang}"]`).forEach(option => {
        option.classList.add('active');
    });
    
    // Aggiunge o rimuove indicatore sul pulsante
    document.querySelectorAll('.language-toggle').forEach(button => {
        if (lang === 'it') {
            button.classList.remove('active');
        } else {
            button.classList.add('active');
        }
    });
}

/**
 * Mostra un overlay durante la traduzione per evitare sfarfallii
 */
function showTranslationOverlay(show) {
    // Rimuovi overlay esistenti
    const existingOverlay = document.getElementById('translation-overlay');
    if (existingOverlay) {
        document.body.removeChild(existingOverlay);
    }
    
    if (show) {
        // Crea nuovo overlay con stile migliorato
        const overlay = document.createElement('div');
        overlay.id = 'translation-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.3);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
        `;
        
        // Crea un contenitore per il messaggio di traduzione
        const messageContainer = document.createElement('div');
        messageContainer.style.cssText = `
            background-color: rgba(255, 255, 255, 0.85);
            border-radius: 8px;
            padding: 15px 25px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            max-width: 90%;
            transform: translateY(20px);
            transition: transform 0.3s ease-out;
        `;
        
        // Icona di traduzione
        const icon = document.createElement('i');
        icon.className = 'fas fa-language fa-pulse';
        icon.style.cssText = `
            font-size: 1.8em;
            color: #105579;
            margin-right: 15px;
        `;
        
        // Testo del messaggio
        const message = document.createElement('span');
        message.textContent = 'Traduzione in corso...';
        message.style.cssText = `
            font-size: 1em;
            color: #333;
        `;
        
        // Assembla il contenitore
        messageContainer.appendChild(icon);
        messageContainer.appendChild(message);
        overlay.appendChild(messageContainer);
        document.body.appendChild(overlay);
        
        // Attiva l'animazione dopo un breve ritardo (microtask)
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            messageContainer.style.transform = 'translateY(0)';
        });
    }
}

/**
 * Nascondi l'overlay di traduzione con animazione
 */
function hideTranslationOverlay() {
    const overlay = document.getElementById('translation-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        
        // Trova il messageContainer e anima verso il basso
        const messageContainer = overlay.firstChild;
        if (messageContainer) {
            messageContainer.style.transform = 'translateY(20px)';
        }
        
        // Rimuovi l'overlay dopo la transizione
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
            translationInProgress = false;
        }, 300);
    }
}

/**
 * Imposta un cookie
 */
function setCookie(name, value, days) {
    const domain = window.location.hostname;
    let expires = "";
    
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    
    document.cookie = name + "=" + value + expires + "; path=/; domain=" + domain;
    document.cookie = name + "=" + value + expires + "; path=/";
}

/**
 * Rimuove tutti i cookie di Google Translate
 */
function removeCookies() {
    // Rimuovi cookie googtrans da tutti i possibili domini
    const domain = window.location.hostname;
    const domains = [domain, "." + domain];
    
    domains.forEach(function(domain) {
        setCookie('googtrans', '', -1);
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=" + domain;
    });
    
    // Rimuovi anche eventuali cookie di Google Translate nel localStorage
    try {
        localStorage.removeItem('googtrans');
    } catch(e) {
        console.log('Errore nel rimuovere googtrans dal localStorage:', e);
    }
}

/**
 * Sistema di gestione delle traduzioni e lingua
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inizializza la gestione delle lingue
    initLanguageSelector();
    
    // Applica la lingua salvata
    applyStoredLanguage();
});

// Inizializza il selettore di lingua
function initLanguageSelector() {
    const languageToggle = document.getElementById('language-toggle');
    const languageDropdown = document.querySelector('.language-dropdown');
    const languageOptions = document.querySelectorAll('.language-option');
    
    if (languageToggle) {
        // Gestisci l'apertura/chiusura del dropdown
        languageToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            languageDropdown.classList.toggle('show');
        });
        
        // Chiudi il dropdown quando si clicca altrove nella pagina
        document.addEventListener('click', function() {
            languageDropdown.classList.remove('show');
        });
        
        // Impedisci la chiusura quando si clicca sul dropdown stesso
        languageDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
    
    // Gestisci il click sulle opzioni di lingua
    languageOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('data-lang');
            setLanguage(lang);
            
            // Aggiorna la selezione attiva
            languageOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            
            // Mostra l'indicatore di lingua attiva sul toggle
            if (languageToggle) {
                if (lang !== 'it') { // Se non è italiano (lingua di default)
                    languageToggle.classList.add('active');
                } else {
                    languageToggle.classList.remove('active');
                }
            }
            
            languageDropdown.classList.remove('show');
        });
    });
}

// Imposta la lingua selezionata
function setLanguage(lang) {
    // Salva la lingua nel localStorage
    localStorage.setItem('selectedLanguage', lang);
    
    // Se si utilizza Google Translate, cambia la lingua
    if (typeof google !== 'undefined' && google.translate) {
        changeLanguageGoogleTranslate(lang);
    } else {
        // Altrimenti ricarica la pagina per applicare la nuova lingua
        window.location.reload();
    }
}

// Cambia lingua utilizzando Google Translate API
function changeLanguageGoogleTranslate(lang) {
    // Mostra l'overlay di traduzione
    showTranslationOverlay();
    
    if (lang === 'it') {
        // Per l'italiano (lingua originale) ricarica semplicemente la pagina
        window.location.reload();
        return;
    }
    
    // Ottieni il selettore della lingua di Google
    const gtCombo = document.querySelector('.goog-te-combo');
    
    if (gtCombo) {
        // Mappa i nostri codici lingua a quelli di Google Translate
        const langMap = {
            'en': 'en',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'it': 'it'
        };
        
        // Imposta la lingua
        gtCombo.value = langMap[lang] || 'it';
        
        // Trigger del cambio
        gtCombo.dispatchEvent(new Event('change'));
        
        // Nascondi l'overlay dopo un po' di tempo
        setTimeout(function() {
            hideTranslationOverlay();
        }, 2000);
    } else {
        console.error('Elemento Google Translate non trovato');
        hideTranslationOverlay();
    }
}

// Applica la lingua memorizzata
function applyStoredLanguage() {
    const savedLang = localStorage.getItem('selectedLanguage');
    if (savedLang && savedLang !== 'it') {
        // Trova e seleziona visivamente l'opzione corretta
        const option = document.querySelector(`.language-option[data-lang="${savedLang}"]`);
        if (option) {
            // Rimuovi la classe attiva da tutte le opzioni
            document.querySelectorAll('.language-option').forEach(opt => opt.classList.remove('active'));
            // Aggiungi la classe attiva all'opzione selezionata
            option.classList.add('active');
            
            // Attiva l'indicatore sul toggle
            const toggle = document.getElementById('language-toggle');
            if (toggle) {
                toggle.classList.add('active');
            }
        }
        
        // Se Google Translate è caricato, applica la traduzione
        if (typeof google !== 'undefined' && google.translate) {
            // Attendiamo che Google Translate sia completamente inizializzato
            setTimeout(function() {
                changeLanguageGoogleTranslate(savedLang);
            }, 1000);
        }
    }
}

// Mostra overlay durante la traduzione
function showTranslationOverlay() {
    let overlay = document.getElementById('translation-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'translation-overlay';
        
        const spinner = document.createElement('div');
        spinner.className = 'translation-spinner';
        
        const icon = document.createElement('i');
        icon.className = 'fas fa-language';
        
        const text = document.createElement('span');
        text.textContent = 'Traduzione in corso...';
        
        spinner.appendChild(icon);
        spinner.appendChild(text);
        overlay.appendChild(spinner);
        
        document.body.appendChild(overlay);
    }
    
    overlay.style.display = 'flex';
}

// Nascondi overlay di traduzione
function hideTranslationOverlay() {
    const overlay = document.getElementById('translation-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
            overlay.style.opacity = '1';
        }, 300);
    }
}

// Funzione di utilità per ottenere la lingua corrente
function getCurrentLanguage() {
    return localStorage.getItem('selectedLanguage') || 'it';
}
