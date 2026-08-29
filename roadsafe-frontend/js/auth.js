const Auth = {
    async login(credentials, allowedRoles = null) {
        try {
            const data = await API.formPost("/auth/login", {
                username: credentials.email,
                password: credentials.password
            });
            if (data.access_token && data.user && data.user.role) {
                const userRole = data.user.role;
                if (allowedRoles) {
                    const rolesArr = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
                    if (!rolesArr.includes(userRole)) {
                        localStorage.removeItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
                        localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_DATA);
                        let portalName = "this portal";
                        if (rolesArr.includes("RESPONDER")) portalName = "Worker portal";
                        else if (rolesArr.includes("ADMIN") || rolesArr.includes("MANAGER")) portalName = "Admin portal";
                        else if (rolesArr.includes("CUSTOMER")) portalName = "Customer portal";

                        let userRoleLabel = "Customer";
                        if (userRole === "RESPONDER") userRoleLabel = "Worker/Responder";
                        else if (userRole === "ADMIN" || userRole === "MANAGER") userRoleLabel = "Admin";

                        throw new Error(`Access denied. ${userRoleLabel} accounts cannot sign in through ${portalName}.`);
                    }
                }

                localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, data.access_token);
                localStorage.setItem(CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));
                this.redirectUser(userRole);
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
        const path = window.location.pathname;
        localStorage.removeItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_DATA);
        if (CONFIG.STORAGE_KEYS.ACTIVE_TICKET_ID) {
            localStorage.removeItem(CONFIG.STORAGE_KEYS.ACTIVE_TICKET_ID);
        }
        try {
            sessionStorage.clear();
        } catch (_) {}

        if (path.includes("/pages/worker/")) {
            window.location.href = "/pages/worker/login.html";
        } else if (path.includes("/pages/admin/")) {
            window.location.href = "/pages/admin/login.html";
        } else {
            window.location.href = "/pages/customer/login.html";
        }
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

        // Check if page is public
        const isPublic = path === "/" || path.endsWith("/index.html") || path.endsWith("/index") || path.includes("/login.html") || path.includes("/register.html");

        if (!user && !isPublic) {
            console.warn("Unauthorized access. Redirecting to login.");
            this.logout();
            return;
        }

        if (user && isPublic) {
            this.redirectUser(user.role);
            return;
        }

        if (user && !isPublic) {
            const role = user.role;
            const isAdminPath = path.includes("/pages/admin/");
            const isWorkerPath = path.includes("/pages/worker/");
            const isCustomerPath = path.includes("/pages/customer/");

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

if (typeof window !== "undefined") {
    Auth.guardRoute();
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) {
            Auth.guardRoute();
        }
    });
}

