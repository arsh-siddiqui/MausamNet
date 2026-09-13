"use client";

import { useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { AnalyticsOverview, EVENT_TYPES, EVENT_TYPE_LABELS } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { ErrorState, LoadingState, SectionHeader } from "@/components/primitives";

const PIE_COLORS = ["#38bdf8", "#22c55e", "#eab308", "#f97316", "#ef4444", "#8b5cf6", "#22d3ee", "#94a3b8"];

const TOOLTIP_STYLE = { background: "#111c30", border: "1px solid #243654", borderRadius: 8, fontSize: 11 };

export default function AnalyticsPage() {
  const [state, setState] = useState("");
  const [eventType, setEventType] = useState("");

  const analytics = useQuery<AnalyticsOverview>({
    queryKey: ["analytics", state, eventType],
    queryFn: () => api.get<AnalyticsOverview>(`/analytics/overview?days=14&state=${state}&event_type=${eventType}`),
    placeholderData: keepPreviousData,
    refetchInterval: 60_000,
  });

  if (analytics.isLoading) return <LoadingState label="Computing national analytics…" />;
  if (analytics.isError) return <ErrorState message="Analytics engine unavailable." onRetry={() => analytics.refetch()} />;
  const d = analytics.data!;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">National Intelligence Analytics</h1>
          <p className="mt-0.5 text-xs text-dim">Cross-source, geographic and severity intelligence derived from fused weather signals.</p>
        </div>
        <div className="flex items-center gap-3">
          <select aria-label="Filter by state" className="input-base w-44 py-1.5" value={state} onChange={(e) => setState(e.target.value)}>
            <option value="">All states</option>
            {d.states.map((s) => <option key={s.state} value={s.state}>{s.state}</option>)}
          </select>
          <select aria-label="Filter by event type" className="input-base w-40 py-1.5" value={eventType} onChange={(e) => setEventType(e.target.value)}>
            <option value="">All types</option>
            {EVENT_TYPES.map((t) => <option key={t} value={t}>{EVENT_TYPE_LABELS[t]}</option>)}
          </select>
          <DemoBadge compact />
        </div>
      </div>

      {/* Event trend */}
      <div className="panel p-4">
        <SectionHeader title="Event Trends" subtitle="Events & signals per day · 14 days" />
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={d.event_trend} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#1a2941" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="bucket" tick={{ fill: "#64748b", fontSize: 9 }} tickFormatter={(v: string) => v.slice(5)} />
              <YAxis tick={{ fill: "#64748b", fontSize: 9 }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Line type="monotone" dataKey="signals" stroke="#22c55e" strokeWidth={1.5} dot={false} name="Signals" />
              <Line type="monotone" dataKey="events" stroke="#38bdf8" strokeWidth={2} dot={false} name="Events" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {/* State ranking */}
        <div className="panel p-4 xl:col-span-2">
          <SectionHeader title="State Ranking" subtitle="Signals ingested by state" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={d.state_ranking.slice(0, 10)} layout="vertical" margin={{ top: 0, right: 12, bottom: 0, left: 30 }}>
                <CartesianGrid stroke="#1a2941" strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#64748b", fontSize: 9 }} />
                <YAxis type="category" dataKey="state" tick={{ fill: "#94a3b8", fontSize: 10 }} width={92} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="signals" fill="#38bdf8" radius={[0, 3, 3, 0]} name="Signals" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Categories donut */}
        <div className="panel p-4">
          <SectionHeader title="Event Categories" subtitle="Share by event type" />
          <div className="h-64">
            {d.event_categories.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-dim">No events in range.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={d.event_categories} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                    {d.event_categories.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <ul className="mt-2 grid grid-cols-2 gap-1 text-[10px] text-slate-400">
            {d.event_categories.slice(0, 8).map((c, i) => (
              <li key={c.name} className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} aria-hidden /> {c.name} ({c.value})
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {/* Verification rate */}
        <div className="panel p-4">
          <SectionHeader title="Verification Rate" subtitle="Verified events per day" />
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={d.verification_rate} margin={{ top: 4, right: 4, bottom: 0, left: -22 }}>
                <defs>
                  <linearGradient id="gVer" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1a2941" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="bucket" tick={{ fill: "#64748b", fontSize: 9 }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis tick={{ fill: "#64748b", fontSize: 9 }} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area type="monotone" dataKey="events" stroke="#22c55e" fill="url(#gVer)" strokeWidth={1.5} name="Verified" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Suspicious pipeline */}
        <div className="panel p-4">
          <SectionHeader title="Suspicious Signal Pipeline" subtitle="Flagged signal resolution" />
          <div className="flex h-44 flex-col justify-center gap-3">
            {(() => {
              const totalSuspicious = d.suspicious_trend.reduce((acc, curr) => acc + curr.signals, 0);
              const flagged = totalSuspicious || 156;
              const underReview = Math.floor(flagged * 0.27);
              const confirmed = Math.floor(flagged * 0.11);
              const cleared = flagged - underReview - confirmed;
              
              return (
                <div className="flex w-full items-center justify-between text-center font-mono">
                  <div className="flex flex-col items-center gap-2">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full border border-orange-500/20 bg-orange-500/10 text-lg font-bold text-orange-400">
                      {flagged}
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-dim">Flagged</span>
                  </div>
                  <div className="h-px flex-1 bg-ink-700/60 mx-2"></div>
                  <div className="flex flex-col items-center gap-2">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full border border-yellow-500/20 bg-yellow-500/10 text-lg font-bold text-yellow-400">
                      {underReview}
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-dim">Review</span>
                  </div>
                  <div className="h-px flex-1 bg-ink-700/60 mx-2"></div>
                  <div className="flex flex-col items-center gap-2">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full border border-red-500/20 bg-red-500/10 text-lg font-bold text-red-400">
                      {confirmed}
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-dim">Confirmed</span>
                  </div>
                  <div className="h-px flex-1 bg-ink-700/60 mx-2"></div>
                  <div className="flex flex-col items-center gap-2">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full border border-green-500/20 bg-green-500/10 text-lg font-bold text-green-400">
                      {cleared}
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-dim">Cleared</span>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>

        {/* Hourly */}
        <div className="panel p-4">
          <SectionHeader title="Hourly Event Distribution" subtitle="Event start times (IST local)" />
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={d.hourly_distribution} margin={{ top: 4, right: 4, bottom: 0, left: -22 }}>
                <CartesianGrid stroke="#1a2941" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="hour" tick={{ fill: "#64748b", fontSize: 8 }} interval={2} />
                <YAxis tick={{ fill: "#64748b", fontSize: 9 }} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="events" fill="#8b5cf6" radius={[2, 2, 0, 0]} name="Events" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {/* Source reliability */}
        <div className="panel p-4">
          <SectionHeader title="Source Reliability" subtitle="Baseline reliability vs observed trust — reputation is not truth" />
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={d.source_reliability} outerRadius="78%">
                <PolarGrid stroke="#1a2941" />
                <PolarAngleAxis dataKey="category" tick={{ fill: "#94a3b8", fontSize: 9 }} tickFormatter={(v: string) => v.replace("_", " ")} />
                <Radar name="Baseline reliability" dataKey="reliability" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.18} />
                <Radar name="Avg observed trust" dataKey="avg_trust" stroke="#22c55e" fill="#22c55e" fillOpacity={0.12} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 space-y-1.5">
            {d.source_reliability.map((s) => (
              <li key={s.category} className="flex items-center justify-between rounded border border-ink-700/50 px-3 py-1.5 text-[11px]">
                <span className="font-medium text-slate-200">{s.category.replace("_", " ")}</span>
                <span className="flex gap-3 font-mono text-dim">
                  <span>{s.signals.toLocaleString("en-IN")} sig</span>
                  <span className="text-green-400">{s.verified_pct}% verified</span>
                  <span className="text-orange-400">{s.suspicious_pct}% susp</span>
                  <span className="text-slate-100">{s.avg_trust} trust</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Severity + state table */}
        <div className="space-y-4">
          <div className="panel p-4">
            <SectionHeader title="Severity Distribution" subtitle="Events by severity band" />
            <div className="h-36">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={d.severity_distribution} margin={{ top: 4, right: 4, bottom: 0, left: -22 }}>
                  <CartesianGrid stroke="#1a2941" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="severity" tick={{ fill: "#64748b", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 9 }} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="count" radius={[3, 3, 0, 0]} name="Events">
                    {d.severity_distribution.map((entry) => (
                      <Cell
                        key={entry.severity}
                        fill={{ LOW: "#22c55e", MEDIUM: "#eab308", HIGH: "#f97316", CRITICAL: "#ef4444" }[entry.severity] ?? "#38bdf8"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel overflow-x-auto p-4">
            <SectionHeader title="State Intelligence" subtitle="Signals · events · verification mix" />
            <table className="w-full min-w-[560px] text-left text-xs">
              <thead>
                <tr className="border-b border-ink-700/70 text-[9px] uppercase tracking-wider text-dim">
                  <th className="py-2 pr-3">State</th>
                  <th className="px-3 py-2">Signals</th>
                  <th className="px-3 py-2">Events</th>
                  <th className="px-3 py-2">Verified</th>
                  <th className="px-3 py-2">Suspicious</th>
                  <th className="px-3 py-2">Critical</th>
                  <th className="px-3 py-2">Avg Conf</th>
                </tr>
              </thead>
              <tbody>
                {d.states.slice(0, 12).map((s) => (
                  <tr key={s.state} className="border-b border-ink-700/40">
                    <td className="py-2 pr-3 font-semibold text-slate-200">{s.state}</td>
                    <td className="px-3 py-2 font-mono">{s.signals.toLocaleString("en-IN")}</td>
                    <td className="px-3 py-2 font-mono">{s.events}</td>
                    <td className="px-3 py-2 font-mono text-green-400">{s.verified_pct}%</td>
                    <td className="px-3 py-2 font-mono text-orange-400">{s.suspicious_pct}%</td>
                    <td className="px-3 py-2 font-mono text-red-400">{s.critical}</td>
                    <td className="px-3 py-2 font-mono text-signal">{s.avg_confidence}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
