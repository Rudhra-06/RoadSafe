const WSManager = {
    socket: null,

    connect(channelId, onMessageCallback) {
        const url = `${CONFIG.WS_BASE_URL}/${channelId}`;
        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
            console.log(`WebSocket connected to channel: ${channelId}`);
        };

        this.socket.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                onMessageCallback(payload);
            } catch (err) {
                console.error("Failed to parse WebSocket message packet:", err);
            }
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket transport error observed:", error);
        };

        this.socket.onclose = () => {
            console.log("WebSocket stream disconnected. Reattempting connection in 3s...");
            setTimeout(() => this.connect(channelId, onMessageCallback), 3000);
        };
    },

    send(payload) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(payload));
        } else {
            console.warn("WebSocket active session unavailable. Event queued/dropped.");
        }
    }
};