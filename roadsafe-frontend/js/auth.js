const Auth = {
    async login(credentials) {
        try {
            const data = await API.formPost("/auth/login", {
                username: credentials.email,
                password: credentials.password
            });
            if (data.access_token && data.user && data.user.role) {
                localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, data.access_token);
                localStorage.setItem(CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));
                this.redirectUser(data.user.role);
            } else {
                throw new Error("Login response did not include a valid user.");
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
        if (!rawData) return null;
        try {
            const user = JSON.parse(rawData);
            return user && typeof user === "object" && user.role ? user : null;
        } catch (_) {
            localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_DATA);
            return null;
        }
    },

    redirectUser(role) {
        if (role === "ADMIN" || role === "MANAGER") {
            window.location.href = "/pages/admin/dashboard.html";
        } else if (role === "RESPONDER") {
            window.location.href = "/pages/worker/dashboard.html";
        } else {
            window.location.href = "/pages/customer/home.html";
        }
    },

    guardRoute() {
        const path = window.location.pathname;
        const user = this.getUser();

        // Allow public pages (login pages, index)
        const isPublic = path === "/" || path.endsWith("/index.html") || path.includes("/login.html") || path.includes("/register.html");

        if (!user && !isPublic) {
            console.warn("Unauthorized access. Redirecting to login.");
            this.logout();
            return;
        }

        if (user && !isPublic) {
            const role = user.role;
            const isAdminPath = path.includes("/pages/admin/");
            const isWorkerPath = path.includes("/pages/worker/");
            const isCustomerPath = path.includes("/pages/customer/") && !path.includes("login") && !path.includes("register");

            if (isAdminPath && role !== "ADMIN" && role !== "MANAGER") {
                this.redirectUser(role);
            } else if (isWorkerPath && role !== "RESPONDER") {
                this.redirectUser(role);
            } else if (isCustomerPath && role !== "CUSTOMER") {
                this.redirectUser(role);
            }
        }
    }
};
