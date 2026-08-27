const RoadSafeMap = {
    render(element, latitude, longitude, label = "Location") {
        if (!window.L || !CONFIG.MAP.tileUrl) {
            element.className = "map-placeholder";
            element.innerHTML = `<div><p>${label}</p><small>${Number(latitude).toFixed(5)}, ${Number(longitude).toFixed(5)}</small></div>`;
            return null;
        }
        const map = L.map(element).setView([latitude, longitude], 14);
        L.tileLayer(CONFIG.MAP.tileUrl, { attribution: CONFIG.MAP.attribution }).addTo(map);
        L.marker([latitude, longitude]).addTo(map).bindPopup(label);
        return map;
    }
};
