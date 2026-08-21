import React, { useState, useEffect } from "react";
import { api } from "../api";

export default function Workers({ addToast }) {
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
