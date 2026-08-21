import React, { useState, useEffect } from "react";
import { Layers, Plus, GitBranch } from "lucide-react";
import { api } from "./api";
import Sidebar from "./components/Sidebar";
import Overview from "./components/Overview";
import QueueConfig from "./components/QueueConfig";
import JobExplorer from "./components/JobExplorer";
import Workers from "./components/Workers";
import Workflows from "./components/Workflows";
import DeadLetterQueue from "./components/DeadLetterQueue";
import DispatchJobModal from "./components/DispatchJobModal";
import NewWorkflowModal from "./components/NewWorkflowModal";

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
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        handleLogout={handleLogout}
      />

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
            <Overview summary={summary} activeProject={activeProject} />
          )}
          {activeTab === "queues" && (
            <QueueConfig
              activeProject={activeProject}
              addToast={addToast}
              showNewQueueModal={showNewQueueModal}
              setShowNewQueueModal={setShowNewQueueModal}
            />
          )}
          {activeTab === "jobs" && (
            <JobExplorer activeProject={activeProject} addToast={addToast} />
          )}
          {activeTab === "workers" && (
            <Workers addToast={addToast} />
          )}
          {activeTab === "workflows" && (
            <Workflows activeProject={activeProject} addToast={addToast} />
          )}
          {activeTab === "dlq" && (
            <DeadLetterQueue addToast={addToast} />
          )}
        </section>
      </main>

      {/* --- New Job Dispatch Modal --- */}
      {showNewJobModal && (
        <DispatchJobModal
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
    </div>
  );
}

