"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import { CountUp } from "./CountUp";

/** KPI stat card — clickable, count-up numbers, hover lift. */
export function StatCard({
  label,
  value,
  hint,
  accent = "#38bdf8",
  onClick,
  suffix,
}: {
  label: string;
  value: number;
  hint?: string;
  accent?: string;
  onClick?: () => void;
  suffix?: string;
}) {
  return (
    <motion.button
      whileHover={{ y: -2 }}
      transition={{ duration: 0.15 }}
      onClick={onClick}
      className="panel focus-ring group w-full p-4 text-left hover:border-signal/40"
      aria-label={`${label}: ${value}${suffix ?? ""}`}
    >
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-dim">{label}</p>
        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: accent }} aria-hidden />
      </div>
      <p className="mt-2 font-mono text-2xl font-semibold text-slate-100">
        <CountUp value={value} />
        {suffix}
      </p>
      {hint ? <p className="mt-1 text-[11px] text-dim">{hint}</p> : null}
    </motion.button>
  );
}

/** Generic section header used across pages. */
export function SectionHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">{title}</h2>
        {subtitle ? <p className="mt-0.5 text-xs text-dim">{subtitle}</p> : null}
      </div>
      {right}
    </div>
  );
}

/** Confidence gauge — semicircular, explainable tooltip. */
export function ConfidenceGauge({ value, size = 92, label = "CONFIDENCE" }: { value: number; size?: number; label?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  const stroke = 8;
  const r = (size - stroke) / 2;
  const circ = Math.PI * r; // semicircle
  const color = pct >= 80 ? "#22c55e" : pct >= 60 ? "#38bdf8" : pct >= 40 ? "#eab308" : "#ef4444";
  return (
    <div className="relative inline-flex flex-col items-center" title={`Confidence ${pct}% — analytical indicator, not certainty`}>
      <svg width={size} height={size / 2 + 10} viewBox={`0 0 ${size} ${size / 2 + 10}`}>
        <path
          d={`M ${stroke / 2} ${size / 2} A ${r} ${r} 0 0 1 ${size - stroke / 2} ${size / 2}`}
          fill="none"
          stroke="#243654"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        <motion.path
          d={`M ${stroke / 2} ${size / 2} A ${r} ${r} 0 0 1 ${size - stroke / 2} ${size / 2}`}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={false}
          animate={{ strokeDashoffset: circ * (1 - pct / 100) }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </svg>
      <div className="-mt-6 text-center">
        <p className="font-mono text-lg font-semibold" style={{ color }}>
          {Math.round(pct)}%
        </p>
        <p className="text-[9px] font-semibold uppercase tracking-widest text-dim">{label}</p>
      </div>
    </div>
  );
}

/** Loading / empty / error states — never a blank page. */
export function LoadingState({ label = "Loading intelligence…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 p-10" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-signal border-t-transparent" aria-hidden />
      <span className="text-sm text-dim">{label}</span>
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 p-10 text-center">
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {hint ? <p className="text-xs text-dim">{hint}</p> : null}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 p-10 text-center">
      <p className="text-sm font-medium text-red-400">{message}</p>
      {onRetry ? (
        <button onClick={onRetry} className="focus-ring rounded border border-ink-600 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:border-signal hover:text-signal">
          Retry
        </button>
      ) : null}
    </div>
  );
}
