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
    },

    calcDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    },

    async getDrivingRoute(startLng, startLat, endLng, endLat) {
        const straightDistKm = this.calcDistance(startLat, startLng, endLat, endLng);
        let roadDistKm = (straightDistKm * 1.25).toFixed(1);
        let durationMins = Math.max(2, Math.round((roadDistKm / 35) * 60));
        let latlngs = [[startLat, startLng], [endLat, endLng]];

        try {
            const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${endLng},${endLat}?overview=full&geometries=geojson`;
            const res = await fetch(osrmUrl);
            if (res.ok) {
                const data = await res.json();
                if (data.routes && data.routes.length > 0) {
                    const route = data.routes[0];
                    latlngs = route.geometry.coordinates.map(c => [c[1], c[0]]);
                    roadDistKm = (route.distance / 1000).toFixed(1);
                    durationMins = Math.max(1, Math.round(route.duration / 60));
                }
            }
        } catch (e) {
            console.warn('RoadSafeMap: OSRM route fetch fallback:', e);
        }

        const etaFormatted = durationMins < 60 ? `${durationMins} min` : `${Math.floor(durationMins/60)} hr ${durationMins%60} min`;
        return {
            latlngs,
            roadDistKm,
            durationMins,
            etaFormatted
        };
    }
};
