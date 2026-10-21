import { Outlet, useLocation, Link } from "react-router";
import { LayoutDashboard, Users, FileText, FileX2, History } from "lucide-react";

const navItems = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/colaboradores", label: "Colaboradores", icon: Users },
  { path: "/recibos", label: "Recibos", icon: FileText },
  { path: "/rescisoes", label: "Rescisões", icon: FileX2 },
  { path: "/historico", label: "Histórico", icon: History },
];

export function Layout() {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-gray-200">
          <div className="w-8 h-8 bg-blue-700 rounded-lg flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-black tracking-tight">P</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 leading-tight">Player</p>
            <p className="text-xs text-gray-400 leading-tight">Contabilidade</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                <Icon
                  className={`w-4 h-4 flex-shrink-0 ${
                    isActive ? "text-blue-600" : "text-gray-400"
                  }`}
                />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User footer */}
        <div className="px-4 py-4 border-t border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-700 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              RH
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">RH Operacional</p>
              <p className="text-xs text-gray-400 truncate">rh@player.com.br</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
