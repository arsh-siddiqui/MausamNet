import React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

export function MapLegend({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return (
    <div className={`absolute bottom-6 right-6 z-[1000] rounded-lg border border-ink-700/60 bg-ink-950/95 p-3 shadow-xl backdrop-blur-md transition-all ${open ? "w-56" : "w-auto"}`}>
      <div className="flex cursor-pointer items-center justify-between gap-4" onClick={onToggle}>
        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-300">Map Legend</p>
        {open ? <ChevronDown size={14} className="text-dim" /> : <ChevronUp size={14} className="text-dim" />}
      </div>
      
      {open ? (
        <div className="mt-3 space-y-4">
          <div>
            <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">Event Status</p>
            <ul className="space-y-1.5 text-[11px] text-slate-300">
              <li className="flex items-center gap-2"><div className="h-2 w-2 rounded-full bg-[#ef4444]" /> Critical Operational Risk</li>
              <li className="flex items-center gap-2"><div className="h-2 w-2 rounded-full bg-[#f97316]" /> High / Suspicious</li>
              <li className="flex items-center gap-2"><div className="h-2 w-2 rounded-full bg-[#eab308]" /> Needs Review</li>
              <li className="flex items-center gap-2"><div className="h-2 w-2 rounded-full bg-[#22c55e]" /> Verified / Normal</li>
            </ul>
          </div>
          <div>
            <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">Weather Layers</p>
            <ul className="space-y-1.5 text-[11px] text-slate-300">
              <li className="flex items-center gap-2"><div className="h-2 w-2 rounded-full bg-[#3b82f6]" /> Rainfall Intensity</li>
              <li className="flex items-center gap-2"><div className="h-2 w-2 rounded-full bg-[#8b5cf6]" /> Weather Anomalies</li>
            </ul>
          </div>
          <div>
            <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">Signal Sources</p>
            <ul className="space-y-1.5 text-[11px] text-slate-300">
              <li className="flex items-center gap-2"><span className="text-[10px]">🏛️</span> Government</li>
              <li className="flex items-center gap-2"><span className="text-[10px]">📡</span> Weather API</li>
              <li className="flex items-center gap-2"><span className="text-[10px]">📰</span> News</li>
              <li className="flex items-center gap-2"><span className="text-[10px]">📱</span> Social</li>
              <li className="flex items-center gap-2"><span className="text-[10px]">📍</span> Ground Evidence</li>
            </ul>
          </div>
        </div>
      ) : (
        <div className="mt-3 flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-2 text-[10px] text-slate-300"><div className="h-2 w-2 rounded-full bg-[#ef4444]" /> Critical</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300"><div className="h-2 w-2 rounded-full bg-[#f97316]" /> High</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300"><div className="h-2 w-2 rounded-full bg-[#eab308]" /> Review</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300"><div className="h-2 w-2 rounded-full bg-[#22c55e]" /> Verified</div>
          </div>
          <div className="border-t border-ink-800 pt-2 flex flex-col gap-1.5">
            <div className="flex items-center gap-2 text-[10px] text-slate-300"><div className="h-2 w-2 rounded-full bg-[#3b82f6]" /> Rain</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-300"><div className="h-2 w-2 rounded-full bg-[#8b5cf6]" /> Anomaly</div>
          </div>
          <div className="border-t border-ink-800 pt-2 flex gap-1.5 justify-between">
            <span className="text-[10px]">🏛️</span>
            <span className="text-[10px]">📡</span>
            <span className="text-[10px]">📰</span>
            <span className="text-[10px]">📱</span>
            <span className="text-[10px]">📍</span>
          </div>
        </div>
      )}
    </div>
  );
}
