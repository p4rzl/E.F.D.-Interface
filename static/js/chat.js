/**
 * Chat avanzata con messaggi privati, gruppi e notifiche
 */
document.addEventListener('DOMContentLoaded', function() {
    // Socket.io
    const socket = io();
    
    // Elementi DOM principali
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('chat-messages');
    const chatTabs = document.querySelectorAll('.chat-tab');
    const chatContents = document.querySelectorAll('.chat-content');
    const usersList = document.getElementById('users-list');
    const groupsList = document.getElementById('groups-list');
    const searchInput = document.getElementById('user-search');
    const newGroupBtn = document.getElementById('new-group-btn');
    const newPrivateBtn = document.getElementById('new-private-btn');
    
    // Modali e form
    const newGroupModal = document.getElementById('new-group-modal');
    const newPrivateModal = document.getElementById('new-private-modal');
    const groupForm = document.getElementById('group-form');
    const privateMessageForm = document.getElementById('private-message-form');
    
    // Ottieni il nome utente corrente e ID dal template
    const currentUser = document.querySelector('meta[name="current-user"]')?.content;
    const currentUserId = parseInt(document.querySelector('meta[name="current-user-id"]')?.content);
    
    // Stato della chat
    let currentChatType = 'general'; // 'general', 'private', 'group'
    let currentRecipientId = null;
    let currentGroupId = null;
    let unreadMessages = {
        general: 0,
        private: {},
        group: {}
    };
    
    // Richiedi permesso per le notifiche
    requestNotificationPermission();
    
    // --- Event Listeners ---
    
    // Tab switching
    chatTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabType = tab.dataset.tab;
            
            // Aggiorna tab attivo
            chatTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Aggiorna contenuto attivo
            chatContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabType}-chat`) {
                    content.classList.add('active');
                }
            });
            
            // Aggiorna lo stato corrente
            currentChatType = tabType;
            
            // Resetta i contatori di messaggi non letti
            if (tabType === 'general') {
                unreadMessages.general = 0;
                updateUnreadBadge('general');
            }
            
            // Scorre verso il basso nella chat attiva
            scrollToBottom();
        });
    });
    
    // Ricerca utenti
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const userItems = usersList.querySelectorAll('.user-item');
            
            userItems.forEach(item => {
                const username = item.querySelector('.user-name').textContent.toLowerCase();
                if (username.includes(searchTerm)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Gestione invio messaggi generali
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        
        if (message) {
            // Invia in base al tipo di chat corrente
            if (currentChatType === 'general') {
                socket.emit('message', { message: message });
            } else if (currentChatType === 'private' && currentRecipientId) {
                socket.emit('private_message', { 
                    message: message,
                    recipient_id: currentRecipientId 
                });
            } else if (currentChatType === 'group' && currentGroupId) {
                socket.emit('group_message', { 
                    message: message,
                    group_id: currentGroupId 
                });
            }
            
            messageInput.value = '';
            messageInput.focus();
        }
    });
    
    // Apertura modali
    if (newGroupBtn) {
        newGroupBtn.addEventListener('click', () => {
            newGroupModal.classList.add('active');
        });
    }
    
    if (newPrivateBtn) {
        newPrivateBtn.addEventListener('click', () => {
            newPrivateModal.classList.add('active');
        });
    }
    
    // Chiusura modali
    document.querySelectorAll('.chat-modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chat-modal').forEach(modal => {
                modal.classList.remove('active');
            });
        });
    });
    
    // Click fuori per chiudere i modali
    document.querySelectorAll('.chat-modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Creazione nuovo gruppo
    if (groupForm) {
        groupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const groupName = document.getElementById('group-name').value.trim();
            const groupDescription = document.getElementById('group-description').value.trim();
            const selectedMembers = Array.from(document.querySelectorAll('#member-selection input:checked'))
                .map(input => parseInt(input.value));
            
            if (groupName && selectedMembers.length > 0) {
                socket.emit('create_group', {
                    name: groupName,
                    description: groupDescription,
                    members: selectedMembers
                });
                
                // Nascondi il modale
                newGroupModal.classList.remove('active');
                
                // Reset form
                groupForm.reset();
            }
        });
    }
    
    // Invio messaggio privato dal modale
    if (privateMessageForm) {
        privateMessageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const recipientId = document.getElementById('recipient-select').value;
            const messageText = document.getElementById('private-message-text').value.trim();
            
            if (recipientId && messageText) {
                socket.emit('private_message', {
                    message: messageText,
                    recipient_id: parseInt(recipientId)
                });
                
                // Nascondi il modale
                newPrivateModal.classList.remove('active');
                
                // Reset form
                privateMessageForm.reset();
            }
        });
    }
    
    // Click su un utente per avviare una chat privata
    document.addEventListener('click', function(e) {
        // Delegazione eventi per chat private
        if (e.target.closest('.user-item')) {
            const userItem = e.target.closest('.user-item');
            const userId = userItem.dataset.userId;
            const username = userItem.querySelector('.user-name').textContent;
            
            if (userId) {
                // Switcha alla tab privata
                document.querySelector('.chat-tab[data-tab="private"]').click();
                
                // Carica la chat con questo utente
                loadPrivateChat(userId, username);
            }
        }
        
        // Delegazione eventi per chat di gruppo
        if (e.target.closest('.group-item')) {
            const groupItem = e.target.closest('.group-item');
            const groupId = groupItem.dataset.groupId;
            const groupName = groupItem.querySelector('.group-name').textContent;
            
            if (groupId) {
                // Switcha alla tab gruppo
                document.querySelector('.chat-tab[data-tab="group"]').click();
                
                // Carica la chat del gruppo
                loadGroupChat(groupId, groupName);
            }
        }
    });
    
    // --- Socket.io event handlers ---
    
    // Connessione
    socket.on('connect', function() {
        console.log('Connesso al server');
        addSystemMessage('Connesso alla chat');
    });
    
    // Disconnessione
    socket.on('disconnect', function() {
        console.log('Disconnesso dal server');
        addSystemMessage('Disconnesso dalla chat. Riconnessione in corso...');
    });
    
    // Messaggi generali ricevuti
    socket.on('message', function(data) {
        // Controlla che non sia un duplicato
        if (document.getElementById(data.id)) {
            return;
        }
        
        // Determina se è un messaggio proprio
        const isOwnMessage = data.is_own || data.user === currentUser;
        
        // Aggiungi il messaggio alla chat
        addMessageToChat('general', data, isOwnMessage);
        
        // Aggiorna il contatore di messaggi non letti se non siamo nella tab generale
        if (currentChatType !== 'general') {
            unreadMessages.general++;
            updateUnreadBadge('general');
            
            // Mostra notifica
            if (!isOwnMessage) {
                showNotification('Nuovo messaggio', `${data.user}: ${data.message}`);
            }
        }
        
        // Scorrimento automatico se siamo in fondo
        if (isNearBottom()) {
            scrollToBottom();
        }
    });
    
    // Messaggi privati ricevuti
    socket.on('private_message', function(data) {
        // Controlla che non sia un duplicato
        if (document.getElementById(data.id)) {
            return;
        }
        
        // Determina se è un messaggio proprio
        const isOwnMessage = data.is_own || data.sender_id === currentUserId;
        const chatId = isOwnMessage ? data.recipient_id : data.sender_id;
        
        // Aggiungi il messaggio alla chat privata
        addMessageToChat(`private-${chatId}`, data, isOwnMessage);
        
        // Se non è un proprio messaggio e non siamo nella chat con questo utente, incrementa contatore
        if (!isOwnMessage && (currentChatType !== 'private' || currentRecipientId != chatId)) {
            if (!unreadMessages.private[chatId]) {
                unreadMessages.private[chatId] = 0;
            }
            unreadMessages.private[chatId]++;
            
            // Aggiorna il badge per la tab privata in generale
            updatePrivateUnreadBadge();
            
            // Aggiorna il badge per questo specifico utente
            updateUserUnreadBadge(chatId, unreadMessages.private[chatId]);
            
            // Mostra notifica
            showNotification('Messaggio privato', `${data.sender_name}: ${data.message}`);
        }
        
        // Scorrimento automatico se siamo in fondo e nella chat corretta
        if (isNearBottom() && currentChatType === 'private' && currentRecipientId == chatId) {
            scrollToBottom();
        }
    });
    
    // Messaggi di gruppo ricevuti
    socket.on('group_message', function(data) {
        // Controlla che non sia un duplicato
        if (document.getElementById(data.id)) {
            return;
        }
        
        // Determina se è un messaggio proprio
        const isOwnMessage = data.is_own || data.sender_id === currentUserId;
        const groupId = data.group_id;
        
        // Aggiungi il messaggio alla chat di gruppo
        addMessageToChat(`group-${groupId}`, data, isOwnMessage);
        
        // Se non siamo nella chat di questo gruppo, incrementa contatore
        if (currentChatType !== 'group' || currentGroupId != groupId) {
            if (!unreadMessages.group[groupId]) {
                unreadMessages.group[groupId] = 0;
            }
            unreadMessages.group[groupId]++;
            
            // Aggiorna il badge per la tab gruppi in generale
            updateGroupUnreadBadge();
            
            // Aggiorna il badge per questo specifico gruppo
            updateGroupItemBadge(groupId, unreadMessages.group[groupId]);
            
            // Mostra notifica
            if (!isOwnMessage) {
                showNotification(`${data.group_name}`, `${data.sender_name}: ${data.message}`);
            }
        }
        
        // Scorrimento automatico se siamo in fondo e nella chat corretta
        if (isNearBottom() && currentChatType === 'group' && currentGroupId == groupId) {
            scrollToBottom();
        }
    });
    
    // Aggiornamento stato utenti (online/offline)
    socket.on('user_status', function(data) {
        updateUserStatus(data.username, data.status);
    });
    
    // Creazione nuovo gruppo
    socket.on('group_created', function(data) {
        // Aggiorna la lista dei gruppi
        addGroupToList(data);
        
        // Notifica l'utente
        showNotification('Nuovo gruppo', `Il gruppo "${data.name}" è stato creato`);
    });

    // Invito al gruppo
    socket.on('group_invitation', function(data) {
        // Notifica l'utente
        showNotification('Invito al gruppo', `Sei stato aggiunto al gruppo "${data.group_name}"`);
        
        // Aggiorna la lista gruppi
        addGroupToList(data.group);
    });
    
    // --- Funzioni di utilità ---
    
    /**
     * Aggiunge un messaggio alla chat specificata
     * @param {string} chatType - Tipo di chat ('general', 'private-{id}', 'group-{id}')
     * @param {object} data - Dati del messaggio
     * @param {boolean} isOwnMessage - Indica se è un messaggio inviato dall'utente corrente
     */
    function addMessageToChat(chatType, data, isOwnMessage) {
        // Crea l'elemento del messaggio
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isOwnMessage ? 'message-own' : ''}`;
        
        if (chatType.startsWith('private-')) {
            messageDiv.classList.add('message-private');
        } else if (chatType.startsWith('group-')) {
            messageDiv.classList.add('message-group');
        }
        
        messageDiv.id = data.id;
        
        // Prepara l'HTML del messaggio
        let messageHTML = `
            <div class="message-avatar">
                <img src="/static/img/avatars/${data.avatar_id}.png" alt="Avatar">
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span translate="no" class="message-username">${data.user || data.sender_name}</span>
                    <span class="message-time">${data.time}</span>
                </div>
                <div class="message-text">
                    ${data.message}
                </div>
            </div>
        `;
        
        // Aggiungi opzioni per i messaggi
        if (isOwnMessage) {
            messageHTML += `
                <div class="message-options">
                    <button class="message-option-btn" title="Opzioni" onclick="showMessageOptions('${data.id}')">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageHTML;
        
        // Trova o crea il contenitore per questo tipo di chat
        let container;
        
        // Per chat generale
        if (chatType === 'general') {
            container = document.getElementById('general-messages');
            if (!container) {
                container = document.createElement('div');
                container.id = 'general-messages';
                document.getElementById('general-chat').appendChild(container);
            }
        }
        // Per chat privata
        else if (chatType.startsWith('private-')) {
            const userId = chatType.split('-')[1];
            container = document.getElementById(`private-messages-${userId}`);
            if (!container) {
                container = document.createElement('div');
                container.id = `private-messages-${userId}`;
                container.className = 'private-messages';
                
                // Trova o crea il contenitore per chat privata
                let privateChat = document.getElementById('private-chat');
                if (!privateChat) {
                    privateChat = document.createElement('div');
                    privateChat.id = 'private-chat';
                    privateChat.className = 'chat-content';
                    document.getElementById('chat-contents').appendChild(privateChat);
                }
                
                privateChat.appendChild(container);
            }
        }
        // Per chat di gruppo
        else if (chatType.startsWith('group-')) {
            const groupId = chatType.split('-')[1];
            container = document.getElementById(`group-messages-${groupId}`);
            if (!container) {
                container = document.createElement('div');
                container.id = `group-messages-${groupId}`;
                container.className = 'group-messages';
                
                // Trova o crea il contenitore per chat di gruppo
                let groupChat = document.getElementById('group-chat');
                if (!groupChat) {
                    groupChat = document.createElement('div');
                    groupChat.id = 'group-chat';
                    groupChat.className = 'chat-content';
                    document.getElementById('chat-contents').appendChild(groupChat);
                }
                
                groupChat.appendChild(container);
            }
        }
        
        // Aggiungi il messaggio al contenitore
        if (container) {
            container.appendChild(messageDiv);
        }
    }
    
    /**
     * Aggiunge un messaggio di sistema alla chat
     * @param {string} message - Il messaggio di sistema da mostrare
     */
    function addSystemMessage(message) {
        const systemMessageDiv = document.createElement('div');
        systemMessageDiv.className = 'system-message';
        systemMessageDiv.textContent = message;
        
        // Aggiungi alla chat attiva
        let activeChat = document.querySelector('.chat-content.active');
        if (activeChat) {
            activeChat.appendChild(systemMessageDiv);
            scrollToBottom();
        } else {
            // Fallback alla chat generale
            let generalChat = document.getElementById('general-chat');
            if (generalChat) {
                generalChat.appendChild(systemMessageDiv);
                scrollToBottom();
            }
        }
    }
    
    /**
     * Aggiorna il badge dei messaggi non letti per una tab
     * @param {string} tabType - Tipo di tab ('general', 'private', 'group')
     */
    function updateUnreadBadge(tabType) {
        const badge = document.querySelector(`.chat-tab[data-tab="${tabType}"] .chat-tab-counter`);
        
        if (!badge) {
            // Crea il badge se non esiste
            const tab = document.querySelector(`.chat-tab[data-tab="${tabType}"]`);
            if (tab && unreadMessages[tabType] > 0) {
                const newBadge = document.createElement('span');
                newBadge.className = 'chat-tab-counter';
                newBadge.textContent = unreadMessages[tabType];
                tab.appendChild(newBadge);
            }
            return;
        }
        
        // Aggiorna il badge esistente
        if (unreadMessages[tabType] > 0) {
            badge.textContent = unreadMessages[tabType];
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }
    
    /**
     * Aggiorna il badge dei messaggi privati non letti
     */
    function updatePrivateUnreadBadge() {
        const totalUnread = Object.values(unreadMessages.private).reduce((sum, count) => sum + count, 0);
        unreadMessages.private._total = totalUnread;
        updateUnreadBadge('private');
    }
    
    /**
     * Aggiorna il badge dei messaggi di gruppo non letti
     */
    function updateGroupUnreadBadge() {
        const totalUnread = Object.values(unreadMessages.group).reduce((sum, count) => sum + count, 0);
        unreadMessages.group._total = totalUnread;
        updateUnreadBadge('group');
    }
    
    /**
     * Aggiorna il badge di un utente specifico
     * @param {number} userId - ID dell'utente
     * @param {number} count - Numero di messaggi non letti
     */
    function updateUserUnreadBadge(userId, count) {
        const userItem = document.querySelector(`.user-item[data-user-id="${userId}"]`);
        if (!userItem) return;
        
        let badge = userItem.querySelector('.badge-notification');
        
        if (!badge && count > 0) {
            // Crea badge se non esiste
            badge = document.createElement('span');
            badge.className = 'badge-notification';
            userItem.appendChild(badge);
        }
        
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    /**
     * Aggiorna il badge di un gruppo specifico
     * @param {number} groupId - ID del gruppo
     * @param {number} count - Numero di messaggi non letti
     */
    function updateGroupItemBadge(groupId, count) {
        const groupItem = document.querySelector(`.group-item[data-group-id="${groupId}"]`);
        if (!groupItem) return;
        
        let badge = groupItem.querySelector('.badge-notification');
        
        if (!badge && count > 0) {
            // Crea badge se non esiste
            badge = document.createElement('span');
            badge.className = 'badge-notification';
            groupItem.appendChild(badge);
        }
        
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    /**
     * Mostra una notifica browser
     * @param {string} title - Titolo della notifica
     * @param {string} message - Messaggio della notifica
     */
    function showNotification(title, message) {
        // Verifica se il documento è in focus
        if (document.hasFocus()) {
            // Se l'utente è già nella pagina, usa una notifica interna
            showInAppNotification(title, message);
            return;
        }
        
        // Verifica se le notifiche sono supportate e autorizzate
        if (Notification && Notification.permission === 'granted') {
            const notification = new Notification(title, {
                body: message,
                icon: '/static/img/logo.png'
            });
            
            // Porta focus alla pagina quando si clicca la notifica
            notification.onclick = function() {
                window.focus();
                notification.close();
            };
            
            // Chiudi automaticamente dopo 5 secondi
            setTimeout(() => notification.close(), 5000);
            
            // Riproduci suono
            playNotificationSound();
        } 
        else if (Notification && Notification.permission !== 'denied') {
            // Richiedi permesso
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    showNotification(title, message);
                }
            });
        }
    }
    
    /**
     * Mostra una notifica all'interno dell'app
     * @param {string} title - Titolo della notifica
     * @param {string} message - Messaggio della notifica
     */
    function showInAppNotification(title, message) {
        // Crea elemento notifica
        const notification = document.createElement('div');
        notification.className = 'in-app-notification';
        notification.innerHTML = `
            <div class="notification-header">
                <strong>${title}</strong>
                <button class="notification-close">&times;</button>
            </div>
            <div class="notification-body">${message}</div>
        `;
        
        // Aggiungi al DOM
        const container = document.getElementById('notifications-container') || document.body;
        container.appendChild(notification);
        
        // Mostra con animazione
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Aggiungi listener per chiusura
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });
        
        // Auto-chiusura dopo 5 secondi
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
        
        // Riproduci suono
        playNotificationSound();
    }
    
    /**
     * Richiedi permesso per le notifiche
     */
    function requestNotificationPermission() {
        if ('Notification' in window) {
            if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
                Notification.requestPermission();
            }
        }
    }
    
    /**
     * Riproduci suono di notifica
     */
    function playNotificationSound() {
        try {
            const sound = new Audio('/static/audio/notification.mp3');
            sound.volume = 0.5;
            sound.play().catch(e => console.log('Errore nella riproduzione del suono:', e));
        } catch (error) {
            console.log('Errore nel caricamento del suono:', error);
        }
    }
    
    /**
     * Verifica se la visualizzazione è vicina al fondo della chat
     * @returns {boolean} - True se la visualizzazione è vicina al fondo
     */
    function isNearBottom() {
        const container = document.querySelector('.chat-content.active');
        if (!container) return true;
        
        const threshold = 100;
        return container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
    }
    
    /**
     * Scrolla al fondo della chat attiva
     */
    function scrollToBottom() {
        const container = document.querySelector('.chat-content.active');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    /**
     * Carica i messaggi di una chat privata
     * @param {number} userId - ID dell'utente con cui chattare
     * @param {string} username - Nome dell'utente
     */
    function loadPrivateChat(userId, username) {
        currentRecipientId = userId;
        
        // Aggiorna intestazione
        const chatHeader = document.querySelector('.chat-title');
        if (chatHeader) {
            chatHeader.innerHTML = `
                <i class="fas fa-user"></i>
                Chat con <span translate="no">${username}</span>
            `;
        }
        
        // Carica i messaggi precedenti
        socket.emit('load_private_chat', { user_id: userId });
        
        // Reset contatore messaggi non letti
        if (unreadMessages.private[userId]) {
            unreadMessages.private[userId] = 0;
            updateUserUnreadBadge(userId, 0);
            updatePrivateUnreadBadge();
        }
        
        // Mostra il contenitore messaggi corretto
        document.querySelectorAll('.private-messages').forEach(el => {
            el.style.display = 'none';
        });
        
        const messagesContainer = document.getElementById(`private-messages-${userId}`);
        if (messagesContainer) {
            messagesContainer.style.display = 'block';
            setTimeout(() => scrollToBottom(), 100);
        }
    }
    
    /**
     * Carica i messaggi di un gruppo
     * @param {number} groupId - ID del gruppo
     * @param {string} groupName - Nome del gruppo
     */
    function loadGroupChat(groupId, groupName) {
        currentGroupId = groupId;
        
        // Aggiorna intestazione
        const chatHeader = document.querySelector('.chat-title');
        if (chatHeader) {
            chatHeader.innerHTML = `
                <i class="fas fa-users"></i>
                ${groupName}
            `;
        }
        
        // Carica i messaggi precedenti
        socket.emit('load_group_chat', { group_id: groupId });
        
        // Reset contatore messaggi non letti
        if (unreadMessages.group[groupId]) {
            unreadMessages.group[groupId] = 0;
            updateGroupItemBadge(groupId, 0);
            updateGroupUnreadBadge();
        }
        
        // Mostra il contenitore messaggi corretto
        document.querySelectorAll('.group-messages').forEach(el => {
            el.style.display = 'none';
        });
        
        const messagesContainer = document.getElementById(`group-messages-${groupId}`);
        if (messagesContainer) {
            messagesContainer.style.display = 'block';
            setTimeout(() => scrollToBottom(), 100);
        }
    }
    
    /**
     * Aggiorna lo stato online/offline di un utente
     * @param {string} username - Nome utente
     * @param {boolean} isOnline - Stato online (true) o offline (false)
     */
    function updateUserStatus(username, isOnline) {
        const userItems = document.querySelectorAll(`.user-item[data-username="${username}"]`);
        
        userItems.forEach(userItem => {
            // Aggiorna classe CSS
            userItem.classList.toggle('online', isOnline);
            userItem.classList.toggle('offline', !isOnline);
            
            // Aggiorna indicatore di stato
            const indicator = userItem.querySelector('.user-status-indicator');
            if (indicator) {
                indicator.classList.toggle('user-status-online', isOnline);
                indicator.classList.toggle('user-status-offline', !isOnline);
            }
            
            // Sposta l'
        });
    }
    
    /**
     * Aggiunge un gruppo alla lista dei gruppi
     * @param {object} group - Dati del gruppo
     */
    function addGroupToList(group) {
        const groupItem = document.createElement('div');
        groupItem.className = 'group-item';
        groupItem.dataset.groupId = group.id;
        groupItem.innerHTML = `
            <span class="group-name">${group.name}</span>
            <span class="unread-badge"></span>
        `;
        groupsList.appendChild(groupItem);
    }
});
