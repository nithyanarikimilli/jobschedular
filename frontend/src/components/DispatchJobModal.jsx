import React, { useState, useEffect } from "react";
import { api } from "../api";

export default function DispatchJobModal({ project, onClose, addToast }) {
  const [queues, setQueues] = useState([]);
  const [qName, setQName] = useState("default");
  const [tName, setTName] = useState("task_success");
  const [priority, setPriority] = useState(1);
  const [payloadText, setPayloadText] = useState('{\n  "data": "Sample background job payload data"\n}');
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

      await api.createJob(project.id, qName, tName, parsedPayload, priority, null);
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
              <label className="block text-xs font-bold text-slate-500 uppercase">Priority Level</label>
              <input
                type="number"
                min="0"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="mt-1 block w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-white"
              />
            </div>
            <div></div>
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
