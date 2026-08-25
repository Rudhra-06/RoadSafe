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

    // Automatic Auth Redirect Check
    const currentUser = Auth.getUser();
    if (currentUser && window.location.pathname === "/index.html") {
        Auth.redirectUser(currentUser.role);
    }
})();