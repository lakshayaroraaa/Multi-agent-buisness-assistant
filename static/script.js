document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('message-input');
    const messagesContainer = document.getElementById('chat-messages');
    
    // Generate a random session ID for this window
    const sessionId = 'session-' + Math.random().toString(36).substr(2, 9);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = input.value.trim();
        if (!message) return;

        // 1. Add User Message to UI
        addMessage(message, 'user');
        input.value = '';

        // 2. Add Loading Indicator
        const typingId = addTypingIndicator();

        try {
            // 3. Send to Backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: message
                })
            });

            const data = await response.json();

            // 4. Remove Loading Indicator
            removeElement(typingId);

            // 5. Add Assistant Response to UI
            // Simple markdown-to-html for bolding and newlines
            let htmlContent = data.response
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
                
            addMessage(htmlContent, 'assistant', true);

        } catch (error) {
            removeElement(typingId);
            addMessage("Sorry, I encountered an error connecting to the server.", 'assistant');
        }
    });

    function addMessage(content, sender, isHtml = false) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isHtml) {
            contentDiv.innerHTML = content;
        } else {
            contentDiv.textContent = content;
        }
        
        div.appendChild(contentDiv);
        messagesContainer.appendChild(div);
        scrollToBottom();
    }

    function addTypingIndicator() {
        const id = 'typing-' + Date.now();
        const div = document.createElement('div');
        div.className = 'message assistant typing-container';
        div.id = id;
        
        div.innerHTML = `
            <div class="typing-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        
        messagesContainer.appendChild(div);
        scrollToBottom();
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) {
            el.remove();
        }
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});
