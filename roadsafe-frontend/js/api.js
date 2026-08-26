const API = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        const headers = {
            "Content-Type": "application/json",
            ...(token && { "Authorization": `Bearer ${token}` }),
            ...options.headers
        };

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
                ...options,
                headers
            });

            if (!response.ok) {
                if (response.status === 401) {
                    if (typeof Auth !== "undefined") Auth.logout();
                }
                const errorBody = await response.json().catch(() => ({}));
                throw new Error(errorBody.detail || `API Error: ${response.statusText}`);
            }

            return await response.json();
        } catch (err) {
            if (!navigator.onLine) {
                OfflineManager.queueRequest(endpoint, options);
                return { offline: true, message: "Action queued offline." };
            }
            throw err;
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: "GET" });
    },

    post(endpoint, body) {
        return this.request(endpoint, { method: "POST", body: JSON.stringify(body) });
    },

    formPost(endpoint, body) {
        return this.request(endpoint, {
            method: "POST",
            body: new URLSearchParams(body).toString(),
            headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });
    },

    patch(endpoint, body) {
        return this.request(endpoint, { method: "PATCH", body: JSON.stringify(body) });
    }
};
