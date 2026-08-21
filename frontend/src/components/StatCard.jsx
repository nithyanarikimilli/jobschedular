import React from "react";

export default function StatCard({ label, value, desc, isBadge }) {
  return (
    <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col justify-between">
      <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">{label}</span>
      <div className="mt-2 flex items-baseline">
        {isBadge ? (
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold tracking-widest ${
              value === "HEALTHY"
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : value === "WARNING"
                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                : "bg-red-500/10 text-red-400 border border-red-500/20"
            }`}
          >
            {value}
          </span>
        ) : (
          <span className="text-2xl font-bold text-white tracking-tight">{value}</span>
        )}
      </div>
      <p className="text-[10px] text-slate-500 mt-1">{desc}</p>
    </div>
  );
}
