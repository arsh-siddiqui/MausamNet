"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp } from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import { Anomaly, MapPoint } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { RiskBadge } from "@/components/badges";
import { EmptyState, ErrorState, LoadingState, SectionHeader } from "@/components/primitives";
import IndiaMap from "@/components/map/IndiaMapDynamic";

export default function AnomaliesPage() {
  const [stateFilter, setStateFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [selected, setSelected] = useState<Anomaly | null>(null);

  const anomalies = useQuery<Anomaly[]>({
    queryKey: ["anomalies", stateFilter, riskFilter],
    queryFn: () => api.get<Anomaly[]>(`/anomalies?state=${stateFilter}&risk=${riskFilter}`),
    refetchInterval: 30_000,
  });

  const states = useMemo(() => Array.from(new Set((anomalies.data ?? []).map((a) => a.state))).sort(), [anomalies.data]);
  const stateDist = useMemo(() => {
    const m = new Map<string, number>();
    (anomalies.data ?? []).forEach((a) => m.set(a.state, (m.get(a.state) ?? 0) + 1));
    return Array.from(m.entries()).map(([state, count]) => ({ state, count })).sort((a, b) => b.count - a.count).slice(0, 10);
  }, [anomalies.data]);

  const series = useQuery<{ observed_at: string; value: number }[]>({
    queryKey: ["anomaly-series", selected?.city ?? "Mumbai"],
    queryFn: () => api.get<{ observed_at: string; value: number }[]>(`/anomalies/series?city=${encodeURIComponent(selected?.city ?? "Mumbai")}&metric=rainfall_mm`),
    enabled: true,
  });

  const points: MapPoint[] = (anomalies.data ?? []).slice(0, 150).map((a) => ({
    id: a.id,
    kind: "anomaly",
    latitude: a.latitude,
    longitude: a.longitude,
    title: `${a.city} ${a.metric} anomaly`,
    event_type: a.metric,
    severity: a.risk,
    status: null,
    source_category: null,
    confidence: null,
    trust_score: null,
    signal_count: null,
    suspicious: false,
    deviation_pct: a.deviation_pct,
    metric: a.metric,
    occurred_at: a.observed_at,
  }));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Anomaly Center</h1>
          <p className="mt-0.5 text-xs text-dim">Statistical z-score engine — observations beyond mean ± 2σ of each city&apos;s baseline.</p>
        </div>
        <DemoBadge compact />
      </div>

      {/* Filters */}
      <div className="panel flex flex-wrap items-end gap-3 p-3">
        <div>
          <label htmlFor="astate" className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-dim">State</label>
          <select id="astate" className="input-base w-44 py-1.5" value={stateFilter} onChange={(e) => setStateFilter(e.target.value)}>
            <option value="">All states</option>
            {states.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="arisk" className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-dim">Risk</label>
          <select id="arisk" className="input-base w-36 py-1.5" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
            <option value="">All</option>
            {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>

      {anomalies.isLoading && <LoadingState label="Scanning observation baselines…" />}
      {anomalies.isError && <ErrorState message="Anomaly engine unavailable." onRetry={() => anomalies.refetch()} />}

      {anomalies.data && anomalies.data.length === 0 && (
        <EmptyState title="No anomalies detected." hint="All observations within expected statistical bands." />
      )}

      {anomalies.data && anomalies.data.length > 0 && (
        <>
          {/* Anomaly cards */}
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {anomalies.data.slice(0, 12).map((a) => (
              <button
                key={a.id}
                onClick={() => setSelected(a)}
                className={`panel focus-ring p-4 text-left transition hover:border-signal/40 ${selected?.id === a.id ? "border-signal/60" : ""}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-bold text-slate-100">{a.city} {a.metric === "RAINFALL" ? "Rainfall" : a.metric}</p>
                  <RiskBadge severity={a.risk} />
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                  <div className="panel-subtle p-2">
                    <p className="text-[9px] font-semibold uppercase tracking-wider text-dim">Expected</p>
                    <p className="mt-0.5 font-mono text-xs text-slate-300">{a.expected_low}–{a.expected_high}</p>
                  </div>
                  <div className="panel-subtle p-2">
                    <p className="text-[9px] font-semibold uppercase tracking-wider text-dim">Current</p>
                    <p className="mt-0.5 font-mono text-sm font-bold text-signal">{a.observed_value}</p>
                  </div>
                  <div className="panel-subtle p-2">
                    <p className="text-[9px] font-semibold uppercase tracking-wider text-dim">Deviation</p>
                    <p className="mt-0.5 font-mono text-xs font-bold text-orange-400">+{Math.round(a.deviation_pct)}%</p>
                  </div>
                </div>
                <p className="mt-2 flex items-center gap-1.5 text-[10px] text-dim">
                  <TrendingUp size={10} aria-hidden /> {a.zscore}σ above baseline · {a.state}
                  {a.event_id && (
                    <>
                      {" · "}
                      <Link href={`/events/${a.event_id}`} className="font-semibold text-signal hover:underline" onClick={(e) => e.stopPropagation()}>
                        correlated event →
                      </Link>
                    </>
                  )}
                </p>
              </button>
            ))}
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            {/* Map */}
            <div className="panel p-4 xl:col-span-2">
              <SectionHeader title="Anomaly Map" subtitle="Geographic spread of statistical outliers" />
              <IndiaMap points={points} height="380px" onSelect={() => {}} selectedId={null} />
            </div>

            {/* Series + explanation */}
            <div className="panel p-4">
              <SectionHeader title="Time Series" subtitle={selected ? `${selected.city} rainfall (mm)` : "Mumbai rainfall (mm) — select a card"} />
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={(series.data ?? []).map((p) => ({ at: new Date(p.observed_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }), value: p.value }))}
                    margin={{ top: 4, right: 4, bottom: 0, left: -22 }}
                  >
                    <defs>
                      <linearGradient id="gRain" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.5} />
                        <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.03} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#1a2941" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="at" tick={{ fill: "#64748b", fontSize: 9 }} />
                    <YAxis tick={{ fill: "#64748b", fontSize: 9 }} />
                    <Tooltip contentStyle={{ background: "#111c30", border: "1px solid #243654", borderRadius: 8, fontSize: 11 }} />
                    <Area type="monotone" dataKey="value" stroke="#38bdf8" fill="url(#gRain)" strokeWidth={1.5} name="mm" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              {selected && (
                <div className="mt-3 rounded-md border border-signal/30 bg-signal/5 p-3">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-signal">Why is this anomalous?</p>
                  <ul className="mt-1.5 space-y-1">
                    {(selected.explanation ?? []).map((x, i) => (
                      <li key={i} className="text-[11px] text-slate-300">{x}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* State distribution */}
          <div className="panel p-4">
            <SectionHeader title="State Distribution" subtitle="Anomaly count by state" />
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stateDist} margin={{ top: 4, right: 4, bottom: 0, left: -22 }}>
                  <CartesianGrid stroke="#1a2941" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="state" tick={{ fill: "#64748b", fontSize: 9 }} interval={0} angle={-18} textAnchor="end" height={48} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 9 }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: "#111c30", border: "1px solid #243654", borderRadius: 8, fontSize: 11 }} />
                  <Bar dataKey="count" fill="#f97316" radius={[3, 3, 0, 0]} name="Anomalies" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
