import React, { useState, useEffect } from "react";
import { api } from "../api";

export default function Workflows({ activeProject, addToast }) {
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
