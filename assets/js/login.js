// 1. Guardián del Login: Si ya estás dentro, te manda a tu página
(function() {
    const userRole = localStorage.getItem('userRole');
    if (userRole) {
        if (userRole === 'gerente') window.location.replace('dashboard.html');
        else window.location.replace('corte.html');
    }
})();

// 2. Lógica del Formulario
document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    // Obtener datos del formulario
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const btn = e.target.querySelector("button");

    // Validar campos vacíos
    if (!email || !password) {
        return toastError("Por favor completa todos los campos");
    }

    // Efecto de carga en el botón
    const originalText = btn.innerText;
    btn.innerText = "Verificando...";
    btn.disabled = true;

    try {
        // 3. CONEXIÓN REAL AL BACKEND (Python)
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (data.status === 'ok') {
            // 4. GUARDAR SESIÓN (Crucial para que el Auth Guard te deje pasar)
            localStorage.setItem('userNombre', data.nombre);
            localStorage.setItem('userRole', data.tipo);
            
            toastSuccess(`Bienvenido, ${data.nombre}`);
            
            // Redirigir según el rol
            setTimeout(() => {
                if (data.tipo === 'gerente') {
                    window.location.href = "dashboard.html";
                } else {
                    window.location.href = "corte.html";
                }
            }, 1000);
        } else {
            // Error de contraseña o usuario no encontrado
            toastError(data.message);
        }
    } catch (error) {
        console.error(error);
        toastError("No se pudo conectar con el servidor");
    } finally {
        // Restaurar botón
        btn.innerText = originalText;
        btn.disabled = false;
    }
});