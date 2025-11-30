// 1. GUARDIÁN DE SEGURIDAD (Verificar si está logueado y rol)
(function () {
    const userRole = localStorage.getItem('userRole');

    // Si no hay rol, expulsar al login
    if (!userRole) {
        window.location.replace('index.html');
        return;
    }

    // Si es gerente y entra directo a corte.html, mándalo a su dashboard
    if (userRole === 'gerente') {
        window.location.replace('dashboard.html');
        return;
    }
    // Si es cajero, se queda aquí en corte.html
})();

document.addEventListener("DOMContentLoaded", () => {
    const $ = (id) => document.getElementById(id);

    // ==========================================
    // 1) LOGOUT (CERRAR SESIÓN)
    // ==========================================
    const logoutBtn = $("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.clear();               // Borramos token, rol, email, etc.
            window.location.href = "index.html"; // Volvemos al login
        });
    }

    // ==========================================
    // 2) DATOS DEL USUARIO (CAJERO ACTUAL)
    // ==========================================
    let currentUserId = null;
    let currentUserEmail = localStorage.getItem('userEmail') || "";
    let currentUserName = localStorage.getItem('userNombre') || currentUserEmail || "Cajero";

    const sidebarName = $("cajero-nombre");        // nombre en el lateral
    const avatar = $("cajero-avatar");             // circulito con iniciales

    function actualizarUIUsuario(nombre) {
        const nombreLimpio = nombre || "Cajero";

        // nombre en el sidebar
        if (sidebarName) {
            sidebarName.textContent = nombreLimpio;
        }

        // iniciales en el avatar
        if (avatar) {
            const iniciales = nombreLimpio
                .trim()
                .split(/\s+/)
                .map(p => p[0])
                .join('')
                .slice(0, 2)
                .toUpperCase();
            avatar.textContent = iniciales || "CC";
        }
    }

    // Pintar lo que haya en localStorage de inicio
    actualizarUIUsuario(currentUserName);

    // Obtener usuario actual desde /usuarios usando el email
    async function cargarUsuarioActual() {
        if (!currentUserEmail) {
            showToast("No se encontró el email de la sesión", "error");
            return;
        }

        try {
            const res = await fetch(`${API_URL}/usuarios`);
            const data = await res.json();
            const usuarios = Array.isArray(data) ? data : (data.usuarios || []);

            const user = usuarios.find(u => u.email === currentUserEmail);
            if (!user) {
                showToast("No se encontró el usuario en la base de datos", "error");
                return;
            }

            currentUserId = user.id;
            currentUserName = user.nombre || currentUserEmail;

            localStorage.setItem('userNombre', currentUserName);
            actualizarUIUsuario(currentUserName);
        } catch (e) {
            console.error(e);
            showToast("Error al obtener datos del cajero", "error");
        }
    }

    cargarUsuarioActual();

    // ==========================================
    // 3) FECHA ACTUAL POR DEFECTO
    // ==========================================
    const fechaInput = $("fecha");
    if (fechaInput && !fechaInput.value) {
        fechaInput.valueAsDate = new Date();
    }

    // ==========================================
    // 4) CÁLCULO DE NETO EN TIEMPO REAL
    // ==========================================
    function parseAmount(input) {
        if (!input) return 0;
        const value = parseFloat(String(input.value).replace(',', '.'));
        return isNaN(value) ? 0 : value;
    }

    function evitarNegativos(input) {
        input.addEventListener("input", () => {
            if (parseFloat(input.value) < 0) {
                input.value = 0;
            }
        });
    }

    // Aplicar a todos los campos numéricos
    ["fondoInicial", "ventasEfectivo", "ventasTarjeta", "gastos"].forEach(id => {
        const inp = document.getElementById(id);
        if (inp) evitarNegativos(inp);
    });


    function updateNeto() {
        const fondo = parseAmount($("fondoInicial"));
        const ventasEf = parseAmount($("ventasEfectivo"));
        const ventasTar = parseAmount($("ventasTarjeta"));
        const gastos = parseAmount($("gastos"));

        const neto = fondo + ventasEf + ventasTar - gastos;
        const netoEl = $("neto");
        if (netoEl) {
            netoEl.textContent = formatCurrency(neto);
        }
    }

    ["fondoInicial", "ventasEfectivo", "ventasTarjeta", "gastos"].forEach(id => {
        const input = $(id);
        if (input) {
            input.addEventListener("input", updateNeto);
        }
    });

    updateNeto();

    // ==========================================
    // 5) BOTÓN LIMPIAR
    // ==========================================
    const limpiarBtn = $("limpiarBtn");
    if (limpiarBtn) {
        limpiarBtn.addEventListener("click", () => {
            const form = $("corteForm");
            if (form) form.reset();
            if (fechaInput) fechaInput.valueAsDate = new Date();
            updateNeto();
        });
    }

    // ==========================================
    // 6) GUARDAR CORTE (POST /guardar-corte)
    // ==========================================
    const form = $("corteForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!currentUserId) {
            showToast("No se encontró el usuario de sesión. Intenta recargar la página.", "error");
            return;
        }

        const btn = form.querySelector("button.btn-primary") || form.querySelector("button[type='submit']");
        const originalText = btn ? btn.innerText : "";

        const body = {
            usuario_id: currentUserId,
            turno: $("turno") ? $("turno").value : null,
            fondoInicial: parseAmount($("fondoInicial")),
            ventasEfectivo: parseAmount($("ventasEfectivo")),
            ventasTarjeta: parseAmount($("ventasTarjeta")),
            gastos: parseAmount($("gastos")),
            observaciones: $("obs") ? $("obs").value : ""
        };

        try {
            if (btn) {
                btn.disabled = true;
                btn.innerText = "Guardando...";
            }

            const response = await fetch(`${API_URL}/guardar-corte`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            });

            const data = await response.json().catch(() => ({}));

            if (response.ok) {
                showToast("Corte guardado correctamente", "success");
                form.reset();
                if (fechaInput) fechaInput.valueAsDate = new Date();
                updateNeto();
                console.log("Corte guardado:", data);
            } else {
                showToast(data.message || data.error || "No se pudo guardar el corte", "error");
            }
        } catch (error) {
            console.error(error);
            showToast("Error de conexión con el servidor", "error");
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerText = originalText;
            }
        }
    });
});