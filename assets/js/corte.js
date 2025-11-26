// 1. GUARDIÁN DE SEGURIDAD (Verificar si está logueado)
(function() {
    const userRole = localStorage.getItem('userRole');
    // Si no hay rol, expulsar al login
    if (!userRole) window.location.replace('index.html');
})();

document.addEventListener("DOMContentLoaded", () => {
    // --- 1. MOSTRAR NOMBRE DEL CAJERO (NUEVO) ---
    const nombreCajero = localStorage.getItem('userNombre') || "Desconocido";
    const displayElement = document.getElementById('display-cajero');
    if (displayElement) {
        displayElement.innerText = nombreCajero;
    }
    // --- 2. LÓGICA DE UI (SIDEBAR - TU CÓDIGO ADAPTADO) ---
    const $ = (id) => document.getElementById(id);
    const aside = $("sidebar");
    const toggleIcon = $("toggleIcon");
    
    $("toggleBtn").onclick = () => {
        if (aside.classList.contains("w-64")) {
            // Ocultar
            aside.classList.remove("w-64"); 
            aside.classList.add("w-0", "overflow-hidden");
            toggleIcon.setAttribute("data-lucide", "panel-left-open"); 
        } else {
            // Mostrar
            aside.classList.remove("w-0", "overflow-hidden"); 
            aside.classList.add("w-64");
            toggleIcon.setAttribute("data-lucide", "panel-left-close"); 
        }
        lucide.createIcons();
    };

    // --- 3. LÓGICA DE NEGOCIO (CÁLCULOS) ---
    const inputs = ["fondoInicial", "ventasEfectivo", "gastos"];
    
    function updateNeto() {
        const efectivo = parseFloat($("fondoInicial").value) || 0; // Ojo: Fondo + Ventas Efectivo
        const ventas = parseFloat($("ventasEfectivo").value) || 0;
        const gastos   = parseFloat($("gastos").value) || 0;
        
        // Neto = (Fondo + Ventas Efectivo) - Gastos
        const neto = (efectivo + ventas) - gastos;
        
        // Usamos formatCurrency de common.js si existe, si no, usamos Intl local
        if (typeof formatCurrency === 'function') {
            $("neto").innerText = formatCurrency(neto);
        } else {
            const fmt = new Intl.NumberFormat("es-MX",{ style:"currency", currency:"MXN" });
            $("neto").textContent = fmt.format(neto);
        }
    }

    // Escuchar cambios para recalcular
    inputs.forEach(id => $(id).addEventListener("input", updateNeto));
    // Inicializar
    updateNeto();
    $("fecha").valueAsDate = new Date();


    // --- 4. LOGOUT REAL (Borrar sesión) ---
    $("logoutBtn").onclick = () => {
        localStorage.clear(); // ¡Importante! Borrar credenciales
        window.location.href = "index.html";
    };

    // --- 5. LIMPIAR FORMULARIO ---
    $("limpiarBtn").onclick = () => { 
        $("corteForm").reset(); 
        updateNeto(); 
        $("fecha").valueAsDate = new Date();
    };

    // --- 6. GUARDAR EN BASE DE DATOS (CONEXIÓN FLASK) ---
    $("corteForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const btn = e.target.querySelector("button[type='submit']") || e.target.querySelector(".btn-primary");
        const originalText = btn.innerText;
        btn.innerText = "Guardando...";
        btn.disabled = true;

        // Recuperar nombre del cajero
        const cajeroNombre = localStorage.getItem('userNombre') || "Desconocido";

        const formData = {
            fecha: $("fecha").value,
            turno: $("turno").value,
            fondoInicial: $("fondoInicial").value,
            ventasEfectivo: $("ventasEfectivo").value,
            ventasTarjeta: $("ventasTarjeta").value,
            gastos: $("gastos").value,
            observaciones: $("obs").value,
            // Datos automáticos
            cajero: cajeroNombre,
            hora: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
        };

        try {
            // Conexión con tu backend
            const response = await fetch(`${API_URL}/guardar-corte`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();

            if (response.ok) {
                toastSuccess(data.message); // Mensaje verde
                $("corteForm").reset();
                updateNeto();
                $("fecha").valueAsDate = new Date();
            } else {
                toastError("Error: " + data.message); // Mensaje rojo
            }
        } catch (error) {
            console.error(error);
            toastError("Error de conexión con el servidor");
        } finally {
            btn.innerText = originalText;
            btn.disabled = false;
        }
    });
});