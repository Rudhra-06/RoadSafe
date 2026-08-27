const UI = {
  escape(value = "") { const node = document.createElement("span"); node.textContent = value; return node.innerHTML; },
  icon(name) { const paths = { wrench: "M14.7 6.3a4 4 0 0 1-5 5L3 18l3 3 6.7-6.7a4 4 0 0 1 5-5l-3 3-2-2 3-3z", map: "M9 18l-6 3V6l6-3 6 3 6-3v15l-6 3-6-3zM9 3v15m6-12v15", clock: "M12 6v6l4 2", check: "m5 12 4 4L19 6", car: "M5 17h14l-1-6H6l-1 6zm2 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm10 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4z", user: "M20 21a8 8 0 0 0-16 0m8-10a4 4 0 1 0 0-8 4 4 0 0 0 0 8", bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9m-8 13h4", logout: "M10 17l5-5-5-5m5 5H3m12-8h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4", phone: "M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1.1.4 2.1.8 3.1a2 2 0 0 1-.5 2.1L8.1 10a16 16 0 0 0 6 6l1.1-1.1a2 2 0 0 1 2.1-.5c1 .4 2 .7 3.1.8a2 2 0 0 1 1.6 1.7z" };
    return `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.check}"/></svg>`; },
  statusLabel(status) { return ({ IN_SERVICE: "Service in progress", EN_ROUTE: "En route", NO_RESPONDER: "Finding provider", DISPATCHING: "Finding provider", REASSIGN: "Reassigning" })[status] || (status || "Unknown").replaceAll("_", " "); },
  statusBadge(status) { return `<span class="badge badge-${(status === 'COMPLETED' ? 'success' : ['CANCELLED','FAILED','NO_RESPONDER'].includes(status) ? 'danger' : 'info')}">${this.escape(this.statusLabel(status))}</span>`; },
  alert(target, message, type = "error") { target.innerHTML = `<div class="alert alert-${type}" role="alert">${this.escape(message)}</div>`; },
  loading(target, message = "Loading…") { target.innerHTML = `<div class="state"><div class="spinner"></div><p>${this.escape(message)}</p></div>`; }
};
