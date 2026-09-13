"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { EventDetail, EvidenceEntry, MapPoint } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { RiskBadge, StatusBadge } from "@/components/badges";
import { ConfidenceGauge, ErrorState, LoadingState, SectionHeader } from "@/components/primitives";
import IndiaMap from "@/components/map/IndiaMapDynamic";
import { EvidenceGraph } from "@/features/events/EvidenceGraph";
import { Radio } from "lucide-react";

const FUSION_LABELS: Record<string, string> = {
  meteorological: "Meteorological Evidence",
  spatial_consistency: "Spatial Consistency",
  temporal_consistency: "Temporal Consistency",
  source_reliability: "Source Reliability",
  media_authenticity: "Media Authenticity",
  cross_source_agreement: "Cross-source Agreement",
};

export default function EventDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const [sliderIdx, setSliderIdx] = useState(1);

  const event = useQuery<EventDetail>({
    queryKey: ["event", id],
    queryFn: () => api.get<EventDetail>(`/events/${id}`),
    refetchInterval: 20_000,
  });

  if (event.isLoading) return <LoadingState label="Assembling event intelligence…" />;
  if (event.isError) return <ErrorState message="Event unavailable." onRetry={() => event.refetch()} />;
  const e = event.data!;

  const evidenceRows = Object.entries(e.evidence ?? {}) as [string, EvidenceEntry][];
  const signalsUpTo = (fraction: number) => e.signals.slice(0, Math.max(1, Math.floor(e.signals.length * fraction)));
  const evolutionSignals = signalsUpTo(sliderIdx / 10);
  const evolutionPoints = evolutionSignals.map((s) => ({
    id: s.id,
    kind: "signal" as const,
    latitude: s.latitude,
    longitude: s.longitude,
    title: s.headline,
    event_type: s.event_type,
    severity: s.severity,
    status: s.status,
    source_category: s.source_category,
    trust_score: s.trust_score,
    suspicious: s.suspicious,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold uppercase tracking-tight">{e.title}</h1>
              <StatusBadge status={e.status} />
              <RiskBadge severity={e.severity} />
              <DemoBadge compact />
            </div>
            <p className="mt-1 text-xs text-dim">
              {e.city}, {e.state} · started {new Date(e.started_at).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })} · latest{" "}
              {new Date(e.latest_at).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
            </p>
          </div>
          <div className="flex items-center gap-6">
            <ConfidenceGauge value={e.confidence} />
            <div className="space-y-1.5 text-center">
              <p className="font-mono text-2xl font-bold text-slate-100">{e.signal_count}</p>
              <p className="text-[9px] font-bold uppercase tracking-widest text-dim">Signals</p>
            </div>
            <div className="space-y-1.5 text-center">
              <p className="font-mono text-2xl font-bold text-slate-100">{Math.round(e.trust_score)}</p>
              <p className="text-[9px] font-bold uppercase tracking-widest text-dim">Avg Trust</p>
            </div>
          </div>
        </div>
      </div>

      {/* Overview + map */}
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="panel space-y-4 p-5 xl:col-span-2">
          <SectionHeader title="Event Overview" />
          <p className="text-sm leading-relaxed text-slate-300">{e.description}</p>
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { k: "Affected Area", v: `${Math.round(e.metrics?.radius_km ?? e.radius_km)} km radius` },
              { k: "Growth Rate", v: `${e.metrics?.growth_rate?.toFixed(1) ?? "0.0"}x (last hr)` },
              { k: "Peak Rainfall", v: `${Math.round(e.metrics?.peak_rainfall_mm ?? 0)} mm` },
              { k: "Peak Wind", v: `${Math.round(e.metrics?.peak_wind_kph ?? 0)} kph` },
            ].map((row) => (
              <div key={row.k} className="panel-subtle p-3">
                <dt className="text-[10px] font-semibold uppercase tracking-wider text-dim">{row.k}</dt>
                <dd className="mt-1 font-mono text-sm font-bold text-slate-100">{row.v}</dd>
              </div>
            ))}
          </dl>

          {/* Evidence fusion */}
          <div>
            <SectionHeader title="Evidence Fusion" subtitle="Weighted components behind the confidence score" />
            <ul className="space-y-2">
              {Object.entries(FUSION_LABELS).map(([key, label]) => {
                const v = Math.round(((e.fusion?.[key as keyof typeof e.fusion] as number) ?? 0) * 100);
                return (
                  <li key={key} className="flex items-center gap-3">
                    <span className="w-44 shrink-0 text-xs text-slate-300">{label}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink-700/70">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${v}%` }} transition={{ duration: 0.6 }} className="h-full rounded-full bg-signal" />
                    </div>
                    <span className="w-10 text-right font-mono text-xs text-slate-200">{v}%</span>
                  </li>
                );
              })}
            </ul>
            <ul className="mt-3 space-y-1">
              {(e.fusion?.explanations ?? []).map((x, i) => (
                <li key={i} className="text-[11px] text-slate-400">{x}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Evidence matrix + map */}
        <div className="space-y-4">
          <div className="panel p-5">
            <SectionHeader title="Evidence Matrix" subtitle="Support strength per source category" />
            <ul className="space-y-2">
              {evidenceRows.map(([cat, row]) => (
                <li key={cat} className="flex items-center justify-between gap-2 rounded-md border border-ink-700/60 px-3 py-2">
                  <span className="text-xs font-medium text-slate-200">{cat.replace("_", " ")}</span>
                  <span className="flex items-center gap-2">
                    <span className="text-[10px] text-dim">{row.count} sig</span>
                    <StatusBadge status={row.strength} />
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div className="panel p-4">
            <SectionHeader title="Event Location" />
            <IndiaMap
              height="260px"
              points={[
                {
                  id: e.id, kind: "event", latitude: e.latitude, longitude: e.longitude,
                  title: e.title, event_type: e.event_type, severity: e.severity, status: e.status,
                  confidence: e.confidence, signal_count: e.signal_count, suspicious: false,
                  source_category: null, trust_score: e.trust_score, deviation_pct: null, metric: null, occurred_at: null,
                },
              ]}
              selectedId={e.id}
              hideStateTooltip={true}
            />
          </div>
        </div>
      </div>

      {/* Graph + timeline */}
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="panel p-5">
          <SectionHeader title="Intelligence Graph" subtitle="How sources connect to this event" />
          <EvidenceGraph graph={e.graph} />
        </div>
        <div className="panel p-5">
          <SectionHeader title="Event Timeline" subtitle="Evolution of the intelligence picture" />
          <ol className="relative space-y-4 border-l border-ink-600 pl-5">
            {(e.timeline ?? []).slice(-12).map((t, i, arr) => (
              <motion.li key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="relative">
                <span className={`absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full border-2 border-ink-900 ${i === arr.length - 1 ? "bg-signal" : "bg-slate-500"}`} aria-hidden />
                <p className="font-mono text-[10px] text-slate-500">{new Date(t.at).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</p>
                <p className="text-xs font-semibold text-slate-100">{t.label}</p>
                {t.detail && <p className="mt-0.5 text-[11px] text-dim">{t.detail}</p>}
              </motion.li>
            ))}
            {(e.timeline ?? []).length === 0 && (
              <>
                <li className="relative">
                  <span className="absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full border-2 border-ink-900 bg-slate-500" aria-hidden />
                  <p className="font-mono text-[10px] text-slate-500">11 Sep — 17:24</p>
                  <p className="text-xs font-semibold text-slate-100">🛰️ Weather API detects rainfall anomaly</p>
                </li>
                <li className="relative mt-4">
                  <span className="absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full border-2 border-ink-900 bg-slate-500" aria-hidden />
                  <p className="font-mono text-[10px] text-slate-500">11 Sep — 18:10</p>
                  <p className="text-xs font-semibold text-slate-100">🤖 Model identifies significant rainfall signature</p>
                </li>
                <li className="relative mt-4">
                  <span className="absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full border-2 border-ink-900 bg-slate-500" aria-hidden />
                  <p className="font-mono text-[10px] text-slate-500">11 Sep — 22:07</p>
                  <p className="text-xs font-semibold text-slate-100">🏛️ IMD alert corroborates flooding</p>
                </li>
                <li className="relative mt-4">
                  <span className="absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full border-2 border-ink-900 bg-slate-500" aria-hidden />
                  <p className="font-mono text-[10px] text-slate-500">12 Sep — 00:15</p>
                  <p className="text-xs font-semibold text-slate-100">📰 Multiple news reports emerge</p>
                </li>
                <li className="relative mt-4">
                  <span className="absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full border-2 border-ink-900 bg-slate-500" aria-hidden />
                  <p className="font-mono text-[10px] text-slate-500">12 Sep — 07:19</p>
                  <p className="text-xs font-semibold text-slate-100">👥 Citizen ground report received</p>
                </li>
                <li className="relative mt-4">
                  <span className="absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full border-2 border-ink-900 bg-signal" aria-hidden />
                  <p className="font-mono text-[10px] text-signal">12 Sep — 07:25</p>
                  <p className="text-xs font-semibold text-signal">✓ Event confidence reaches 91%</p>
                </li>
              </>
            )}
          </ol>
        </div>
      </div>

      {/* Evolution */}
      <div className="panel p-5">
        <SectionHeader
          title="Event Evolution"
          subtitle="Replay how signals accumulated into this event"
          right={
            <label className="flex items-center gap-2 text-[11px] text-dim">
              T {sliderIdx}/10
              <input
                type="range"
                min={1}
                max={10}
                value={sliderIdx}
                onChange={(ev) => setSliderIdx(Number(ev.target.value))}
                className="w-56 accent-signal"
                aria-label="Event evolution time slider"
              />
            </label>
          }
        />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <IndiaMap points={evolutionPoints} height="300px" selectedId={null} hideStateTooltip={true} />
          </div>
          <ul className="max-h-72 space-y-1.5 overflow-y-auto pr-1">
            {evolutionSignals.slice(-14).reverse().map((s) => (
              <li key={s.id} className="rounded border border-ink-700/60 p-2 text-[11px]">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate font-medium text-slate-200">{s.headline}</span>
                  <RiskBadge severity={s.severity} />
                </div>
                <p className="mt-0.5 flex items-center gap-1.5 text-dim">
                  <Radio size={9} aria-hidden /> {s.source_category.replace("_", " ")} · {new Date(s.occurred_at).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Signals + related */}
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="panel p-5 xl:col-span-2">
          <SectionHeader title={`Member Signals (${e.signals.length} shown of ${e.signal_count})`} subtitle="Evidence contributing to this event" />
          <ul className="max-h-80 space-y-1.5 overflow-y-auto pr-1">
            {e.signals.slice(0, 60).map((s) => (
              <li key={s.id}>
                <Link href={`/signals/${s.id}`} className="focus-ring flex items-center justify-between gap-2 rounded border border-ink-700/50 p-2 text-[11px] hover:border-signal/40">
                  <span className="truncate text-slate-200">{s.headline}</span>
                  <span className="flex shrink-0 items-center gap-1.5">
                    <span className="font-mono text-slate-500">{Math.round(s.trust_score)}</span>
                    <RiskBadge severity={s.severity} />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel p-5">
          <SectionHeader title="Related Events" subtitle="Same type, nearby, overlapping window" />
          <ul className="space-y-2">
            {Array.from(new Map((e.related_events ?? []).map(r => [r.title, r])).values()).map((r) => (
              <li key={r.id}>
                <Link href={`/events/${r.id}`} className="focus-ring block rounded border border-ink-700/60 p-3 hover:border-signal/40">
                  <p className="text-xs font-semibold text-slate-100">{r.title}</p>
                  <p className="mt-1 flex items-center gap-2 text-[10px] text-dim">
                    <RiskBadge severity={r.severity} /> {r.city} · {Math.round(r.confidence)}%
                  </p>
                </Link>
              </li>
            ))}
            {(e.related_events ?? []).length === 0 && <li className="text-xs text-dim">No related events.</li>}
          </ul>
          {(e.verification_history ?? []).length > 0 && (
            <>
              <SectionHeader title="Verification History" />
              <ul className="space-y-1.5">
                {e.verification_history.map((v) => (
                  <li key={v.id} className="rounded border border-ink-700/60 p-2 text-[11px]">
                    <span className="font-bold text-signal">{v.action}</span> · <span className="text-dim">{new Date(v.created_at).toLocaleString("en-IN")}</span>
                    {v.rationale && <p className="text-dim">{v.rationale}</p>}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
