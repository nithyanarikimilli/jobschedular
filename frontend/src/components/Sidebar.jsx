import React from "react";
import {
  LayoutDashboard,
  Layers,
  Search,
  Activity,
  AlertTriangle,
  GitBranch,
  LogOut,
  User
} from "lucide-react";

export default function Sidebar({
  activeTab,
  setActiveTab,
  currentUser,
  handleLogout
}) {
  const navItems = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "queues", label: "Queues config", icon: Layers },
    { id: "jobs", label: "Job Explorer", icon: Search },
    { id: "workers", label: "Workers", icon: Activity },
    { id: "workflows", label: "Workflows", icon: GitBranch },
    { id: "dlq", label: "Dead Letter Queue", icon: AlertTriangle },
  ];

  return (
    <aside className="w-64 bg-[#0a0f1d] border-r border-slate-900 flex flex-col justify-between p-4">
      <div>
        <div className="flex items-center gap-3 px-2 py-3 border-b border-slate-900/60 mb-6">
          <div className="bg-blue-600 p-1.5 rounded-lg text-white">
            <Layers size={20} />
          </div>
          <div>
            <h1 className="font-extrabold text-sm text-white tracking-wide uppercase">SmartQueue</h1>
            <span className="text-[10px] text-slate-500 tracking-wider">DISTRIBUTED TASKING</span>
          </div>
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 ${
                  active
                    ? "bg-blue-600/10 text-blue-400 border-l-2 border-blue-500"
                    : "text-slate-400 hover:bg-slate-900/40 hover:text-white"
                }`}
              >
                <Icon size={16} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div>
        <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800/60 mb-4 flex items-center gap-3">
          <div className="bg-slate-800 p-1 rounded-full text-slate-400">
            <User size={16} />
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-bold text-white truncate">{currentUser?.full_name}</p>
            <p className="text-[10px] text-slate-500 truncate">{currentUser?.email}</p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-red-400 hover:bg-red-950/20 transition-all"
        >
          <LogOut size={16} />
          Exit Workspace
        </button>
      </div>
    </aside>
  );
}
