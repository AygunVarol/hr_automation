javascript
// WebSocket handler for real-time notifications
class WebSocketHandler {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.messageHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    // Initialize WebSocket connection
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.connected = false;
            this.handleReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        };
    }

    // Handle incoming messages
    handleMessage(data) {
        const { type, payload } = data;
        
        if (this.messageHandlers.has(type)) {
            this.messageHandlers.get(type)(payload);
        }

        // Display notification based on message type
        switch(type) {
            case 'REVIEW_REQUIRED':
                this.showNotification('New Review Required', payload.message);
                break;
            case 'ACCESS_CHANGE':
                this.showNotification('Access Change Alert', payload.message);
                break;
            case 'DECISION_PENDING':
                this.showNotification('Decision Pending', payload.message);
                break;
            case 'SYSTEM_ALERT':
                this.showNotification('System Alert', payload.message, true);
                break;
        }
    }

    // Register message handler
    on(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    // Send message to server
    send(type, data) {
        if (!this.connected) {
            console.error('WebSocket not connected');
            return;
        }

        const message = JSON.stringify({
            type,
            payload: data
        });

        this.socket.send(message);
    }

    // Handle reconnection
    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

        setTimeout(() => {
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.connect();
        }, delay);
    }

    // Show browser notification
    showNotification(title, message, urgent = false) {
        if (!("Notification" in window)) {
            console.log("Browser doesn't support notifications");
            return;
        }

        if (Notification.permission === "granted") {
            this.createNotification(title, message, urgent);
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    this.createNotification(title, message, urgent);
                }
            });
        }
    }

    // Create and display notification
    createNotification(title, message, urgent) {
        const options = {
            body: message,
            icon: '/static/img/notification-icon.png',
            tag: 'hr-notification',
            requireInteraction: urgent
        };

        const notification = new Notification(title, options);
        
        notification.onclick = function() {
            window.focus();
            notification.close();
        };
    }

    // Cleanup
    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Initialize WebSocket handler
const wsHandler = new WebSocketHandler();
wsHandler.connect();

// Export for use in other modules
export default wsHandler;
