// Iconos Lucide en cada render
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();
});

// Helpers de toasts
function toastSuccess(msg) {
  Toastify({ text: msg, gravity: "top", position: "right", backgroundColor: "#16a34a" }).showToast();
}
function toastError(msg) {
  Toastify({ text: msg, gravity: "top", position: "right", backgroundColor: "#ef4444" }).showToast();
}
function toastInfo(msg) {
  Toastify({ text: msg, gravity: "top", position: "right", backgroundColor: "#0ea5e9" }).showToast();
}

// Formatear moneda (También faltaba esta función que usa dashboard.js)
function formatCurrency(number) {
    return parseFloat(number).toLocaleString('es-MX', {
        style: 'currency',
        currency: 'MXN'
    });
}

// --- ESTO ES LO QUE FALTABA ---
const API_URL = "http://127.0.0.1:5000";