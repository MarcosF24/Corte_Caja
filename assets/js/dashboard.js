document.addEventListener("DOMContentLoaded", () => {
    // --- UI: Tabs de Navegación ---
    const navDash = document.getElementById('nav-dashboard');
    const navUsers = document.getElementById('nav-usuarios');
    const pageDash = document.getElementById('page-dashboard');
    const pageUsers = document.getElementById('page-usuarios');

    function switchTab(active) {
        if (active === 'dash') {
            pageDash.classList.remove('hidden-section');
            pageUsers.classList.add('hidden-section');
            // Estilos activos para Dash
            navDash.classList.remove('text-slate-400', 'hover:text-white', 'hover:bg-white/10');
            navDash.classList.add('bg-blue-600', 'text-white', 'shadow-lg');
            // Estilos inactivos para Users
            navUsers.classList.add('text-slate-400', 'hover:text-white', 'hover:bg-white/10');
            navUsers.classList.remove('bg-blue-600', 'text-white', 'shadow-lg');
        } else {
            pageDash.classList.add('hidden-section');
            pageUsers.classList.remove('hidden-section');
            // Estilos inactivos para Dash
            navDash.classList.add('text-slate-400', 'hover:text-white', 'hover:bg-white/10');
            navDash.classList.remove('bg-blue-600', 'text-white', 'shadow-lg');
            // Estilos activos para Users
            navUsers.classList.remove('text-slate-400', 'hover:text-white', 'hover:bg-white/10');
            navUsers.classList.add('bg-blue-600', 'text-white', 'shadow-lg');
            
            cargarUsuarios();
        }
    }

    navDash.addEventListener('click', () => switchTab('dash'));
    navUsers.addEventListener('click', () => switchTab('users'));

    // --- UI: Datos del Usuario ---
    const storedName = localStorage.getItem('userNombre') || "Gerente";
    document.getElementById('gerente-nombre').innerText = storedName;
    // Iniciales
    const initials = storedName.split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase() || 'GA';
    document.getElementById('gerente-avatar').innerText = initials;
    document.getElementById('fecha-hoy').innerText = new Date().toLocaleDateString();

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'index.html';
    });

    // ================= DASHBOARD =================

    async function cargarDashboard() {
        const fecha = document.getElementById('filter-fecha').value;
        const cajero = document.getElementById('filter-cajero').value;
        
        const url = new URL(`${API_URL}/obtener-cortes`);
        if (fecha) url.searchParams.append('fecha', fecha);
        if (cajero) url.searchParams.append('cajero', cajero);

        try {
            const res = await fetch(url);
            const data = await res.json();

            // Llenar Tarjetas
            document.getElementById('card-total-ventas').innerText = formatCurrency(data.summary.total_ventas);
            document.getElementById('card-total-gastos').innerText = formatCurrency(data.summary.total_gastos);
            document.getElementById('card-neto-total').innerText = formatCurrency(data.summary.neto_total);
            document.getElementById('conteo-cortes').innerText = `${data.history.length} registros encontrados`;

            // Llenar Tabla
            const tbody = document.getElementById('historial-tbody');
            tbody.innerHTML = '';
            
            if(data.history.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="table-cell text-center text-slate-400 py-8">No se encontraron datos</td></tr>`;
            }

            data.history.forEach(corte => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-50 transition-colors";
                tr.innerHTML = `
                    <td class="table-cell text-slate-600">${corte.fecha}</td>
                    <td class="table-cell text-slate-500 text-xs">${corte.hora || '--'}</td>
                    <td class="table-cell font-medium text-slate-700">${corte.cajero || 'N/A'}</td>
                    <td class="table-cell text-slate-500">${formatCurrency(corte.fondo_inicial)}</td>
                    <td class="table-cell text-emerald-600 font-medium">+${formatCurrency(corte.ventas)}</td>
                    <td class="table-cell text-rose-600 font-medium">-${formatCurrency(corte.gastos)}</td>
                    <td class="table-cell text-right">
                        <button class="icon-btn ml-auto view-btn text-blue-600 hover:bg-blue-50 border-blue-100" data-id="${corte.id}">
                            <i data-lucide="eye" class="w-4 h-4"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            lucide.createIcons();

            // Listeners para botones "Ver"
            document.querySelectorAll('.view-btn').forEach(btn => {
                btn.addEventListener('click', () => abrirModal(btn.dataset.id));
            });

        } catch (e) {
            console.error(e);
            showToast("Error cargando datos", "error");
        }
    }

    document.getElementById('filter-fecha').addEventListener('change', cargarDashboard);
    document.getElementById('filter-cajero').addEventListener('keyup', cargarDashboard);

    // ================= MODAL =================
    
    const modal = document.getElementById('view-modal');
    
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
            // Animación simple
            modal.classList.remove('opacity-0');
        } catch(e) { showToast("Error obteniendo detalle", "error"); }
    }

    function cerrarModal() {
        modal.classList.add('hidden');
    }

    document.getElementById('modal-close-btn').addEventListener('click', cerrarModal);
    modal.addEventListener('click', (e) => { if(e.target === modal) cerrarModal(); });


    // ================= USUARIOS =================

    async function cargarUsuarios() {
        const tbody = document.getElementById('usuarios-tbody');
        tbody.innerHTML = `<tr><td colspan="4" class="table-cell text-center">Cargando...</td></tr>`;
        
        try {
            const res = await fetch(`${API_URL}/usuarios`);
            const data = await res.json();
            tbody.innerHTML = '';

            data.usuarios.forEach(u => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-50 transition-colors";
                
                const roleBadge = u.role === 'gerente' 
                    ? '<span class="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">Gerente</span>'
                    : '<span class="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">Cajero</span>';

                const deleteBtn = u.id !== 1 
                    ? `<button class="btn-danger ml-auto" onclick="eliminarUsuario(${u.id})"><i data-lucide="trash-2" class="w-3 h-3"></i> Eliminar</button>` 
                    : '<span class="text-xs text-slate-400 block text-right pr-2">Principal</span>';
                
                tr.innerHTML = `
                    <td class="table-cell font-medium text-slate-800">${u.nombre || '--'}</td>
                    <td class="table-cell text-slate-500">${u.email}</td>
                    <td class="table-cell">${roleBadge}</td>
                    <td class="table-cell">${deleteBtn}</td>
                `;
                tbody.appendChild(tr);
            });
            lucide.createIcons();
        } catch (e) { console.error(e); }
    }

    window.eliminarUsuario = async (id) => {
        if(!confirm("¿Estás seguro de eliminar este usuario?")) return;
        try {
            const res = await fetch(`${API_URL}/usuario/${id}`, { method: 'DELETE' });
            const json = await res.json();
            if(res.ok) { showToast("Usuario eliminado"); cargarUsuarios(); }
            else showToast(json.message, "error");
        } catch(e) { showToast("Error de red", "error"); }
    };

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
            role: document.getElementById('new-role').value
        };

        try {
            const res = await fetch(`${API_URL}/usuario`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            const json = await res.json();
            if(res.ok) {
                showToast(json.message);
                e.target.reset();
                cargarUsuarios();
            } else {
                showToast(json.message, "error");
            }
        } catch(e) { showToast("Error de conexión", "error"); }
        finally {
            btn.innerText = originalText;
            btn.disabled = false;
        }
    });

    // Inicializar
    cargarDashboard();
});