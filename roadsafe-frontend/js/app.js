// Application Initializer & PWA Lifecycle Management
(function () {
    // Service Worker Registration
    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker
                .register("/service-worker.js")
                .then((reg) => console.log("Service Worker registered successfully:", reg.scope))
                .catch((err) => console.error("Service Worker registration failed:", err));
        });
    }

    // Automatic Auth Redirect & Route Guard
    if (typeof Auth !== 'undefined') {
        Auth.guardRoute();

        const currentUser = Auth.getUser();
        if (currentUser && (window.location.pathname.endsWith("/index.html") || window.location.pathname === "/")) {
            Auth.redirectUser(currentUser.role);
        }
    }
})();