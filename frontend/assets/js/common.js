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

// Adaptador para el código viejo que usa showToast(mensaje, tipo)
function showToast(msg, type = "info") {
  switch (type) {
    case "success":
      toastSuccess(msg);
      break;
    case "error":
      toastError(msg);
      break;
    default:
      toastInfo(msg);
  }
}

// Formatear moneda (lo usa dashboard/corte)
function formatCurrency(number) {
  return parseFloat(number).toLocaleString("es-MX", {
    style: "currency",
    currency: "MXN",
  });
}

// URL base de la API en AWS (API Gateway HTTP)
const API_URL = "https://v7fgupxkyh.execute-api.us-east-2.amazonaws.com";