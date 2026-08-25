const OfflineManager = {
    init() {
        window.addEventListener('online', () => this.syncQueue());
    },

    queueRequest(endpoint, options) {
        const queue = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.OFFLINE_QUEUE) || "[]");
        queue.push({ endpoint, options, timestamp: new Date().toISOString() });
        localStorage.setItem(CONFIG.STORAGE_KEYS.OFFLINE_QUEUE, JSON.stringify(queue));
        alert("You are offline. Request cached locally and will sync when reconnected.");
    },

    async syncQueue() {
        const queue = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.OFFLINE_QUEUE) || "[]");
        if (queue.length === 0) return;

        for (const req of queue) {
            try {
                await fetch(`${CONFIG.API_BASE_URL}${req.endpoint}`, req.options);
            } catch (err) {
                console.error("Failed sync attempt", err);
                return;
            }
        }
        localStorage.removeItem(CONFIG.STORAGE_KEYS.OFFLINE_QUEUE);
        alert("Offline transactions synchronized successfully!");
    }
};

OfflineManager.init();