const Auth = {
    async login(credentials) {
        try {
            const data = await API.post("/auth/login", credentials);
            if (data.token) {
                localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, data.token);
                localStorage.setItem(CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));
                this.redirectUser(data.user.role);
            }
            return data;
        } catch (err) {
            console.error("Login Error:", err);
            throw err;
        }
    },

    async register(userData) {
        return await API.post("/auth/register", userData);
    },

    logout() {
        localStorage.removeItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_DATA);
        window.location.href = "/pages/customer/login.html";
    },

    getUser() {
        const rawData = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_DATA);
        return rawData ? JSON.parse(rawData) : null;
    },

    redirectUser(role) {
        switch (role) {
            case "ADMIN":
                window.location.href = "/pages/admin/dashboard.html";
                break;
            case "WORKER":
                window.location.href = "/pages/worker/dashboard.html";
                break;
            default:
                window.location.href = "/pages/customer/home.html";
        }
    }
};