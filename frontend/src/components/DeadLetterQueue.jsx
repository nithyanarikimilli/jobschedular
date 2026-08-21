import React, { useState, useEffect } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";
import { api } from "../api";

export default function DeadLetterQueue({ addToast }) {
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
  );
}
