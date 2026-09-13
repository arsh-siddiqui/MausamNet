"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { MapPoint, SOURCE_LABELS } from "@/types";
import { RiskBadge, StatusBadge } from "@/components/badges";

interface ContextualPanelProps {
  selected: MapPoint;
  onClose: () => void;
}

export function ContextualPanel({ selected, onClose }: ContextualPanelProps) {
  // Determine if it's an event, signal, or anomaly
  const isEvent = selected.kind === "event";
  const isSignal = selected.kind === "signal";
  const isAnomaly = selected.kind === "anomaly";

  return (
    <div className="absolute bottom-24 right-4 z-[1000] w-[calc(100%-2rem)] max-w-sm rounded-xl border border-ink-600 bg-ink-950/95 p-5 shadow-2xl backdrop-blur-xl md:bottom-auto md:top-4 md:w-80">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-base font-bold uppercase tracking-wide text-slate-100 pr-4 leading-tight">
            {selected.title}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            {selected.district ? `${selected.district}, ` : ""}{selected.state || "India"}
          </p>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white" aria-label="Close details">
          <X size={18} />
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {selected.severity && <RiskBadge severity={selected.severity} />}
        {selected.status && <StatusBadge status={selected.status} />}
        {isSignal && selected.source_category && (
          <span className="rounded border border-ink-600 bg-ink-800/50 px-2 py-0.5 text-[10px] font-bold tracking-wider text-slate-300">
            {SOURCE_LABELS[selected.source_category]}
          </span>
        )}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 text-xs">
        {selected.confidence != null && (
          <div className="rounded-lg bg-ink-900/50 p-2">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Confidence</p>
            <p className="mt-1 font-mono text-lg font-semibold text-signal">{Math.round(selected.confidence)}%</p>
          </div>
        )}
        {selected.trust_score != null && (
          <div className="rounded-lg bg-ink-900/50 p-2">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Trust</p>
            <p className="mt-1 font-mono text-lg font-semibold text-blue-400">{Math.round(selected.trust_score)}/100</p>
          </div>
        )}
        {selected.signal_count != null && (
          <div className="rounded-lg bg-ink-900/50 p-2">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Signals</p>
            <p className="mt-1 font-mono text-lg font-semibold text-slate-200">{selected.signal_count}</p>
          </div>
        )}
        {selected.deviation_pct != null ? (
          <div className="rounded-lg bg-purple-900/20 p-2">
            <p className="text-[10px] font-bold uppercase tracking-widest text-purple-400/70">Deviation</p>
            <p className="mt-1 font-mono text-lg font-semibold text-purple-300">+{Math.round(selected.deviation_pct)}%</p>
          </div>
        ) : isEvent ? (
          <div className="rounded-lg bg-ink-900/50 p-2">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Sources</p>
            <p className="mt-1 font-mono text-lg font-semibold text-slate-200">5+</p>
          </div>
        ) : null}
      </div>

      {isEvent && (
        <div className="mt-4 rounded-lg border border-ink-800 bg-ink-900/30 p-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Evidence</p>
          <div className="space-y-1.5 font-mono text-[10px] text-slate-300">
            {selected.fusion?.explanations?.map((exp: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5">
                <span className={exp.startsWith("✓") ? "text-signal" : "text-slate-400"}>{exp}</span>
              </div>
            )) || (
              <>
                <div className="flex items-start gap-1.5"><span className="text-signal">✓</span> Weather anomaly detected</div>
                <div className="flex items-start gap-1.5"><span className="text-signal">✓</span> Multiple APIs agree</div>
                <div className="flex items-start gap-1.5"><span className="text-signal">✓</span> News & social clusters</div>
                <div className="flex items-start gap-1.5"><span className="text-signal">✓</span> Ground reports verified</div>
              </>
            )}
          </div>
        </div>
      )}

      <div className="mt-5 flex gap-3">
        {isEvent && (
          <Link href={`/events/${selected.id}`} className="focus-ring flex-1 rounded-lg bg-signal py-2.5 text-center text-xs font-bold text-ink-950 transition-transform hover:scale-[1.02] hover:bg-signal-light">
            View Event Intelligence →
          </Link>
        )}
        {isSignal && (
          <Link href={`/signals/${selected.id}`} className="focus-ring flex-1 rounded-lg bg-signal py-2.5 text-center text-xs font-bold text-ink-950 transition-transform hover:scale-[1.02] hover:bg-signal-light">
            View Signal Details →
          </Link>
        )}
        {isAnomaly && (
          <Link href={`/anomalies/${selected.id}`} className="focus-ring flex-1 rounded-lg border border-purple-500/50 bg-purple-500/10 py-2.5 text-center text-xs font-bold text-purple-300 transition-transform hover:scale-[1.02] hover:bg-purple-500/20">
            View Anomaly →
          </Link>
        )}
      </div>
    </div>
  );
}
