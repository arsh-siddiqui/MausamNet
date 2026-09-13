"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowRight, Zap } from "lucide-react";
import { api } from "@/lib/api";
import { DashboardOverview, Event, EventsPage, MapPoint, SignalsPage, SimulationStatus } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { RiskBadge, StatusBadge } from "@/components/badges";
import { ErrorState, LoadingState, SectionHeader, StatCard } from "@/components/primitives";
import IndiaMap from "@/components/map/IndiaMapDynamic";
import { useSimulationControls } from "@/hooks/useSimulation";
import { EventTrendCard } from "@/features/dashboard/EventTrendCard";
import { SourceActivityCard } from "@/features/dashboard/SourceActivityCard";
import { WhyThisEventCard } from "@/features/dashboard/WhyThisEventCard";

export default function DashboardPage() {
  const router = useRouter();
  const [selectedPoint, setSelectedPoint] = useState<MapPoint | null>(null);
  const { start } = useSimulationControls();

  const overview = useQuery<DashboardOverview>({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardOverview>("/dashboard/overview"),
    refetchInterval: 15_000,
  });
  const priority = useQuery<EventsPage>({
    queryKey: ["dashboard-priority"],
    queryFn: () => api.get<EventsPage>("/events?page_size=6&sort=confidence&direction=desc"),
    refetchInterval: 15_000,
  });
  const recent = useQuery<SignalsPage>({
    queryKey: ["recent-signals"],
    queryFn: () => api.get<SignalsPage>("/signals?page_size=8&sort=occurred_at&direction=desc"),
    refetchInterval: 15_000,
  });
  const mapPoints = useQuery<MapPoint[]>({
    queryKey: ["map", "dashboard"],
    queryFn: () => api.get<MapPoint[]>("/map/points?layer=events&hours=168&limit=250"),
    refetchInterval: 20_000,
  });
  const sim = useQuery<SimulationStatus>({ queryKey: ["simulation-status"], refetchInterval: 20_000 });

  if (overview.isLoading) return <LoadingState label="Synthesizing national intelligence…" />;
  if (overview.isError) return <ErrorState message="Data source unavailable — command center offline." onRetry={() => overview.refetch()} />;

  const o = overview.data!;
  const topEvent = priority.data?.items?.[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight">National Weather Intelligence Command Center</h1>
            <DemoBadge compact />
          </div>
          <p className="mt-0.5 text-xs text-signal font-mono font-medium tracking-wide">Detect → Correlate → Verify → Act</p>
        </div>
        <div className="flex items-center gap-2">
          {sim.data && !sim.data.running && (
            <button
              onClick={() => start.mutate({ speed: 1 })}
              className="focus-ring flex items-center gap-2 rounded-lg border border-amber-500/50 bg-amber-500/10 px-4 py-2 text-xs font-bold uppercase tracking-wider text-amber-400 hover:bg-amber-500/20"
            >
              <Zap size={14} aria-hidden /> Start Live Intelligence Simulation
            </button>
          )}
          <div className="flex items-center gap-3 font-mono text-[10px] text-slate-400 bg-ink-800/80 px-3 py-1.5 rounded border border-ink-700">
            <span className="flex items-center gap-1.5 font-bold text-slate-200">
              <span className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]"></span>
              SYSTEM OPERATIONAL
            </span>
            <span className="text-ink-600">|</span>
            <span><strong className="text-slate-200">{o.active_events}</strong> ACTIVE</span>
            <span className="text-ink-600">|</span>
            <span><strong className="text-red-400">{o.critical_events}</strong> CRITICAL</span>
            <span className="text-ink-600">|</span>
            <span>LAST INGEST {new Date(o.generated_at).toLocaleString("en-IN", { hour: "2-digit", minute: "2-digit" })}</span>
          </div>
        </div>
      </div>

      {/* KPI Funnel */}
      <div className="flex flex-wrap items-stretch justify-between gap-2 bg-ink-900 p-2 rounded-xl border border-ink-800 shadow-inner">
        <div className="flex-1 min-w-[140px] relative">
          <StatCard label="Signals Processed" value={o.signals_processed} accent="#38bdf8" onClick={() => router.push("/signals")} />
          <div className="absolute top-1/2 -right-3 -translate-y-1/2 z-10 hidden xl:flex text-ink-600">
            <ArrowRight size={20} />
          </div>
        </div>
        <div className="flex-1 min-w-[140px] relative">
          <StatCard label="Suspicious Signals" value={o.suspicious_signals} accent="#f97316" onClick={() => router.push("/signals?suspicious=true")} />
          <div className="absolute top-1/2 -right-3 -translate-y-1/2 z-10 hidden xl:flex text-ink-600">
            <ArrowRight size={20} />
          </div>
        </div>
        <div className="flex-1 min-w-[140px] relative">
          <StatCard label="Active Events" value={o.active_events} accent="#ef4444" onClick={() => router.push("/events")} />
          <div className="absolute top-1/2 -right-3 -translate-y-1/2 z-10 hidden xl:flex text-ink-600">
            <ArrowRight size={20} />
          </div>
        </div>
        <div className="flex-1 min-w-[140px] relative">
          <StatCard label="Pending Reviews" value={o.pending_reviews} accent="#eab308" onClick={() => router.push("/verification")} />
          <div className="absolute top-1/2 -right-3 -translate-y-1/2 z-10 hidden xl:flex text-ink-600">
            <ArrowRight size={20} />
          </div>
        </div>
        <div className="flex-1 min-w-[140px]">
          <StatCard label="Verified Events" value={o.verified_events} accent="#22c55e" onClick={() => router.push("/events?status=VERIFIED")} />
        </div>
      </div>

      {/* Map + priority queue */}
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="panel p-4 xl:col-span-2">
          <SectionHeader
            title="Live India Intelligence Map"
            subtitle="Verified & candidate events — click a cluster for details"
            right={
              <Link href="/live-map" className="focus-ring flex items-center gap-1 text-[11px] font-semibold text-signal hover:underline">
                Full map <ArrowRight size={12} aria-hidden />
              </Link>
            }
          />
          <IndiaMap points={mapPoints.data ?? []} onSelect={(p) => setSelectedPoint(p)} height="440px" selectedId={selectedPoint?.id ?? null} />
          {selectedPoint && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-3 flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-signal/30 bg-ink-900/80 p-4 shadow-lg backdrop-blur-sm">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <RiskBadge severity={selectedPoint.severity} />
                  <p className="truncate text-sm font-bold uppercase tracking-wide text-slate-100">{selectedPoint.title}</p>
                </div>
                
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="block text-slate-500 font-mono mb-0.5">Confidence</span>
                    <span className="font-bold text-signal">{selectedPoint.confidence ? `${Math.round(selectedPoint.confidence)}%` : '--'}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500 font-mono mb-0.5">Trust</span>
                    <span className="font-bold text-blue-400">{selectedPoint.trust_score ? `${Math.round(selectedPoint.trust_score)}/100` : '--'}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500 font-mono mb-0.5">Signals</span>
                    <span className="font-bold text-slate-200">{selectedPoint.signal_count ?? '--'}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500 font-mono mb-0.5">Sources</span>
                    <span className="font-bold text-slate-200">Multiple</span>
                  </div>
                </div>
              </div>
              
              <div className="shrink-0">
                {selectedPoint.kind === "event" && (
                  <Link href={`/events/${selectedPoint.id}`} className="focus-ring flex items-center gap-2 rounded-lg bg-signal px-4 py-2.5 text-xs font-bold text-ink-950 hover:bg-signal-dim shadow-[0_0_10px_rgba(56,189,248,0.2)] w-full sm:w-auto justify-center">
                    View Intelligence <ArrowRight size={14} aria-hidden />
                  </Link>
                )}
                {selectedPoint.kind === "signal" && (
                  <Link href={`/signals/${selectedPoint.id}`} className="focus-ring flex items-center gap-2 rounded-lg bg-signal px-4 py-2.5 text-xs font-bold text-ink-950 hover:bg-signal-dim w-full sm:w-auto justify-center">
                    View Signal <ArrowRight size={14} aria-hidden />
                  </Link>
                )}
              </div>
            </motion.div>
          )}
        </div>

        {/* Priority queue */}
        <div className="panel p-4">
          <SectionHeader title="Priority Queue" subtitle="Highest-confidence active events" />
          <ol className="space-y-2">
            {(priority.data?.items ?? []).map((e: Event, i: number) => (
              <motion.li key={e.id} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}>
                <Link href={`/events/${e.id}`} className="focus-ring block rounded-lg border border-ink-700/70 bg-ink-850/60 p-3 transition hover:border-signal/40">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-semibold text-slate-100">
                      <span className="mr-1.5 font-mono text-xs text-slate-500">{i + 1}.</span>
                      {e.title}
                    </p>
                    <span className="font-mono text-sm font-bold text-signal">{Math.round(e.confidence)}%</span>
                  </div>
                  <div className="mt-1.5 flex items-center gap-2">
                    <RiskBadge severity={e.severity} />
                    <StatusBadge status={e.status} />
                    <span className="ml-auto text-[10px] text-dim">{e.signal_count} signals</span>
                  </div>
                </Link>
              </motion.li>
            ))}
            {(priority.data?.items ?? []).length === 0 && <li className="p-4 text-center text-xs text-dim">No active events.</li>}
          </ol>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid gap-4 lg:grid-cols-3">
        <EventTrendCard />
        <div className="panel p-4">
          <SectionHeader
            title="Recent Intelligence"
            subtitle="Latest signals ingested"
            right={<Link href="/signals" className="text-[11px] font-semibold text-signal hover:underline">Signal Explorer →</Link>}
          />
          <ul className="space-y-2">
            {(recent.data?.items ?? []).map((s) => (
              <li key={s.id}>
                <Link href={`/signals/${s.id}`} className="focus-ring block rounded-md border border-ink-700/60 p-2.5 hover:border-signal/40">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-xs font-medium text-slate-200">{s.headline}</p>
                    <RiskBadge severity={s.severity} />
                  </div>
                  <p className="mt-1 flex items-center gap-2 text-[10px] text-dim">
                    <span className="rounded bg-ink-700/60 px-1 font-mono">{s.source_category.replace("_", " ")}</span>
                    <span>{s.city}</span>
                    <span className="ml-auto">{new Date(s.occurred_at).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
                  </p>
                </Link>
              </li>
            ))}
            {(recent.data?.items ?? []).length === 0 && <li className="p-4 text-center text-xs text-dim">No signals yet — start the simulation.</li>}
          </ul>
        </div>
        <SourceActivityCard />
      </div>

      {topEvent && (
        <WhyThisEventCard event={topEvent} />
      )}
    </div>
  );
}
