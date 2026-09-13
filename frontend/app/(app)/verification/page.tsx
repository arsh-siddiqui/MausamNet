"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Eye, SearchX, ShieldAlert, Slash } from "lucide-react";
import { api } from "@/lib/api";
import { VerificationItem } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { RiskBadge, StatusBadge } from "@/components/badges";
import { EmptyState, ErrorState, LoadingState, SectionHeader } from "@/components/primitives";
import { useAuth } from "@/app/providers";

const QUEUE_TABS = [
  { key: "urgent", label: "Urgent", match: (v: VerificationItem) => v.event.severity === "CRITICAL" },
  { key: "high", label: "High Priority", match: (v: VerificationItem) => v.event.severity === "HIGH" },
  { key: "review", label: "Needs Review", match: (v: VerificationItem) => v.event.confidence < 70 },
  { key: "suspicious", label: "Suspicious", match: (v: VerificationItem) => v.trust_score < 55 },
  { key: "all", label: "All", match: () => true },
];

export default function VerificationPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [tab, setTab] = useState("urgent");
  const [rationale, setRationale] = useState("");
  const [toast, setToast] = useState("");

  const queue = useQuery<VerificationItem[]>({
    queryKey: ["verification-queue"],
    queryFn: () => api.get<VerificationItem[]>("/verification/queue"),
    refetchInterval: 20_000,
  });

  const history = useQuery<{ id: string; action: string; event_title: string | null; verifier_name: string; created_at: string }[]>({
    queryKey: ["verification-history"],
    queryFn: () => api.get("/verification/history"),
    refetchInterval: 30_000,
  });

  const act = useMutation({
    mutationFn: (vars: { eventId: string; action: string }) =>
      api.post(`/verification/${vars.eventId}/${vars.action}`, { rationale }),
    onSuccess: (_d, vars) => {
      setToast(`Event ${vars.action.toUpperCase()} — database updated, audit record created.`);
      setTimeout(() => setToast(""), 4000);
      qc.invalidateQueries({ queryKey: ["verification-queue"] });
      qc.invalidateQueries({ queryKey: ["verification-history"] });
      qc.invalidateQueries({ queryKey: ["events"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      setRationale("");
    },
    onError: (e: Error) => {
      setToast(`Action failed: ${e.message}`);
      setTimeout(() => setToast(""), 4000);
    },
  });

  const isVerifier = user?.role === "VERIFIER" || user?.role === "ADMIN";
  const isAnalyst = user?.role === "ANALYST";
  const items = (queue.data ?? []).filter((v) => QUEUE_TABS.find((t) => t.key === tab)?.match(v) ?? true);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Verification Center</h1>
          <p className="mt-0.5 text-xs text-dim">Human-in-the-loop review — every action writes an audit record.</p>
        </div>
        <div className="flex items-center gap-3">
          <DemoBadge compact />
        </div>
      </div>

      {/* Role Indicator Mode */}
      {isVerifier ? (
        <div className="rounded-lg border border-green-500/30 bg-green-500/10 px-4 py-3 flex items-start sm:items-center gap-3">
           <ShieldAlert size={18} className="text-green-400 mt-0.5 sm:mt-0 flex-shrink-0" />
           <div>
             <div className="text-[11px] font-bold uppercase tracking-wider text-green-400">Verifier Mode</div>
             <div className="text-xs text-green-400/80 mt-0.5">Authorized to approve/reject events. All actions are recorded in the audit trail.</div>
           </div>
        </div>
      ) : (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 flex items-start sm:items-center gap-3">
           <SearchX size={18} className="text-amber-400 mt-0.5 sm:mt-0 flex-shrink-0" />
           <div>
             <div className="text-[11px] font-bold uppercase tracking-wider text-amber-400">Analyst Mode</div>
             <div className="text-xs text-amber-400/80 mt-0.5">You can investigate and recommend actions. Final verification requires an authorized verifier.</div>
           </div>
        </div>
      )}

      {/* Tabs */}
      <div className="panel flex flex-wrap gap-1 p-1.5" role="tablist" aria-label="Verification queues">
        {QUEUE_TABS.map((t) => {
          const count = (queue.data ?? []).filter(t.match).length;
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              role="tab"
              aria-selected={tab === t.key}
              className={`focus-ring rounded-md px-3.5 py-2 text-xs font-semibold transition ${tab === t.key ? "bg-signal/15 text-signal" : "text-slate-400 hover:bg-ink-700/50"}`}
            >
              {t.label} <span className="ml-1 rounded bg-ink-700/80 px-1 font-mono text-[10px]">{count}</span>
            </button>
          );
        })}
      </div>

      {queue.isLoading && <LoadingState label="Loading verification queue…" />}
      {queue.isError && <ErrorState message="Queue unavailable." onRetry={() => queue.refetch()} />}

      {queue.data && items.length === 0 && (
        <EmptyState title="Queue is clear." hint="No events match this queue — run the simulation to generate new candidates." />
      )}

      <div className="grid gap-3 xl:grid-cols-2">
        <AnimatePresence>
          {items.map((v) => (
            <motion.div key={v.event.id} layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.98 }} className="panel p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <Link href={`/events/${v.event.id}`} className="focus-ring truncate text-sm font-bold text-slate-100 hover:text-signal">
                    {v.event.title}
                  </Link>
                  <p className="mt-0.5 text-[11px] text-dim">
                    {v.event.city}, {v.event.state} · {v.event.signal_count} signals · via{" "}
                    {Object.entries(v.source_breakdown ?? {}).map(([k, n]) => `${k.replace("_", " ")}×${n}`).join(", ") || "mixed sources"}
                  </p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <RiskBadge severity={v.event.severity} />
                  <span className="font-mono text-sm font-bold text-signal">{Math.round(v.event.confidence)}%</span>
                </div>
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <StatusBadge status={v.event.status} />
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${v.ai_recommendation === "VERIFY" ? "bg-green-500/10 text-green-400" : v.ai_recommendation === "INVESTIGATE" ? "bg-amber-500/10 text-amber-400" : "bg-red-500/10 text-red-400"}`}>
                  AI RECOMMENDS: {v.ai_recommendation}
                </span>
                <span className="rounded bg-ink-700/70 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">TRUST {Math.round(v.trust_score)}</span>
              </div>

              <ul className="mt-2.5 space-y-0.5">
                {(v.evidence_summary ?? []).slice(0, 3).map((x, i) => (
                  <li key={i} className="text-[11px] text-slate-400">{x}</li>
                ))}
              </ul>

              <div className="mt-3 grid grid-cols-2 gap-1.5 sm:grid-cols-4">
                {[
                  { action: "verify", label: "Verify", icon: CheckCircle2, cls: "border-green-500/40 text-green-400 hover:bg-green-500/10", requiresVerifier: true },
                  { action: "investigate", label: "Investigate", icon: SearchX, cls: "border-sky-500/40 text-sky-400 hover:bg-sky-500/10", requiresVerifier: false },
                  { action: "escalate", label: "Escalate", icon: ShieldAlert, cls: "border-amber-500/40 text-amber-400 hover:bg-amber-500/10", requiresVerifier: false },
                  { action: "reject", label: "Reject", icon: Slash, cls: "border-red-500/40 text-red-400 hover:bg-red-500/10", requiresVerifier: true },
                ].map((b) => {
                  const Icon = b.icon;
                  const buttonAllowed = isVerifier || (isAnalyst && !b.requiresVerifier);
                  return (
                    <button
                      key={b.action}
                      disabled={!buttonAllowed || act.isPending}
                      onClick={() => act.mutate({ eventId: v.event.id, action: b.action })}
                      className={`focus-ring flex items-center justify-center gap-1.5 rounded-md border px-2 py-2 text-[11px] font-bold uppercase tracking-wide transition disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent ${b.cls}`}
                      title={buttonAllowed ? b.label : "Requires VERIFIER role"}
                    >
                      <Icon size={13} aria-hidden /> {b.label}
                    </button>
                  );
                })}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Rationale + history */}
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="panel p-4">
          <SectionHeader title="Action Rationale" subtitle="Attached to the audit record for your next action" />
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            rows={3}
            maxLength={2000}
            placeholder="Optional: why you verified/rejected/investigated…"
            className="input-base resize-none"
            aria-label="Verification rationale"
          />
          <p className="mt-1 text-[10px] text-slate-500">
            <Eye size={10} className="mr-1 inline" aria-hidden />
            Audit trail: user ID, timestamp, from/to status, rationale.
          </p>
        </div>
        <div className="panel p-4">
          <SectionHeader title="Recently Verified" subtitle="Latest operator decisions" />
          <ul className="max-h-44 space-y-1.5 overflow-y-auto pr-1">
            {(history.data ?? []).slice(0, 8).map((h) => (
              <li key={h.id} className="flex items-center justify-between rounded border border-ink-700/60 px-3 py-2 text-[11px]">
                <span className="truncate">
                  <b className={h.action === "VERIFY" ? "text-green-400" : h.action === "REJECT" ? "text-red-400" : "text-amber-400"}>{h.action}</b>{" "}
                  <span className="text-slate-300">{h.event_title ?? "—"}</span>
                </span>
                <span className="shrink-0 text-dim">{h.verifier_name} · {new Date(h.created_at).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
              </li>
            ))}
            {(history.data ?? []).length === 0 && <li className="py-4 text-center text-xs text-dim">No verification actions yet.</li>}
          </ul>
        </div>
      </div>

      {toast && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="fixed bottom-5 left-1/2 z-[95] -translate-x-1/2 rounded-lg border border-signal/40 bg-ink-850 px-4 py-2.5 text-xs font-semibold text-slate-100 shadow-2xl" role="status">
          {toast}
        </motion.div>
      )}
    </div>
  );
}
