import React, { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Layers,
  Search,
  Activity,
  AlertTriangle,
  Play,
  Pause,
  RefreshCw,
  GitBranch,
  LogOut,
  User,
  ArrowRight,
  Clock,
  CheckCircle,
  XCircle,
  HelpCircle,
  Plus,
  Send,
  Loader2,
  Lock
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from "recharts";
import { api } from "./api";

// --- Toast Component ---
function Toast({ message, type, onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bg = type === "error" ? "bg-red-900/80 border-red-500" : "bg-emerald-950/80 border-emerald-500";
  const text = type === "error" ? "text-red-200" : "text-emerald-200";

  return (
    <div className={`fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 border rounded-lg shadow-2xl backdrop-blur-md transition-all duration-300 ${bg} ${text}`}>
      {type === "error" ? <XCircle size={18} /> : <CheckCircle size={18} />}
      <span className="text-sm font-medium">{message}</span>
      <button onClick={onClose} className="hover:opacity-80 ml-2">&times;</button>
    </div>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(api.isAuthenticated());
  const [currentUser, setCurrentUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  
  // Auth Form State
  const [isRegister, setIsRegister] = useState(false);
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [authOrg, setAuthOrg] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  const [backendOnline, setBackendOnline] = useState(true);

  // Global State for UI
  const [toasts, setToasts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [pollingActive, setPollingActive] = useState(true);

  useEffect(() => {
    const handleStatus = (e) => {
      setBackendOnline(e.detail.online);
    };
    window.addEventListener("backend-status", handleStatus);
    return () => window.removeEventListener("backend-status", handleStatus);
  }, []);

  // Modal / Form States
  const [showNewJobModal, setShowNewJobModal] = useState(false);
  const [showNewWorkflowModal, setShowNewWorkflowModal] = useState(false);
  const [showNewQueueModal, setShowNewQueueModal] = useState(false);

  const addToast = (message, type = "success") => {
    setToasts((prev) => [...prev, { id: Date.now(), message, type }]);
  };

  useEffect(() => {
    if (isAuthenticated) {
      // Fetch user profile and project config
      api.getMe()
        .then((user) => {
          setCurrentUser(user);
          return api.getProjects();
        })
        .then((projs) => {
          setProjects(projs);
          if (projs.length > 0) {
            setActiveProject(projs[0]);
          }
        })
        .catch((err) => {
          addToast(err.message, "error");
          setIsAuthenticated(false);
        });
    }
  }, [isAuthenticated]);

  // Polling summary stats
  useEffect(() => {
    if (!isAuthenticated) return;
    
    const fetchSummary = () => {
      api.getDashboardSummary()
        .then(setSummary)
        .catch((err) => console.error("Stats fetch error:", err));
    };

    fetchSummary();
    const interval = setInterval(() => {
      if (pollingActive) fetchSummary();
    }, 4000);

    return () => clearInterval(interval);
  }, [isAuthenticated, pollingActive]);

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    try {
      if (isRegister) {
        await api.register(authEmail, authPassword, authName, authOrg);
        addToast("Registered organization and admin user successfully.");
      } else {
        await api.login(authEmail, authPassword);
        addToast("Logged in successfully.");
      }
      setIsAuthenticated(true);
    } catch (err) {
      addToast(err.message, "error");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    api.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setProjects([]);
    setActiveProject(null);
    addToast("Logged out successfully.");
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-radial-gradient text-slate-100">
        {!backendOnline && (
          <div className="fixed top-0 left-0 right-0 bg-red-950/90 border-b border-red-500 text-red-200 text-center py-2.5 px-4 text-xs font-semibold z-50 flex items-center justify-center gap-2 backdrop-blur-md">
             <span>⚠️ Connection Lost: Backend API is currently unreachable. Make sure the backend server is running and CORS is configured.</span>
          </div>
        )}
        <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
          <div className="inline-flex items-center justify-center p-3 bg-blue-600/10 border border-blue-500/20 rounded-2xl mb-4">
            <Layers className="h-10 w-10 text-blue-500 animate-pulse" />
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-white">
            SmartQueue Scheduler
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Intelligent background worker & pipeline orchestrator
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-slate-900 border border-slate-800 py-8 px-4 shadow-2xl rounded-2xl sm:px-10 backdrop-blur-xl">
            <form className="space-y-6" onSubmit={handleAuth}>
              {isRegister && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Full Name
                    </label>
                    <input
                      type="text"
                      required
                      value={authName}
                      onChange={(e) => setAuthName(e.target.value)}
                      className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Jane Doe"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Organization Name
                    </label>
                    <input
                      type="text"
                      required
                      value={authOrg}
                      onChange={(e) => setAuthOrg(e.target.value)}
                      className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="ACME Corp"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="admin@smartqueue.ai"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="••••••••"
                />
              </div>

              <div>
                <button
                  type="submit"
                  disabled={authLoading}
                  className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {authLoading ? (
                    <Loader2 className="animate-spin" size={18} />
                  ) : isRegister ? (
                    "Create Workspace"
                  ) : (
                    "Access Platform"
                  )}
                </button>
              </div>
            </form>

            <div className="mt-6 flex justify-center text-xs">
              <button
                type="button"
                onClick={() => setIsRegister(!isRegister)}
                className="font-medium text-blue-500 hover:text-blue-400 focus:outline-none"
              >
                {isRegister ? "Already registered? Sign In" : "Register a new Account / Organization"}
              </button>
            </div>
          </div>
        </div>
        {toasts.map((t) => (
          <Toast key={t.id} message={t.message} type={t.type} onClose={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))} />
        ))}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070b13] flex text-slate-200 flex-col">
      {!backendOnline && (
        <div className="w-full bg-red-950/90 border-b border-red-500 text-red-200 text-center py-2.5 px-4 text-xs font-semibold z-50 flex items-center justify-center gap-2 backdrop-blur-md">
           <span>⚠️ Connection Lost: Backend API is currently unreachable. Make sure the backend server is running.</span>
        </div>
      )}
      <div className="flex flex-1">
      {/* Sidebar Navigation */}
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
            {[
              { id: "overview", label: "Overview", icon: LayoutDashboard },
              { id: "queues", label: "Queues config", icon: Layers },
              { id: "jobs", label: "Job Explorer", icon: Search },
              { id: "workers", label: "Workers", icon: Activity },
              { id: "workflows", label: "Workflows", icon: GitBranch },
              { id: "dlq", label: "Dead Letter Queue", icon: AlertTriangle },
            ].map((item) => {
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

      {/* Main View Area */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        <header className="h-16 border-b border-slate-900 px-6 flex items-center justify-between bg-[#080d1a]/80 backdrop-blur-md sticky top-0 z-40">
          <div className="flex items-center gap-4">
            <span className="text-xs text-slate-500 uppercase tracking-widest font-semibold">Active Project</span>
            {projects.length > 0 ? (
              <select
                value={activeProject?.id || ""}
                onChange={(e) => setActiveProject(projects.find((p) => p.id === e.target.value))}
                className="bg-[#0b0f19] border border-slate-800 rounded-lg text-xs font-semibold px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 text-white"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-xs text-slate-400 italic">No project</span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setPollingActive(!pollingActive)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold border uppercase tracking-wider transition-all ${
                pollingActive
                  ? "bg-blue-600/10 border-blue-500/30 text-blue-400"
                  : "bg-slate-900 border-slate-800 text-slate-500"
              }`}
            >
              <RefreshCw size={12} className={pollingActive ? "animate-spin" : ""} />
              {pollingActive ? "Live Autorefresh" : "Paused"}
            </button>

            <button
              onClick={() => setShowNewJobModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-500 shadow-lg shadow-blue-900/20"
            >
              <Plus size={14} />
              Dispatch Job
            </button>
            <button
              onClick={() => setShowNewWorkflowModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-500 shadow-lg shadow-indigo-900/20"
            >
              <GitBranch size={14} />
              New Workflow
            </button>
          </div>
        </header>

        <section className="flex-1 p-6">
          {activeTab === "overview" && (
            <OverviewTab summary={summary} activeProject={activeProject} addToast={addToast} />
          )}
          {activeTab === "queues" && (
            <QueuesTab
              activeProject={activeProject}
              addToast={addToast}
              showNewQueueModal={showNewQueueModal}
              setShowNewQueueModal={setShowNewQueueModal}
            />
          )}
          {activeTab === "jobs" && (
            <JobsTab activeProject={activeProject} addToast={addToast} />
          )}
          {activeTab === "workers" && (
            <WorkersTab addToast={addToast} />
          )}
          {activeTab === "workflows" && (
            <WorkflowsTab activeProject={activeProject} addToast={addToast} />
          )}
          {activeTab === "dlq" && (
            <DLQTab addToast={addToast} />
          )}
        </section>
      </main>

      {/* --- New Job Dispatch Modal --- */}
      {showNewJobModal && (
        <NewJobModal
          project={activeProject}
          onClose={() => setShowNewJobModal(false)}
          addToast={addToast}
        />
      )}

      {/* --- New Workflow Modal --- */}
      {showNewWorkflowModal && (
        <NewWorkflowModal
          project={activeProject}
          onClose={() => setShowNewWorkflowModal(false)}
          addToast={addToast}
        />
      )}

      {/* Global toasts rendering */}
      {toasts.map((t) => (
        <Toast
          key={t.id}
          message={t.message}
          type={t.type}
          onClose={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
        />
      ))}
    </div>
  );
}

// ======================== TABS IMPLEMENTATION ========================

// --- OVERVIEW TAB ---
function OverviewTab({ summary, activeProject, addToast }) {
  const [chartData, setChartData] = useState([]);
  
  useEffect(() => {
    if (!activeProject) return;
    // Query last executions to build chart statistics
    api.getJobs({ projectId: activeProject.id, limit: 100 })
      .then((jobs) => {
        // Group by hour or just format list for chart demo
        const hourlyStats = {};
        jobs.slice().reverse().forEach((j) => {
          const date = new Date(j.created_at);
          const hourLabel = `${date.getHours()}:00`;
          if (!hourlyStats[hourLabel]) {
            hourlyStats[hourLabel] = { time: hourLabel, Completed: 0, Failed: 0 };
          }
          if (j.status === "COMPLETED") hourlyStats[hourLabel].Completed += 1;
          if (j.status === "FAILED" || j.status === "DLQ") hourlyStats[hourLabel].Failed += 1;
        });
        const chartList = Object.values(hourlyStats);
        if (chartList.length === 0) {
          // Default seed visual
          setChartData([
            { time: "10:00", Completed: 12, Failed: 1 },
            { time: "11:00", Completed: 18, Failed: 0 },
            { time: "12:00", Completed: 15, Failed: 2 },
            { time: "13:00", Completed: 22, Failed: 1 },
            { time: "14:00", Completed: 30, Failed: 3 },
          ]);
        } else {
          setChartData(chartList);
        }
      });
  }, [activeProject, summary]);

  const stats = [
    { label: "Total jobs", value: summary?.total_jobs ?? 0, desc: "All recorded jobs" },
    { label: "Active claimed/running", value: summary?.running_jobs ?? 0, desc: "Worker claimed tasks" },
    { label: "Completed jobs", value: summary?.completed_jobs ?? 0, desc: "Successful runs" },
    { label: "Queue depth", value: summary?.queue_depth ?? 0, desc: "Queued waiting to claim" },
    { label: "Active Workers", value: summary?.active_workers ?? 0, desc: "Online heartbeat runners" },
    { label: "Success rate", value: `${summary?.success_rate ?? 0}%`, desc: "Run completion efficiency" },
    {
      label: "System health",
      value: summary?.system_health ?? "HEALTHY",
      desc: "Based on queue loads",
      isBadge: true
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((s, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col justify-between">
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">{s.label}</span>
            <div className="mt-2 flex items-baseline">
              {s.isBadge ? (
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold tracking-widest ${
                    s.value === "HEALTHY"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : s.value === "WARNING"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "bg-red-500/10 text-red-400 border border-red-500/20"
                  }`}
                >
                  {s.value}
                </span>
              ) : (
                <span className="text-2xl font-bold text-white tracking-tight">{s.value}</span>
              )}
            </div>
            <p className="text-[10px] text-slate-500 mt-1">{s.desc}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#0a0f1d] border border-slate-900 p-5 rounded-2xl">
          <h3 className="text-xs uppercase font-extrabold tracking-wider text-slate-400 mb-4">
            Throughput (Completed vs Failed over time)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorComp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFail" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155" }} />
                <Legend />
                <Area type="monotone" dataKey="Completed" stroke="#3b82f6" fillOpacity={1} fill="url(#colorComp)" />
                <Area type="monotone" dataKey="Failed" stroke="#ef4444" fillOpacity={1} fill="url(#colorFail)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-[#0a0f1d] border border-slate-900 p-5 rounded-2xl flex flex-col justify-between">
          <div>
            <h3 className="text-xs uppercase font-extrabold tracking-wider text-slate-400 mb-4">
              Operation Guide & Architecture
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-3">
              SmartQueue evaluates tasks by checking prioritizing parameters, scheduled timers, and concurrency slot buffers inside PostgreSQL.
            </p>
            <p className="text-xs text-slate-400 leading-relaxed">
              If tasks fail, Gemini AI analyzes trace logs and generates recovery suggestions. Permanent errors bypass retries to save capacity.
            </p>
          </div>
          <div className="pt-4 border-t border-slate-800/50 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Atomic Claims:</span>
              <span className="text-emerald-400 font-semibold">FOR UPDATE SKIP LOCKED</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Worker Statuses:</span>
              <span className="text-slate-300">ACTIVE, IDLE, BUSY, OFFLINE</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- QUEUES TAB ---
function QueuesTab({ activeProject, addToast, showNewQueueModal, setShowNewQueueModal }) {
  const [queues, setQueues] = useState([]);
  const [stats, setStats] = useState({});
  const [qName, setQName] = useState("");
  const [qDesc, setQDesc] = useState("");
  const [qPriority, setQPriority] = useState(1);
  const [qConcurrency, setQConcurrency] = useState(10);
  const [loading, setLoading] = useState(false);

  const fetchQueues = () => {
    if (!activeProject) return;
    api.getQueues(activeProject.id)
      .then((res) => {
        setQueues(res);
        res.forEach((q) => {
          api.getQueueStats(q.id).then((stat) => {
            setStats((prev) => ({ ...prev, [q.id]: stat }));
          });
        });
      })
      .catch((err) => addToast(err.message, "error"));
  };

  useEffect(() => {
    fetchQueues();
  }, [activeProject]);

  const handleCreateQueue = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createQueue(activeProject.id, qName, qDesc, qPriority, qConcurrency);
      addToast("Queue created successfully.");
      setQName("");
      setQDesc("");
      setQPriority(1);
      setQConcurrency(10);
      setShowNewQueueModal(false);
      fetchQueues();
    } catch (err) {
      addToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePause = async (q) => {
    try {
      if (q.is_paused) {
        await api.resumeQueue(q.id);
        addToast(`Queue '${q.name}' resumed.`);
      } else {
        await api.pauseQueue(q.id);
        addToast(`Queue '${q.name}' paused.`);
      }
      fetchQueues();
    } catch (err) {
      addToast(err.message, "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-white">Queue Configuration</h2>
          <p className="text-xs text-slate-500">Configure processing priority levels, rate limits, and pause jobs.</p>
        </div>
        <button
          onClick={() => setShowNewQueueModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-500"
        >
          <Plus size={14} />
          Create Queue
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {queues.map((q) => {
          const qStat = stats[q.id];
          const isOverloaded = qStat?.is_overloaded;
          const health = qStat?.health_score ?? 100;

          let healthColor = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
          if (health < 80 && health >= 40) healthColor = "text-amber-400 bg-amber-500/10 border-amber-500/20";
          if (health < 40) healthColor = "text-red-400 bg-red-500/10 border-red-500/20";

          return (
            <div key={q.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      {q.name}
                      {q.is_paused && (
                        <span className="px-2 py-0.5 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded text-[9px] font-bold uppercase tracking-wider">
                          PAUSED
                        </span>
                      )}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">{q.description || "No description provided."}</p>
                  </div>

                  <span className={`px-2.5 py-1 text-[10px] font-bold rounded-lg border ${healthColor}`}>
                    Health: {health}/100
                  </span>
                </div>

                {isOverloaded && (
                  <div className="mt-3 flex items-center gap-2 p-2 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-300">
                    <AlertTriangle size={14} className="shrink-0" />
                    <span>Queue is approaching overload. Running workers have hit claims capacity.</span>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/40">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Running / Limit</span>
                    <span className="text-sm font-extrabold text-white">
                      {qStat?.running_jobs ?? 0} / {q.max_concurrency}
                    </span>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/40">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Queue Depth</span>
                    <span className="text-sm font-extrabold text-white">{qStat?.depth ?? 0}</span>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/40">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Avg Duration</span>
                    <span className="text-sm font-extrabold text-white">{qStat?.avg_execution_time ?? 0}s</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/60 flex justify-between items-center mt-4">
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                  Priority level: <span className="text-blue-400">{q.priority}</span>
                </div>

                <button
                  onClick={() => handleTogglePause(q)}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    q.is_paused
                      ? "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                      : "bg-amber-500/10 text-amber-400 hover:bg-amber-500/20"
                  }`}
                >
                  {q.is_paused ? <Play size={12} /> : <Pause size={12} />}
                  {q.is_paused ? "Resume Queue" : "Pause Queue"}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {showNewQueueModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0b0f19] border border-slate-850 rounded-2xl w-full max-w-md p-6 relative">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Create Queue</h3>
            <form onSubmit={handleCreateQueue} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase">Queue Name</label>
                <input
                  type="text"
                  required
                  value={qName}
                  onChange={(e) => setQName(e.target.value)}
                  placeholder="e.g. image-processing"
                  className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase">Description</label>
                <textarea
                  value={qDesc}
                  onChange={(e) => setQDesc(e.target.value)}
                  placeholder="Task description..."
                  className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white h-20"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase">Priority (1-10)</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={qPriority}
                    onChange={(e) => setQPriority(e.target.value)}
                    className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase">Max Concurrency</label>
                  <input
                    type="number"
                    min="1"
                    value={qConcurrency}
                    onChange={(e) => setQConcurrency(e.target.value)}
                    className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowNewQueueModal(false)}
                  className="px-4 py-2 border border-slate-800 text-xs font-bold rounded-lg text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-xs font-bold rounded-lg text-white disabled:opacity-50"
                >
                  {loading ? "Creating..." : "Save Queue"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// --- JOBS EXPLORER TAB ---
function JobsTab({ activeProject, addToast }) {
  const [jobs, setJobs] = useState([]);
  const [queues, setQueues] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [queueFilter, setQueueFilter] = useState("");
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobExecs, setJobExecs] = useState([]);
  const [jobLogs, setJobLogs] = useState([]);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const fetchJobs = () => {
    if (!activeProject) return;
    api.getJobs({
      projectId: activeProject.id,
      queueId: queueFilter || null,
      status: statusFilter || null,
      search: search || null
    })
      .then(setJobs)
      .catch((err) => addToast(err.message, "error"));
  };

  useEffect(() => {
    fetchJobs();
  }, [activeProject, statusFilter, queueFilter, search]);

  useEffect(() => {
    if (activeProject) {
      api.getQueues(activeProject.id).then(setQueues);
    }
  }, [activeProject]);

  const selectJob = async (job) => {
    setSelectedJob(job);
    setJobExecs([]);
    setJobLogs([]);
    setAiAnalysis(null);
    try {
      const execs = await api.getJobExecutions(job.id);
      setJobExecs(execs);
      const logs = await api.getJobLogs(job.id);
      setJobLogs(logs);

      if (job.status === "FAILED" || job.status === "DLQ") {
        setAiLoading(true);
        const analysis = await api.getFailureAnalysis(job.id).catch(() => null);
        setAiAnalysis(analysis);
        setAiLoading(false);
      }
    } catch (err) {
      console.warn("Details fetch error:", err);
    }
  };

  const handleRetryJob = async (jobId) => {
    try {
      await api.retryJob(jobId);
      addToast("Job re-queued successfully.");
      fetchJobs();
      setSelectedJob(null);
    } catch (err) {
      addToast(err.message, "error");
    }
  };

  const handleCancelJob = async (jobId) => {
    try {
      await api.cancelJob(jobId);
      addToast("Job cancelled.");
      fetchJobs();
      setSelectedJob(null);
    } catch (err) {
      addToast(err.message, "error");
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters bar */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg text-xs px-3 py-1.5 text-slate-300"
          >
            <option value="">All Statuses</option>
            <option value="QUEUED">QUEUED</option>
            <option value="CLAIMED">CLAIMED</option>
            <option value="RUNNING">RUNNING</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="FAILED">FAILED</option>
            <option value="DLQ">DLQ</option>
            <option value="BLOCKED">BLOCKED</option>
          </select>

          <select
            value={queueFilter}
            onChange={(e) => setQueueFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg text-xs px-3 py-1.5 text-slate-300"
          >
            <option value="">All Queues</option>
            {queues.map((q) => (
              <option key={q.id} value={q.id}>
                {q.name}
              </option>
            ))}
          </select>
        </div>

        <button onClick={fetchJobs} className="text-slate-400 hover:text-white p-1 text-xs font-semibold flex items-center gap-1">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Table list */}
        <div className="lg:col-span-2 bg-[#0a0f1d] border border-slate-900 rounded-2xl overflow-hidden shadow-xl">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-800/60 bg-slate-900/35 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                <th className="px-4 py-3">Task Name</th>
                <th className="px-4 py-3">Queue</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-xs">
              {jobs.map((job) => {
                let badgeClass = "bg-slate-500/10 text-slate-400 border border-slate-500/20";
                if (job.status === "QUEUED") badgeClass = "bg-blue-500/10 text-blue-400 border border-blue-500/20";
                if (job.status === "RUNNING") badgeClass = "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 animate-pulse";
                if (job.status === "CLAIMED") badgeClass = "bg-sky-500/10 text-sky-400 border border-sky-500/20";
                if (job.status === "COMPLETED") badgeClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                if (job.status === "FAILED") badgeClass = "bg-red-500/10 text-red-400 border border-red-500/20";
                if (job.status === "DLQ") badgeClass = "bg-red-600/20 text-red-400 border border-red-500/30 font-bold";
                if (job.status === "BLOCKED") badgeClass = "bg-purple-500/10 text-purple-400 border border-purple-500/20";

                return (
                  <tr
                    key={job.id}
                    onClick={() => selectJob(job)}
                    className="hover:bg-slate-900/20 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 font-bold text-slate-200">{job.task_name}</td>
                    <td className="px-4 py-3 text-slate-400">
                      {queues.find((q) => q.id === job.queue_id)?.name || "default"}
                    </td>
                    <td className="px-4 py-3 font-semibold text-blue-400">{job.priority}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {new Date(job.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                );
              })}
              {jobs.length === 0 && (
                <tr>
                  <td colSpan="5" className="text-center py-8 text-slate-500 italic">No tasks found. Dispatch a new task!</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Detail Panel */}
        <div className="bg-[#0a0f1d] border border-slate-900 rounded-2xl p-5 shadow-xl space-y-5">
          {selectedJob ? (
            <div className="space-y-4">
              <div className="flex justify-between items-start border-b border-slate-800/80 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">{selectedJob.task_name}</h3>
                  <span className="text-[9px] text-slate-500 font-mono block mt-1 select-all">{selectedJob.id}</span>
                </div>
                <div className="flex gap-2">
                  {(selectedJob.status === "FAILED" || selectedJob.status === "DLQ") && (
                    <button
                      onClick={() => handleRetryJob(selectedJob.id)}
                      className="px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold"
                    >
                      Retry
                    </button>
                  )}
                  {["QUEUED", "RUNNING", "CLAIMED", "BLOCKED"].includes(selectedJob.status) && (
                    <button
                      onClick={() => handleCancelJob(selectedJob.id)}
                      className="px-2 py-1 bg-red-950 text-red-400 hover:bg-red-900 border border-red-500/20 rounded text-[10px] font-bold"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>

              {/* Status Timeline */}
              <div>
                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Job Timeline</h4>
                <div className="flex items-center gap-2 text-xs">
                  <div className="flex items-center gap-1 text-slate-300">
                    <Clock size={12} />
                    <span>Created: {new Date(selectedJob.created_at).toLocaleTimeString()}</span>
                  </div>
                  <ArrowRight size={12} className="text-slate-600" />
                  <div className="flex items-center gap-1 text-slate-300">
                    <CheckCircle size={12} />
                    <span>Status: {selectedJob.status}</span>
                  </div>
                </div>
              </div>

              {/* Payload box */}
              <div>
                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Payload arguments</h4>
                <pre className="bg-slate-950 border border-slate-800/60 p-3 rounded-xl text-[10px] font-mono overflow-auto max-h-32 text-slate-300">
                  {JSON.stringify(selectedJob.payload, null, 2)}
                </pre>
              </div>

              {/* Execution log history */}
              <div>
                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Logs output</h4>
                <div className="bg-slate-950 border border-slate-800/60 p-3 rounded-xl text-[10px] font-mono overflow-auto max-h-40 text-slate-300 space-y-1.5">
                  {jobLogs.map((log) => (
                    <div key={log.id} className="leading-normal">
                      <span className="text-slate-500">[{new Date(log.created_at).toLocaleTimeString()}]</span>{" "}
                      <span className={log.log_level === "ERROR" ? "text-red-400" : log.log_level === "WARNING" ? "text-yellow-400" : "text-slate-300"}>
                        {log.message}
                      </span>
                    </div>
                  ))}
                  {jobLogs.length === 0 && <span className="text-slate-600 italic">No logs generated.</span>}
                </div>
              </div>

              {/* Gemini AI Diagnostic Panel */}
              {(selectedJob.status === "FAILED" || selectedJob.status === "DLQ") && (
                <div className="p-3 bg-red-950/20 border border-red-500/20 rounded-xl space-y-2">
                  <div className="flex justify-between items-center">
                    <h4 className="text-[10px] font-extrabold text-red-400 uppercase tracking-wider flex items-center gap-1">
                      <AlertTriangle size={12} /> AI Diagnosis Report
                    </h4>
                    {aiAnalysis && (
                      <span className="px-1.5 py-0.5 bg-red-600/10 text-red-400 border border-red-500/20 rounded text-[8px] font-bold tracking-widest">
                        {aiAnalysis.severity}
                      </span>
                    )}
                  </div>

                  {aiLoading ? (
                    <div className="flex items-center gap-2 text-xs text-slate-500 py-2">
                      <Loader2 className="animate-spin" size={14} />
                      <span>Diagnosing crash log...</span>
                    </div>
                  ) : aiAnalysis ? (
                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase font-bold tracking-wider">Root Cause</span>
                        <p className="text-slate-300 mt-0.5">{aiAnalysis.failure_reason}</p>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase font-bold tracking-wider">Recommended Fix</span>
                        <p className="text-slate-300 mt-0.5 font-medium">{aiAnalysis.suggested_solution}</p>
                      </div>
                      <div className="flex items-center gap-2 pt-1">
                        <span className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">Retry Strategy:</span>
                        <span className={aiAnalysis.is_temporary ? "text-emerald-400" : "text-amber-400 font-semibold"}>
                          {aiAnalysis.is_temporary ? "Transient (Backoff safe)" : "Permanent Error (Do not retry)"}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-[10px] text-slate-600 italic">No analysis cache found. Retry the job to re-analyze.</p>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-16 text-slate-600 italic">Select a job from the explorer table to inspect logs, timelines, and diagnostics.</div>
          )}
        </div>
      </div>
    </div>
  );
}

// --- WORKERS TAB ---
function WorkersTab({ addToast }) {
  const [workers, setWorkers] = useState([]);

  const fetchWorkers = () => {
    api.getWorkers()
      .then(setWorkers)
      .catch((err) => addToast(err.message, "error"));
  };

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white">Active Workers Cluster</h2>
        <p className="text-xs text-slate-500">Live heartbeat tracker of worker containers and execution loads.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {workers.map((w) => {
          let dotColor = "bg-slate-500";
          if (w.status === "ACTIVE") dotColor = "bg-emerald-400 shadow-[0_0_8px_#34d399]";
          if (w.status === "IDLE") dotColor = "bg-emerald-400 shadow-[0_0_8px_#34d399]";
          if (w.status === "BUSY") dotColor = "bg-amber-400 shadow-[0_0_8px_#fbbf24]";
          if (w.status === "OFFLINE") dotColor = "bg-slate-700";

          // CPU / Memory display
          const cpu = w.system_info?.cpu ?? 10;
          const mem = w.system_info?.memory ?? 25;

          return (
            <div key={w.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    {w.name}
                  </h3>
                  <span className="text-[9px] text-slate-500 font-mono">{w.id.slice(0, 8)}...</span>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className={`w-2.5 h-2.5 rounded-full ${dotColor}`} />
                  <span className="text-xs font-bold text-slate-300 tracking-wide uppercase">{w.status}</span>
                </div>
              </div>

              {/* Resource Bars */}
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>CPU Util</span>
                    <span>{cpu}%</span>
                  </div>
                  <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden mt-0.5 border border-slate-850">
                    <div className="bg-blue-500 h-full transition-all" style={{ width: `${cpu}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>Memory Allocation</span>
                    <span>{mem}%</span>
                  </div>
                  <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden mt-0.5 border border-slate-850">
                    <div className="bg-indigo-500 h-full transition-all" style={{ width: `${mem}%` }} />
                  </div>
                </div>
              </div>

              {/* Work stats */}
              <div className="grid grid-cols-2 gap-2 pt-2 text-center text-xs">
                <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/40">
                  <span className="text-[10px] text-slate-500 block">Completed</span>
                  <span className="text-sm font-bold text-emerald-400">{w.jobs_completed}</span>
                </div>
                <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/40">
                  <span className="text-[10px] text-slate-500 block">Failed</span>
                  <span className="text-sm font-bold text-red-400">{w.jobs_failed}</span>
                </div>
              </div>

              <div className="pt-2 text-center text-[10px] text-slate-500">
                Last Heartbeat: {new Date(w.last_heartbeat).toLocaleTimeString()}
              </div>
            </div>
          );
        })}
        {workers.length === 0 && (
          <div className="col-span-3 text-center py-12 text-slate-500 italic">No workers connected. Launch worker containers!</div>
        )}
      </div>
    </div>
  );
}

// --- WORKFLOWS TAB ---
function WorkflowsTab({ activeProject, addToast }) {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);

  const fetchWorkflows = () => {
    api.getWorkflows()
      .then(setWorkflows)
      .catch((err) => addToast(err.message, "error"));
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const selectWorkflow = (wf) => {
    // Poll updates on details
    api.getWorkflowDetails(wf.id).then(setSelectedWorkflow);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-white">Pipeline Workflows</h2>
          <p className="text-xs text-slate-500">Inspect sequence job queues linked with sequential dependencies.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Workflows list */}
        <div className="bg-[#0a0f1d] border border-slate-900 rounded-2xl overflow-hidden shadow-xl">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-800/60 bg-slate-900/35 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                <th className="px-4 py-3">Workflow Name</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-xs">
              {workflows.map((wf) => (
                <tr
                  key={wf.id}
                  onClick={() => selectWorkflow(wf)}
                  className="hover:bg-slate-900/20 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-bold text-slate-200">{wf.name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      wf.status === "COMPLETED"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : wf.status === "FAILED"
                        ? "bg-red-500/10 text-red-400 border border-red-500/20"
                        : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    }`}>
                      {wf.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(wf.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
              {workflows.length === 0 && (
                <tr>
                  <td colSpan="3" className="text-center py-8 text-slate-500 italic">No workflows created. Trigger one from the header button!</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Visual Map / Details */}
        <div className="bg-[#0a0f1d] border border-slate-900 rounded-2xl p-5 shadow-xl space-y-4">
          {selectedWorkflow ? (
            <div className="space-y-4">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">{selectedWorkflow.name}</h3>
                <p className="text-xs text-slate-500 mt-1">{selectedWorkflow.description || "Sequenced worker steps."}</p>
              </div>

              {/* Node diagram list */}
              <div>
                <h4 className="text-[10px] font-extrabold text-slate-500 uppercase tracking-widest mb-3">Pipeline Node Status Map</h4>
                <div className="space-y-3">
                  {selectedWorkflow.jobs.map((job, idx) => {
                    let dotColor = "bg-slate-600";
                    let bg = "bg-slate-900 border-slate-850";
                    if (job.status === "QUEUED") {
                      dotColor = "bg-blue-400";
                      bg = "bg-blue-950/10 border-blue-900/30";
                    }
                    if (job.status === "RUNNING") {
                      dotColor = "bg-yellow-400 animate-ping";
                      bg = "bg-yellow-950/10 border-yellow-900/30";
                    }
                    if (job.status === "COMPLETED") {
                      dotColor = "bg-emerald-400";
                      bg = "bg-emerald-950/10 border-emerald-900/30 text-emerald-100";
                    }
                    if (job.status === "FAILED" || job.status === "DLQ") {
                      dotColor = "bg-red-500";
                      bg = "bg-red-950/10 border-red-900/30";
                    }

                    return (
                      <div key={job.id} className={`flex items-center gap-3 p-3 border rounded-xl ${bg}`}>
                        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${dotColor}`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-center">
                            <span className="text-xs font-bold text-white block truncate">{job.task_name}</span>
                            <span className="text-[9px] text-slate-500">Step {idx + 1}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 block mt-0.5">Status: <span className="font-semibold text-slate-300">{job.status}</span></span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-slate-600 italic">Select a workflow pipeline from the table to view real-time dependency status maps.</div>
          )}
        </div>
      </div>
    </div>
  );
}

// --- DEAD LETTER QUEUE (DLQ) TAB ---
function DLQTab({ addToast }) {
  const [dlqJobs, setDlqJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const fetchDLQ = () => {
    api.getDLQJobs()
      .then(setDlqJobs)
      .catch((err) => addToast(err.message, "error"));
  };

  useEffect(() => {
    fetchDLQ();
  }, []);

  const selectJob = async (job) => {
    setSelectedJob(job);
    setAiAnalysis(null);
    setAiLoading(true);
    try {
      const res = await api.getFailureAnalysis(job.job_id);
      setAiAnalysis(res);
    } catch (err) {
      console.warn(err);
    } finally {
      setAiLoading(false);
    }
  };

  const handleRetry = async (jobId) => {
    try {
      await api.retryDLQJob(jobId);
      addToast("Job re-queued successfully for execution.");
      fetchDLQ();
      setSelectedJob(null);
    } catch (err) {
      addToast(err.message, "error");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white">Dead Letter Queue (DLQ)</h2>
        <p className="text-xs text-slate-500">Review jobs that failed permanently after exceeding retry limits, diagnosed with AI suggestions.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* DLQ List */}
        <div className="lg:col-span-2 bg-[#0a0f1d] border border-slate-900 rounded-2xl overflow-hidden shadow-xl">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-800/60 bg-slate-900/35 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                <th className="px-4 py-3">Task Name</th>
                <th className="px-4 py-3">Failure Reason</th>
                <th className="px-4 py-3">Failed At</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-xs">
              {dlqJobs.map((job) => (
                <tr
                  key={job.id}
                  onClick={() => selectJob(job)}
                  className="hover:bg-slate-900/20 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-bold text-slate-200">{job.task_name}</td>
                  <td className="px-4 py-3 text-red-400 max-w-xs truncate">{job.failure_reason || job.error_message}</td>
                  <td className="px-4 py-3 text-slate-500">{new Date(job.failed_at).toLocaleTimeString()}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRetry(job.job_id);
                      }}
                      className="px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-[10px] font-bold"
                    >
                      Retry Claim
                    </button>
                  </td>
                </tr>
              ))}
              {dlqJobs.length === 0 && (
                <tr>
                  <td colSpan="4" className="text-center py-8 text-slate-500 italic font-medium">Excellent. Dead Letter Queue is clean and empty!</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* AI Diagnostics Panel */}
        <div className="bg-[#0a0f1d] border border-slate-900 rounded-2xl p-5 shadow-xl space-y-4">
          {selectedJob ? (
            <div className="space-y-4">
              <div className="border-b border-slate-800 pb-3 flex justify-between items-center">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">{selectedJob.task_name}</h3>
                <button
                  onClick={() => handleRetry(selectedJob.job_id)}
                  className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold"
                >
                  Retry Execution
                </button>
              </div>

              {/* Error Stack message */}
              <div>
                <span className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">Raw Stack Error</span>
                <pre className="bg-slate-950 border border-slate-800/60 p-3 rounded-xl text-[9px] font-mono text-red-300 overflow-auto max-h-40 leading-relaxed mt-1">
                  {selectedJob.error_message}
                  {selectedJob.stack_trace && `\n\n${selectedJob.stack_trace}`}
                </pre>
              </div>

              {/* AI diagnostic report */}
              <div className="p-4 bg-red-950/20 border border-red-500/20 rounded-xl space-y-3">
                <h4 className="text-[10px] font-bold text-red-400 uppercase tracking-widest flex items-center gap-1">
                  <AlertTriangle size={12} /> Gemini Crash Diagnosis
                </h4>
                {aiLoading ? (
                  <div className="flex items-center gap-2 text-xs text-slate-500 py-1">
                    <Loader2 className="animate-spin" size={14} />
                    <span>Analyzing stack trace...</span>
                  </div>
                ) : aiAnalysis ? (
                  <div className="space-y-3 text-xs leading-normal">
                    <div>
                      <span className="text-[9px] text-slate-500 block uppercase font-bold">Failure Category</span>
                      <span className="text-slate-300 font-medium block mt-0.5">{aiAnalysis.failure_reason}</span>
                    </div>
                    <div>
                      <span className="text-[9px] text-slate-500 block uppercase font-bold">Remediation Action</span>
                      <span className="text-slate-200 block mt-0.5 font-bold">{aiAnalysis.suggested_solution}</span>
                    </div>
                    <div className="flex gap-4 text-[10px]">
                      <div>
                        <span className="text-slate-500 uppercase block font-bold">Severity</span>
                        <span className="text-red-400 font-bold uppercase">{aiAnalysis.severity}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 uppercase block font-bold">Transient Type</span>
                        <span className="text-slate-300 font-semibold">{aiAnalysis.is_temporary ? "Yes (Delay/Backoff)" : "No (Permanent)"}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-[10px] text-slate-600 italic">Could not load failure analysis diagnostics.</p>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-slate-600 italic">Select a dead-letter job from the list to review the failure stack trace and AI suggestions.</div>
          )}
        </div>
      </div>
    </div>
    </div>
  );
}

// --- MODAL: NEW JOB DISPATCH ---
function NewJobModal({ project, onClose, addToast }) {
  const [queues, setQueues] = useState([]);
  const [qName, setQName] = useState("default");
  const [tName, setTName] = useState("task_success");
  const [priority, setPriority] = useState(1);
  const [payloadText, setPayloadText] = useState('{\n  "data": "Sample background job payload data"\n}');
  const [delaySec, setDelaySec] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (project) {
      api.getQueues(project.id).then(setQueues);
    }
  }, [project]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      let parsedPayload = {};
      try {
        parsedPayload = JSON.parse(payloadText);
      } catch (err) {
        throw new Error("Invalid payload JSON format.");
      }

      const delayInt = delaySec ? parseInt(delaySec) : null;
      await api.createJob(project.id, qName, tName, parsedPayload, priority, delayInt);
      addToast("Job successfully dispatched to the queue scheduler.");
      onClose();
    } catch (err) {
      addToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0b0f19] border border-slate-850 rounded-2xl w-full max-w-lg p-6 relative">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Dispatch Background Task</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase">Target Queue</label>
              <input
                type="text"
                required
                value={qName}
                onChange={(e) => setQName(e.target.value)}
                className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
                placeholder="e.g. default, image-processing"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase">Task Name Registry</label>
              <select
                value={tName}
                onChange={(e) => setTName(e.target.value)}
                className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
              >
                <option value="task_success">task_success (Always works)</option>
                <option value="task_fail">task_fail (Intentional Error)</option>
                <option value="task_network_error">task_network_error (Rule-based timeout)</option>
                <option value="task_validation_error">task_validation_error (Rule-based permanent)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase">Priority level</label>
              <input
                type="number"
                min="0"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase">Scheduling Delay (seconds)</label>
              <input
                type="number"
                min="0"
                value={delaySec}
                onChange={(e) => setDelaySec(e.target.value)}
                placeholder="Leave blank for immediate run"
                className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white placeholder-slate-650"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase">Payload Args (JSON)</label>
            <textarea
              required
              rows="5"
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-300 font-mono"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-slate-800 text-xs font-bold rounded-lg text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-xs font-bold rounded-lg text-white disabled:opacity-50"
            >
              {loading ? "Dispatching..." : "Inject Job"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// --- MODAL: NEW WORKFLOW PIPELINE ---
function NewWorkflowModal({ project, onClose, addToast }) {
  const [wfName, setWfName] = useState("SaaS Build Report");
  const [wfDesc, setWfDesc] = useState("Sequential automated data extract, train, report, and notification pipeline.");
  const [jobs, setJobs] = useState([
    { queue_name: "workflow-queue", task_name: "task_success", payload: { step: "1. Download Data" }, priority: 3 },
    { queue_name: "workflow-queue", task_name: "task_success", payload: { step: "2. Clean Datasets" }, priority: 2 },
    { queue_name: "workflow-queue", task_name: "task_success", payload: { step: "3. Train AI Model" }, priority: 1 },
    { queue_name: "workflow-queue", task_name: "task_success", payload: { step: "4. Send Notification" }, priority: 0 },
  ]);
  const [dependencies, setDependencies] = useState([
    { parent_job_index: 0, child_job_index: 1 },
    { parent_job_index: 1, child_job_index: 2 },
    { parent_job_index: 2, child_job_index: 3 },
  ]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createWorkflow(project.id, wfName, wfDesc, jobs, dependencies);
      addToast("Workflow pipeline created successfully.");
      onClose();
    } catch (err) {
      addToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0b0f19] border border-slate-850 rounded-2xl w-full max-w-lg p-6 relative">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Create Workflow Pipeline</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase">Workflow Name</label>
            <input
              type="text"
              required
              value={wfName}
              onChange={(e) => setWfName(e.target.value)}
              className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase">Description</label>
            <input
              type="text"
              value={wfDesc}
              onChange={(e) => setWfDesc(e.target.value)}
              className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Workflow Steps (4 jobs sequence A {"->"} B {"->"} C {"->"} D)</label>
            <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
              {jobs.map((job, idx) => (
                <div key={idx} className="bg-slate-950 border border-slate-850 p-2.5 rounded-lg flex items-center justify-between text-xs">
                  <span className="font-bold text-white">{job.payload.step}</span>
                  <span className="text-[10px] text-slate-500">Queue: {job.queue_name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-slate-800 text-xs font-bold rounded-lg text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold rounded-lg text-white disabled:opacity-50"
            >
              {loading ? "Creating..." : "Save Workflow"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
