const CONFIG = {
    // A host page may define window.ROADSAFE_CONFIG before this script to override these values.
    API_BASE_URL: window.ROADSAFE_CONFIG?.API_BASE_URL || "http://localhost:8000/api/v1",
    WS_BASE_URL: window.ROADSAFE_CONFIG?.WS_BASE_URL || "ws://localhost:8000/ws",
    STORAGE_KEYS: {
        AUTH_TOKEN: "rs_token",
        USER_DATA: "rs_user",
        OFFLINE_QUEUE: "rs_offline_queue",
        ACTIVE_TICKET_ID: "rs_active_ticket_id"
    }
};
