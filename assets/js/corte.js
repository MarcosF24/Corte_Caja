const $ = (id) => document.getElementById(id);

// Toggle sidebar
const aside = $("sidebar");
const toggleIcon = $("toggleIcon");
$("toggleBtn").onclick = () => {
  if (aside.classList.contains("w-64")) {
    aside.classList.remove("w-64"); aside.classList.add("w-0","overflow-hidden");
    toggleIcon.setAttribute("data-lucide","panel-left-open"); lucide.createIcons();
  } else {
    aside.classList.remove("w-0","overflow-hidden"); aside.classList.add("w-64");
    toggleIcon.setAttribute("data-lucide","panel-left-close"); lucide.createIcons();
  }
};

// Logout
$("logoutBtn").onclick = () => location.href = "index.html";

// Neto en tiempo real
const fmt = new Intl.NumberFormat("es-MX",{ style:"currency", currency:"MXN" });
function updateNeto() {
  const efectivo = Number($("ventasEfectivo").value || 0);
  const tarjeta  = Number($("ventasTarjeta").value || 0);
  const gastos   = Number($("gastos").value || 0);
  $("neto").textContent = fmt.format(efectivo + tarjeta - gastos);
}
["ventasEfectivo","ventasTarjeta","gastos"].forEach(id => $(id).addEventListener("input", updateNeto));
updateNeto();

// Guardar (solo UI)
$("corteForm").addEventListener("submit",(e)=>{
  e.preventDefault();
  toastSuccess("Corte guardado (solo UI)");
  e.target.reset(); updateNeto();
});

// Limpiar
$("limpiarBtn").onclick = () => { $("corteForm").reset(); updateNeto(); };
