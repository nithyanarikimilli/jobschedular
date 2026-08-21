import React, { useState, useEffect } from "react";
import { Search, RefreshCw, Clock, CheckCircle, ArrowRight, AlertTriangle, Loader2 } from "lucide-react";
import { api } from "../api";

export default function JobExplorer({ activeProject, addToast }) {
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
