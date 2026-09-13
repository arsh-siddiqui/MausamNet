"use client";

import { motion } from "framer-motion";

const BANDS = [
  { min: 80, label: "HIGH CONFIDENCE", color: "#22c55e" },
  { min: 60, label: "MODERATE CONFIDENCE", color: "#38bdf8" },
  { min: 40, label: "LOW CONFIDENCE", color: "#eab308" },
  { min: 0, label: "NEEDS VERIFICATION", color: "#ef4444" },
];

/** Explainable WeatherTrust score card. */
export function TrustScoreCard({ trustScore, breakdown }: { trustScore: number; breakdown: Record<string, number> }) {
  const band = BANDS.find((b) => trustScore >= b.min) ?? BANDS[BANDS.length - 1];
  const verdict = trustScore >= 80 ? "Likely Genuine" : trustScore >= 55 ? "Needs Verification" : "Potentially Misleading";

  return (
    <div className="panel p-5" aria-label={`Trust score ${trustScore} of 100, ${band.label}`}>
      <p className="text-[10px] font-bold uppercase tracking-widest text-dim">WeatherTrust AI</p>
      <div className="mt-2 flex items-end gap-2">
        <motion.p
          key={trustScore}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-mono text-4xl font-extrabold"
          style={{ color: band.color }}
        >
          {trustScore}
        </motion.p>
        <p className="pb-1.5 text-xs text-dim">/ 100</p>
      </div>
      <div className="mt-1 flex items-center gap-2">
        <span className="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider" style={{ color: band.color, backgroundColor: `${band.color}18` }}>
          {band.label}
        </span>
        <span className="text-[11px] text-slate-300">{verdict}</span>
      </div>

      <div className="mt-4 space-y-2">
        {Object.entries(breakdown).map(([k, v]) => (
          <div key={k} className="flex items-center gap-2">
            <span className="w-20 shrink-0 text-[10px] uppercase tracking-wider text-dim">{k}</span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-ink-700/70">
              <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(100, v)}%` }} transition={{ duration: 0.5 }} className="h-full rounded-full bg-signal" />
            </div>
            <span className="w-9 text-right font-mono text-[10px] text-slate-300">{Math.round(v)}%</span>
          </div>
        ))}
      </div>
      <p className="mt-3 text-[10px] leading-relaxed text-slate-500">
        Analytical indicator only — not a guarantee of authenticity. Human verification decides.
      </p>
    </div>
  );
}
