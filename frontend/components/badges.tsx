import { SEVERITY_COLORS } from "@/types";

/** Severity/risk badge — color + label + dot, never color alone (a11y). */
export function RiskBadge({ severity, className = "" }: { severity: string; className?: string }) {
  const color = SEVERITY_COLORS[severity] || "#94a3b8";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${className}`}
      style={{ borderColor: `${color}55`, color, backgroundColor: `${color}14` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} aria-hidden />
      {severity}
    </span>
  );
}

const STATUS_COLORS: Record<string, string> = {
  VERIFIED: "#22c55e",
  ACTIVE: "#38bdf8",
  CANDIDATE: "#eab308",
  REJECTED: "#ef4444",
  RESOLVED: "#94a3b8",
  SUSPICIOUS: "#f97316",
  DUPLICATE: "#94a3b8",
  CLASSIFIED: "#38bdf8",
  NEW: "#eab308",
  OPERATIONAL: "#22c55e",
  DEGRADED: "#f97316",
  OFFLINE: "#ef4444",
  STRONG: "#22c55e",
  SUPPORTING: "#38bdf8",
  WEAK: "#eab308",
  ABSENT: "#64748b",
  CONTRADICTING: "#ef4444",
};

export function StatusBadge({ status, className = "" }: { status: string; className?: string }) {
  const color = STATUS_COLORS[status] || "#94a3b8";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${className}`}
      style={{ borderColor: `${color}55`, color, backgroundColor: `${color}14` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} aria-hidden />
      {status.replace(/_/g, " ")}
    </span>
  );
}
