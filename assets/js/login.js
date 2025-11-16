document.getElementById("loginForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const email = document.getElementById("email").value.toLowerCase().trim();
  const pass  = document.getElementById("password").value;

  if (!email || !pass) return toastError("Completa todos los campos");

  if (email.includes("@cajero"))  return (location.href = "corte.html");
  if (email.includes("@gerente")) return (location.href = "dashboard.html");

  toastInfo("Credenciales inválidas (usa @cajero o @gerente)");
});
