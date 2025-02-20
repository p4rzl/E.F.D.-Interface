document.addEventListener('DOMContentLoaded', function () {
    // Inizializza socket.io
    const socket = io();
    const chatButton = document.getElementById('chatButton');
    const chatContainer = document.getElementById('chatContainer');
    const closeChat = document.getElementById('closeChat');
    const messageInput = document.getElementById('messageInput');
    const sendMessage = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');

    // Imposta isAdmin come variabile JavaScript
    const isAdmin = document.body.dataset.isAdmin === 'true';

    // Funzione per mostrare le notifiche
    function showNotification(message, username) {
        if (!chatContainer.classList.contains('active')) {
            const notification = document.getElementById('chatNotification');
            notification.textContent = `${username}: ${message}`;
            notification.classList.add('show');
            chatButton.classList.add('new-message');

            setTimeout(() => {
                notification.classList.add('hide');
                setTimeout(() => {
                    notification.classList.remove('show', 'hide');
                    chatButton.classList.remove('new-message');
                }, 300);
            }, 5000);
        }
    }

    // Modifica la funzione addMessage per il corretto allineamento
    function addMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';

        const avatarImg = document.createElement('img');
        avatarImg.src = `/static/img/avatars/${data.avatar_id}.png`;
        avatarImg.alt = 'Avatar';
        avatarImg.className = 'message-avatar';

        const userInfoDiv = document.createElement('div');
        userInfoDiv.className = 'message-user-info';

        const usernameSpan = document.createElement('span');
        usernameSpan.className = `username ${data.isAdmin ? 'admin' : ''}`;
        usernameSpan.textContent = data.username;

        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'timestamp';
        timestampSpan.textContent = data.timestamp;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = data.message;

        userInfoDiv.appendChild(usernameSpan);
        userInfoDiv.appendChild(timestampSpan);

        const messageContentWrapper = document.createElement('div');
        messageContentWrapper.className = 'message-wrapper';
        messageContentWrapper.appendChild(userInfoDiv);
        messageContentWrapper.appendChild(contentDiv);

        messageDiv.appendChild(avatarImg);
        messageDiv.appendChild(messageContentWrapper);

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Mostra notifica se la chat è chiusa
        if (!chatContainer.classList.contains('active')) {
            showNotification(data.message, data.username);
        }
    }

    // Gestione eventi chat
    chatButton.addEventListener('click', () => {
        chatContainer.classList.toggle('active');
        if (chatContainer.classList.contains('active')) {
            loadMessages();
        }
    });

    closeChat.addEventListener('click', () => {
        chatContainer.classList.remove('active');
    });

    // Carica messaggi esistenti
    function loadMessages() {
        fetch('/get_messages')
            .then(response => response.json())
            .then(messages => {
                chatMessages.innerHTML = '';
                messages.reverse().forEach(msg => {
                    msg.isAdmin = msg.username === 'admin';
                    addMessage(msg);
                });
            });
    }

    // Gestione invio messaggi
    function sendNewMessage() {
        const message = messageInput.value.trim();
        if (message) {
            socket.emit('send_message', { message: message });
            messageInput.value = '';
        }
    }

    sendMessage.addEventListener('click', sendNewMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendNewMessage();
    });

    // Socket.io event listeners
    socket.on('connect', () => {
        console.log('Connected to socket.io');
    });

    socket.on('new_message', (data) => {
        data.isAdmin = data.username === 'admin';
        addMessage(data);
    });
});