const CACHE_NAME = "roadsafe-v1";
const ASSETS_TO_CACHE = [
    "/",
    "/index.html",
    "/manifest.json",
    "/css/styles.css",
    "/js/config.js",
    "/js/api.js",
    "/js/auth.js",
    "/js/offline.js",
    "/js/ws.js",
    "/pages/customer/home.html",
    "/pages/customer/request.html"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    // Bypass WebSocket and non-GET requests
    if (event.request.url.startsWith("ws") || event.request.method !== "GET") {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                // Fetch background updates dynamically (Stale-While-Revalidate)
                fetch(event.request).then((networkResponse) => {
                    if (networkResponse.status === 200) {
                        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
                    }
                }).catch(() => {/* Ignore network errors offline */ });

                return cachedResponse;
            }

            return fetch(event.request).catch(() => {
                // Fallback offline UI for document requests
                if (event.request.headers.get("accept").includes("text/html")) {
                    return caches.match("/pages/customer/home.html");
                }
            });
        })
    );
});