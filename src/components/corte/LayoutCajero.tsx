import { DollarSign, LogOut } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

export default function LayoutCajero({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  return (
    <div className="min-h-screen bg-background">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="w-64 bg-slate-900 text-white flex flex-col">
          <div className="h-14 px-4 flex items-center gap-2 border-b border-white/10">
            <div className="w-7 h-7 rounded-lg bg-white/10 grid place-items-center">
              <DollarSign className="w-4 h-4" />
            </div>
            <span className="font-semibold">Corte de Caja</span>
          </div>

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

          <div className="p-3">
            <button
              className="w-full h-10 rounded-md bg-white/10 text-white/60 cursor-not-allowed flex items-center justify-center gap-2"
              disabled
            >
              <LogOut className="w-4 h-4" /> Cerrar sesión
            </button>
          </div>
        </aside>

        {/* Contenido */}
        <div className="flex-1 min-w-0">
          {/* Topbar */}
          <header className="h-14 bg-white/70 backdrop-blur border-b flex items-center px-6">
            <h1 className="ml-2 font-medium">Registro de Corte de Caja</h1>
          </header>

          <main className="p-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
