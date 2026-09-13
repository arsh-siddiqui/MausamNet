"use client";

import { useMemo } from "react";
import { MapPoint } from "@/types";

interface BottomEventStripProps {
  points: MapPoint[];
  onSelect: (point: MapPoint) => void;
}

export function BottomEventStrip({ points, onSelect }: BottomEventStripProps) {
  const events = useMemo(() => {
    // Only show critical/high/medium events
    return points
      .filter((p) => p.kind === "event" && (p.severity === "CRITICAL" || p.severity === "HIGH" || p.severity === "MEDIUM"))
      .sort((a, b) => {
        const order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2 };
        const sevA = order[(a.severity as keyof typeof order)] ?? 99;
        const sevB = order[(b.severity as keyof typeof order)] ?? 99;
        if (sevA !== sevB) return sevA - sevB;
        return (b.confidence ?? 0) - (a.confidence ?? 0);
      })
      .slice(0, 5); // Limit to top 5
  }, [points]);

  if (events.length === 0) return null;

  return (
    <div className="flex w-full items-center gap-3 overflow-x-auto border-t border-ink-800 bg-ink-950 px-4 py-2 scrollbar-hide">
      <span className="shrink-0 text-[10px] font-bold uppercase tracking-widest text-slate-500">Live Events</span>
      <div className="h-4 w-px bg-ink-800 shrink-0" />
      {events.map((event) => {
        let dotColor = "bg-yellow-500";
        if (event.severity === "CRITICAL") dotColor = "bg-red-500";
        if (event.severity === "HIGH") dotColor = "bg-orange-500";

        return (
          <button
            key={event.id}
            onClick={() => onSelect(event)}
            className="flex shrink-0 items-center gap-2 rounded-full border border-ink-800 bg-ink-900/50 px-3 py-1 transition-colors hover:border-ink-600 hover:bg-ink-800"
          >
            <span className={`h-2 w-2 rounded-full ${dotColor} shadow-[0_0_8px_currentColor]`} />
            <span className="text-[11px] font-medium text-slate-200">{event.title}</span>
            <span className="text-[10px] font-bold text-slate-400">{Math.round(event.confidence ?? 0)}%</span>
          </button>
        );
      })}
    </div>
  );
}
