import { DollarSign, LogOut, PanelLeftOpen, PanelLeftClose } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

export default function LayoutCajero({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(true); 

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside
        className={`bg-slate-900 text-white flex flex-col transition-all duration-200 ${
          open ? "w-64" : "w-0 overflow-hidden"
        }`}
      >
        {/* Encabezado del menú */}
        <div className="h-14 px-4 flex items-center gap-2 border-b border-white/10">
          <div className="w-7 h-7 rounded-lg bg-white/10 grid place-items-center">
            <DollarSign className="w-4 h-4" />
          </div>
          <span className="font-semibold">Corte de Caja</span>
        </div>

        {/* Menú principal */}
        <nav className="flex-1 p-3">
          <Link
            to="/corte"
            className={`block px-3 py-2 rounded-md text-sm ${
              pathname === "/corte" ? "bg-white/10" : "hover:bg-white/5"
            }`}
          >
            Registro de Corte
          </Link>
        </nav>

        {/* Botón de cerrar sesión */}
        <div className="p-3">
          <button
            onClick={() => navigate("/")} 
            className="w-full h-10 rounded-md bg-white/10 text-white flex items-center justify-center gap-2 hover:bg-white/20"
          >
            <LogOut className="w-4 h-4" /> Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Contenido principal */}
      <div className="flex-1 min-w-0">
        {/* Topbar */}
        <header className="h-14 bg-white/70 backdrop-blur border-b flex items-center px-4 gap-3">
          {/* Botón de abrir/cerrar menú */}
          <button
            onClick={() => setOpen((v) => !v)}
            className="w-9 h-9 rounded-md border bg-white hover:bg-slate-50 grid place-items-center"
            title={open ? "Ocultar menú" : "Mostrar menú"}
          >
            {open ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
          </button>

          <h1 className="font-medium">Registro de Corte de Caja</h1>
        </header>

        {/* Contenido dinámico */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
