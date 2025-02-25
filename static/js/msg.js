// static/js/msg.js

document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatContainer = document.getElementById('chatContainer');
    const closeChat = document.getElementById('closeChat');
    const messageInput = document.getElementById('messageInput');
    const sendMessage = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');
    
    // Socket.io per la chat in tempo reale
    let socket;
    try {
        socket = io();
    } catch (e) {
        console.error('Errore nella connessione Socket.IO:', e);
    }
    
    if (socket) {
        // Gestione connessione socket
        socket.on('connect', function() {
            console.log('Connesso al server');
        });
        
        // Ricezione messaggi
        socket.on('message', function(data) {
            appendMessage(data.user, data.message, data.avatar_id);
            
            // Notifica se la chat è chiusa
            if (chatContainer.style.display !== 'flex') {
                chatButton.classList.add('new-message');
                const notification = document.getElementById('chatNotification');
                notification.textContent = 'Nuovo messaggio!';
                notification.style.display = 'block';
                
                setTimeout(() => {
                    notification.style.display = 'none';
                }, 3000);
            }
        });
    }
    
    // Mostra/nascondi chat
    chatButton.addEventListener('click', function() {
        if (chatContainer.style.display === 'flex') {
            chatContainer.style.display = 'none';
        } else {
            chatContainer.style.display = 'flex';
            chatButton.classList.remove('new-message');
        }
    });
    
    closeChat.addEventListener('click', function() {
        chatContainer.style.display = 'none';
    });
    
    // Invio messaggi
    function sendChatMessage() {
        const message = messageInput.value.trim();
        
        if (message && socket) {
            socket.emit('message', { message: message });
            messageInput.value = '';
        }
    }
    
    sendMessage.addEventListener('click', sendChatMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
    
    // Funzione per aggiungere messaggi alla chat
    function appendMessage(user, message, avatarId) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message';
        
        messageElement.innerHTML = `
            <img src="/static/img/avatars/${avatarId}.png" alt="${user}" class="message-avatar">
            <div class="message-content">
                <div class="message-user-info">
                    <span class="message-username">${user}</span>
                    <span class="message-time">${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="message-text">${message}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});