import React, { useState, useEffect } from "react";
import { Plus, AlertTriangle, Play, Pause } from "lucide-react";
import { api } from "../api";

export default function QueueConfig({ activeProject, addToast, showNewQueueModal, setShowNewQueueModal }) {
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
