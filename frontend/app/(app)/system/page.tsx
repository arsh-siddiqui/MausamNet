"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity } from "lucide-react";
import { api } from "@/lib/api";
import { SystemHealth } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { StatusBadge } from "@/components/badges";
import { ErrorState, LoadingState, SectionHeader } from "@/components/primitives";

export default function SystemPage() {
  const health = useQuery<SystemHealth>({
    queryKey: ["system-health"],
    queryFn: () => api.get<SystemHealth>("/system/health"),
    refetchInterval: 10_000,
  });

  if (health.isLoading) return <LoadingState label="Probing services…" />;
  if (health.isError) return <ErrorState message="System probe failed." onRetry={() => health.refetch()} />;

  const d = health.data!;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">System Health</h1>
          <p className="mt-0.5 text-xs text-dim">Live status of every local prototype service — real latency, real heartbeats.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded border border-green-500/40 bg-green-500/10 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-green-400">
            {d.overall} · v{d.version}
          </span>
          <DemoBadge compact />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {d.components.map((c) => (
          <div key={c.name} className="panel p-4">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-bold text-slate-100">{c.name}</p>
              <StatusBadge status={c.status} />
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-dim">{c.detail}</p>
            <div className="mt-3 flex items-center justify-between border-t border-ink-700/60 pt-2.5 text-[10px]">
              <span className="flex items-center gap-1.5 font-mono text-slate-400">
                <Activity size={10} className="text-green-400" aria-hidden /> {c.latency_ms} ms
              </span>
              <span className="text-dim">heartbeat {new Date(c.last_heartbeat).toLocaleTimeString("en-IN")}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="panel p-5">
        <SectionHeader title="Runtime Environment" />
        <div className="grid gap-3 text-xs sm:grid-cols-3">
          <div className="panel-subtle p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-dim">Frontend</p>
            <p className="mt-1 font-mono text-slate-200">Next.js 14 · React 18 · Tailwind</p>
          </div>
          <div className="panel-subtle p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-dim">Backend</p>
            <p className="mt-1 font-mono text-slate-200">FastAPI · SQLAlchemy · SQLite (WAL)</p>
          </div>
          <div className="panel-subtle p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-dim">AI Engines</p>
            <p className="mt-1 font-mono text-slate-200">Classifier · TrustEngine · Dedup · aHash · Z-Score</p>
          </div>
        </div>
      </div>
    </div>
  );
}
