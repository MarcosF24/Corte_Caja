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
