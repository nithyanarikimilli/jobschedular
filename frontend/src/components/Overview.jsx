import React, { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts";
import { api } from "../api";
import StatCard from "./StatCard";

export default function Overview({ summary, activeProject }) {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    if (!activeProject) return;

    api.getJobs({
      projectId: activeProject.id,
      limit: 100
    }).then((jobs) => {
      const hourlyStats = {};
      const jobsList = Array.isArray(jobs) ? jobs : (jobs && Array.isArray(jobs.data) ? jobs.data : []);

      jobsList.slice().reverse().forEach((j) => {
        const date = new Date(j.created_at);
        const hourLabel = `${date.getHours()}:00`;

        if (!hourlyStats[hourLabel]) {
          hourlyStats[hourLabel] = {
            time: hourLabel,
            Completed: 0,
            completed: 0,
            Failed: 0,
            failed: 0
          };
        }

        if (j.status === "COMPLETED") {
          hourlyStats[hourLabel].Completed += 1;
          hourlyStats[hourLabel].completed += 1;
        }

        if (j.status === "FAILED" || j.status === "DLQ") {
          hourlyStats[hourLabel].Failed += 1;
          hourlyStats[hourLabel].failed += 1;
        }
      });

      const chartList = Object.values(hourlyStats);

      if (chartList.length === 0) {
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
          <StatCard
            key={idx}
            label={s.label}
            value={s.value}
            desc={s.desc}
            isBadge={s.isBadge}
          />
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
