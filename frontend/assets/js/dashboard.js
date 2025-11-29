// ==========================================
// ARCHIVO: assets/js/dashboard.js
// ==========================================

// 1. Segunda validación de seguridad (Por si el auth-guard fallara)
(function() {
    const userRole = localStorage.getItem('userRole');
    if (userRole !== 'gerente') {
        // Si es cajero, mándalo a su sitio sin preguntar
        if (userRole === 'cajero') window.location.replace('corte.html');
        // Si no es nada, al login
        else window.location.replace('index.html');
    }
})();

document.addEventListener("DOMContentLoaded", () => {
    
    // --- REFERENCIAS DOM ---
    // Navegación
    const navDash = document.getElementById('nav-dashboard');
    const navUsers = document.getElementById('nav-usuarios');
    const pageDash = document.getElementById('page-dashboard');
    const pageUsers = document.getElementById('page-usuarios');
    
    // Filtros
    const filterFecha = document.getElementById('filter-fecha');
    const filterCajero = document.getElementById('filter-cajero');

    // Modal
    const modal = document.getElementById('view-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    // --- UI: DATOS DEL USUARIO Y LOGOUT ---
    const storedName = localStorage.getItem('userNombre') || "Gerente";
    document.getElementById('gerente-nombre').innerText = storedName;
    
    // Iniciales del Avatar
    const initials = storedName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'GA';
    document.getElementById('gerente-avatar').innerText = initials;
    document.getElementById('fecha-hoy').innerText = new Date().toLocaleDateString();

    // Botón Cerrar Sesión
    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'index.html';
    });

    // --- UI: NAVEGACIÓN DE PESTAÑAS (TABS) ---
    function switchTab(active) {
        if (active === 'dash') {
            pageDash.classList.remove('hidden-section');
            pageUsers.classList.add('hidden-section');
            
            // Estilos Activos Dash
            navDash.classList.remove('text-slate-400', 'hover:bg-white/10');
            navDash.classList.add('bg-blue-600', 'text-white', 'shadow-lg');
            
            // Estilos Inactivos Users
            navUsers.classList.add('text-slate-400', 'hover:bg-white/10');
            navUsers.classList.remove('bg-blue-600', 'text-white', 'shadow-lg');
            
            cargarDashboard(); // Refrescar datos al volver
        } else {
            pageDash.classList.add('hidden-section');
            pageUsers.classList.remove('hidden-section');
            
            // Estilos Inactivos Dash
            navDash.classList.add('text-slate-400', 'hover:bg-white/10');
            navDash.classList.remove('bg-blue-600', 'text-white', 'shadow-lg');
            
            // Estilos Activos Users
            navUsers.classList.remove('text-slate-400', 'hover:bg-white/10');
            navUsers.classList.add('bg-blue-600', 'text-white', 'shadow-lg');
            
            cargarUsuarios(); // Cargar lista de usuarios
        }
    }

    navDash.addEventListener('click', () => switchTab('dash'));
    navUsers.addEventListener('click', () => switchTab('users'));


    // ==========================================
    // LÓGICA: DASHBOARD Y CORTES
    // ==========================================

    async function cargarDashboard() {
        const fecha = filterFecha.value;
        const cajero = filterCajero.value;
        
        // Construir URL con filtros
        const url = new URL(`${API_URL}/obtener-cortes`);
        if (fecha) url.searchParams.append('fecha', fecha);
        if (cajero) url.searchParams.append('cajero', cajero);

        try {
            const res = await fetch(url);
            const data = await res.json();

            // 1. Actualizar Tarjetas
            document.getElementById('card-total-ventas').innerText = formatCurrency(data.summary.total_ventas);
            document.getElementById('card-total-gastos').innerText = formatCurrency(data.summary.total_gastos);
            document.getElementById('card-neto-total').innerText = formatCurrency(data.summary.neto_total);
            document.getElementById('conteo-cortes').innerText = `${data.history.length} registros encontrados`;

            // 2. Actualizar Tabla
            const tbody = document.getElementById('historial-tbody');
            tbody.innerHTML = '';
            
            if(data.history.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="table-cell text-center text-slate-400 py-8">No se encontraron datos</td></tr>`;
            }

            data.history.forEach(corte => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-50 transition-colors";
                tr.innerHTML = `
                    <td class="table-cell text-slate-600">
                        <div class="font-medium">${corte.fecha}</div>
                        <div class="text-xs text-slate-500">${corte.hora || '--'}</div>
                    </td>
                    <td class="table-cell font-medium text-slate-700">${corte.cajero || 'N/A'}</td>
                    <td class="table-cell text-slate-500">${formatCurrency(corte.fondo_inicial)}</td>
                    <td class="table-cell text-emerald-600 font-medium">+${formatCurrency(corte.ventas)}</td>
                    <td class="table-cell text-rose-600 font-medium">-${formatCurrency(corte.gastos)}</td>
                    <td class="table-cell font-bold">${formatCurrency(corte.monto_final)}</td>
                    <td class="table-cell text-right">
                        <div class="flex justify-end gap-2">
                            <button class="icon-btn view-btn text-blue-600 hover:bg-blue-50 border-blue-100" 
                                    title="Ver detalle" data-id="${corte.id}">
                                <i data-lucide="eye" class="w-4 h-4"></i>
                            </button>
                            <button class="icon-btn delete-corte-btn text-rose-600 hover:bg-rose-50 border-rose-100" 
                                    title="Eliminar corte" data-id="${corte.id}">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            
            // Refrescar iconos
            if (window.lucide) lucide.createIcons();

            // Listeners dinámicos para la tabla
            document.querySelectorAll('.view-btn').forEach(btn => {
                btn.addEventListener('click', () => abrirModal(btn.dataset.id));
            });
            document.querySelectorAll('.delete-corte-btn').forEach(btn => {
                btn.addEventListener('click', () => eliminarCorte(btn.dataset.id));
            });

        } catch (e) {
            console.error(e);
            showToast("Error cargando datos", "error");
        }
    }

    // Eventos de Filtros
    filterFecha.addEventListener('change', cargarDashboard);
    filterCajero.addEventListener('keyup', cargarDashboard);

    // Función Eliminar Corte
    async function eliminarCorte(id) {
        if(!confirm("¿Estás seguro de eliminar este corte permanentemente?")) return;
        
        try {
            const res = await fetch(`${API_URL}/corte/${id}`, { method: 'DELETE' });
            const json = await res.json();
            
            if(res.ok) {
                showToast("Corte eliminado correctamente", "success");
                cargarDashboard(); // Recargar tabla
            } else {
                showToast(json.message, "error");
            }
        } catch(e) {
            showToast("Error de conexión", "error");
        }
    }


    // ==========================================
    // LÓGICA: MODAL (DETALLE)
    // ==========================================
    
    async function abrirModal(id) {
        try {
            const res = await fetch(`${API_URL}/corte/${id}`);
            const data = await res.json();
            
            document.getElementById('modal-cajero').innerText = data.cajero;
            document.getElementById('modal-fecha').innerText = data.fecha;
            document.getElementById('modal-hora').innerText = data.hora || '--:--';
            
            document.getElementById('modal-fondo').innerText = formatCurrency(data.fondo_inicial);
            document.getElementById('modal-ventas-efectivo').innerText = formatCurrency(data.ventas_efectivo);
            document.getElementById('modal-ventas-tarjeta').innerText = formatCurrency(data.ventas_tarjeta);
            document.getElementById('modal-total-ventas').innerText = formatCurrency(data.total_ventas);
            document.getElementById('modal-gastos').innerText = formatCurrency(data.gastos);
            document.getElementById('modal-neto-calculado').innerText = formatCurrency(data.neto_calculado);
            document.getElementById('modal-observaciones').innerText = data.observaciones || "Ninguna";

            modal.classList.remove('hidden');
            modal.classList.remove('opacity-0');
        } catch(e) { showToast("Error obteniendo detalle", "error"); }
    }

    function cerrarModal() {
        modal.classList.add('hidden');
    }

    modalCloseBtn.addEventListener('click', cerrarModal);
    modal.addEventListener('click', (e) => { if(e.target === modal) cerrarModal(); });


    // ==========================================
    // LÓGICA: GESTIÓN DE USUARIOS
    // ==========================================

        async function cargarUsuarios() {
        const tbody = document.getElementById('usuarios-tbody');
        tbody.innerHTML = `<tr><td colspan="4" class="table-cell text-center text-slate-400">Cargando...</td></tr>`;

        try {
            const res = await fetch(`${API_URL}/usuarios`);
            const data = await res.json();
            tbody.innerHTML = '';

            // Nuestro backend regresa un array simple
            const usuarios = Array.isArray(data) ? data : (data.usuarios || []);

            usuarios.forEach(u => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-50 transition-colors";

                const rolRaw = u.rol || u.role || "";
                const rolLower = String(rolRaw).toLowerCase();

                const roleBadge = rolLower === "gerente"
                    ? '<span class="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">Gerente</span>'
                    : '<span class="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">Cajero</span>';

                // De momento solo bloqueamos borrar al gerente principal
                const deleteBtn = rolLower !== "gerente"
                    ? `<button class="btn-danger ml-auto flex items-center gap-1" onclick="window.eliminarUsuario(${u.id}, '${u.email}')">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                            <span class="hidden sm:inline">Eliminar</span>
                       </button>`
                    : '<span class="text-xs text-slate-400 block text-right pr-2">Principal</span>';

                tr.innerHTML = `
                    <td class="table-cell font-medium text-slate-800">${u.nombre || '--'}</td>
                    <td class="table-cell text-slate-500">${u.email}</td>
                    <td class="table-cell">${roleBadge}</td>
                    <td class="table-cell text-right">${deleteBtn}</td>
                `;
                tbody.appendChild(tr);
            });

            if (window.lucide) lucide.createIcons();
        } catch (e) {
            console.error(e);
            tbody.innerHTML = `<tr><td colspan="4" class="table-cell text-center text-red-500">Error al cargar usuarios</td></tr>`;
        }
    }

    // Función Global para Eliminar Usuario (accesible desde el HTML onclick)
        window.eliminarUsuario = async (id, email) => {
        if (!confirm(`¿Seguro que deseas eliminar al usuario ${email}?`)) return;

        try {
            const res = await fetch(`${API_URL}/usuarios/${id}`, {
                method: 'DELETE'
            });
            const data = await res.json().catch(() => ({}));

            if (res.ok) {
                showToast("Usuario eliminado correctamente", "success");
                cargarUsuarios();
            } else {
                showToast(data.error || data.message || "No se pudo eliminar el usuario", "error");
            }
        } catch (e) {
            console.error(e);
            showToast("Error de conexión al eliminar usuario", "error");
        }
    };

    // Crear Nuevo Usuario
    document.getElementById('add-user-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button');
        const originalText = btn.innerText;
        btn.innerText = "Guardando...";
        btn.disabled = true;

        const data = {
            nombre: document.getElementById('new-nombre').value,
            email: document.getElementById('new-email').value,
            password: document.getElementById('new-password').value,
            // En la BD usamos rol en MAYÚSCULAS: GERENTE / CAJERO
            rol: document.getElementById('new-role').value.toUpperCase()
        };

        try {
            const res = await fetch(`${API_URL}/usuarios`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            const json = await res.json();

            if (res.ok) {
                showToast("Usuario creado correctamente", "success");
                e.target.reset();
                cargarUsuarios();
            } else {
                showToast(json.error || json.message || "No se pudo crear el usuario", "error");
            }
        } catch (e) {
            console.error(e);
            showToast("Error de conexión", "error");
        } finally {
            btn.innerText = originalText;
            btn.disabled = false;
        }
    });

    // --- INICIALIZACIÓN ---
    // Cargar el dashboard por defecto al abrir
    cargarDashboard();
});