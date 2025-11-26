(function() {
    const userRole = localStorage.getItem('userRole');
    const currentPage = window.location.pathname.split('/').pop();

    // 1. Si no hay rol, expulsar al login
    if (!userRole) {
        window.location.replace('index.html');
        return;
    }

    const role = userRole.toLowerCase(); // Convertir a minúsculas para evitar errores

    // 2. Proteger Dashboard (Solo Gerentes)
    if (currentPage.includes('dashboard.html')) {
        if (role !== 'gerente') {
            alert("Acceso denegado: Solo gerentes pueden ver esto.");
            window.location.replace('corte.html');
        }
    }

    // 3. Proteger Corte (Solo Cajeros - Opcional, si quieres que el gerente no entre aquí)
    /* if (currentPage.includes('corte.html')) {
        if (role !== 'cajero' && role !== 'gerente') {
             window.location.replace('index.html');
        }
    }
    */
})();