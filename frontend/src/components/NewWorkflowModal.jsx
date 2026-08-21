import React, { useState } from "react";
import { api } from "../api";

export default function NewWorkflowModal({ project, onClose, addToast }) {
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
