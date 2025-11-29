// 1. Guardián del Login: si ya estás dentro, te manda a tu página
(function () {
    const userRole = localStorage.getItem("userRole");
    if (userRole === "gerente") {
        window.location.replace("dashboard.html");
    } else if (userRole === "cajero") {
        window.location.replace("corte.html");
    }
})();

// 2. Lógica del formulario de login
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        // Botón para cambiar texto mientras se hace login
        const btn = e.submitter || form.querySelector("button") || form.querySelector("button[type='submit']");
        const originalText = btn ? btn.innerText : "";

        if (!email || !password) {
            toastError("Por favor ingresa tu usuario y contraseña");
            return;
        }

        try {
            if (btn) {
                btn.innerText = "Entrando...";
                btn.disabled = true;
            }

            const response = await fetch(`${API_URL}/auth/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                // Error HTTP (401, 400, etc.)
                toastError(data.message || "Credenciales inválidas");
                return;
            }

            // Esperamos algo como: { token: "...", role: "GERENTE" | "CAJERO" }
            if (!data.token || !data.role) {
                toastError("Respuesta inválida del servidor de autenticación");
                return;
            }

            const roleNormalized = String(data.role).toLowerCase(); // "gerente" / "cajero"

            // Guardamos en localStorage
            localStorage.setItem("authToken", data.token);
            localStorage.setItem("userRole", roleNormalized);
            localStorage.setItem("userEmail", email);

            toastSuccess(`Bienvenido, ${email}`);

            // Redirigir según el rol
            setTimeout(() => {
                if (roleNormalized === "gerente") {
                    window.location.href = "dashboard.html";
                } else {
                    window.location.href = "corte.html";
                }
            }, 800);
        } catch (error) {
            console.error(error);
            toastError("No se pudo conectar con el servidor");
        } finally {
            if (btn) {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        }
    });
});
