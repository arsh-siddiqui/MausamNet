"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { SignalDetail } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { RiskBadge, StatusBadge } from "@/components/badges";
import { ErrorState, LoadingState, SectionHeader } from "@/components/primitives";
import { TrustScoreCard } from "@/features/signals/TrustScoreCard";

export default function SignalDetailsPage() {
  const { id } = useParams<{ id: string }>();

  const signal = useQuery<SignalDetail>({
    queryKey: ["signal", id],
    queryFn: () => api.get<SignalDetail>(`/signals/${id}`),
  });

  if (signal.isLoading) return <LoadingState label="Loading signal intelligence…" />;
  if (signal.isError) return <ErrorState message="Signal unavailable." onRetry={() => signal.refetch()} />;
  const s = signal.data!;

  return (
    <div className="space-y-5">
      <Link href="/signals" className="focus-ring inline-flex items-center gap-1.5 text-xs font-semibold text-dim hover:text-signal">
        <ArrowLeft size={13} aria-hidden /> Back to Signal Explorer
      </Link>

      {/* Header */}
      <div className="panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight">{s.headline}</h1>
              <StatusBadge status={s.status} />
              <RiskBadge severity={s.severity} />
              <DemoBadge compact />
            </div>
            <p className="mt-1 font-mono text-[11px] text-slate-500">{s.id}</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className="font-mono text-xl font-bold text-slate-100">{Math.round(s.ai_confidence * 100)}%</p>
              <p className="text-[9px] font-bold uppercase tracking-widest text-dim">AI Confidence</p>
            </div>
            {s.event_id && (
              <Link href={`/events/${s.event_id}`} className="focus-ring rounded-md bg-signal px-3 py-2 text-xs font-bold text-ink-950 hover:bg-signal-dim">
                View Member Event →
              </Link>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {/* Left column */}
        <div className="space-y-4 xl:col-span-2">
          <div className="panel p-5">
            <SectionHeader title="Original Content" subtitle={`${s.source_category.replace("_", " ")} · ingested ${new Date(s.ingested_at).toLocaleString("en-IN")}`} />
            <p className="text-sm leading-relaxed text-slate-200">{s.headline}</p>
            {s.content && <p className="mt-2 text-xs leading-relaxed text-dim">{s.content}</p>}
            <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { k: "Occurred", v: new Date(s.occurred_at).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) },
                { k: "Location", v: `${s.city}, ${s.state}` },
                { k: "Coordinates", v: `${s.latitude.toFixed(2)}, ${s.longitude.toFixed(2)}` },
                { k: "AI Label", v: s.ai_label || s.event_type },
              ].map((r) => (
                <div key={r.k} className="panel-subtle p-3">
                  <dt className="text-[10px] font-semibold uppercase tracking-wider text-dim">{r.k}</dt>
                  <dd className="mt-1 text-xs font-semibold text-slate-100">{r.v}</dd>
                </div>
              ))}
            </dl>
            {Object.keys(s.metrics ?? {}).length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {Object.entries(s.metrics).map(([k, v]) => (
                  <span key={k} className="rounded border border-ink-600 bg-ink-850 px-2 py-1 font-mono text-[10px] text-slate-300">
                    {k}: <b className="text-signal">{String(v)}</b>
                  </span>
                ))}
              </div>
            )}
            {s.media_url && (
              <div className="mt-3 rounded-md border border-ink-600 p-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-dim">Attached Media (simulated)</p>
                <p className="mt-1 break-all font-mono text-[11px] text-signal">{s.media_url}</p>
                <Link href="/media-forensics" className="mt-2 inline-block text-[11px] font-semibold text-signal hover:underline">
                  Run media forensics →
                </Link>
              </div>
            )}
          </div>

          {/* Explainability */}
          <div className="panel p-5">
            <SectionHeader title="Why this score?" subtitle="Explainable AI — every factor behind the verdict" />
            <ul className="space-y-1.5">
              {(s.explanation ?? []).map((x, i) => (
                <li key={i} className="text-xs leading-relaxed text-slate-300">{x}</li>
              ))}
              {(s.explanation ?? []).length === 0 && <li className="text-xs text-dim">No explanation recorded.</li>}
            </ul>
            {s.suspicious && (s.suspicious_reasons ?? []).length > 0 && (
              <div className="mt-4 rounded-md border border-orange-500/40 bg-orange-500/10 p-3">
                <p className="text-xs font-bold uppercase tracking-wider text-orange-400">Why is this signal suspicious?</p>
                <ul className="mt-1.5 space-y-1">
                  {s.suspicious_reasons.map((r, i) => (
                    <li key={i} className="text-xs text-orange-300">⚠ {r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Related signals */}
          <div className="panel p-5">
            <SectionHeader title="Related Signals" subtitle="Same city & type within ±12h" />
            <ul className="space-y-1.5">
              {(s.related_signals ?? []).map((r) => (
                <li key={r.id}>
                  <Link href={`/signals/${r.id}`} className="focus-ring flex items-center justify-between gap-2 rounded border border-ink-700/60 p-2 text-[11px] hover:border-signal/40">
                    <span className="truncate text-slate-200">{r.headline}</span>
                    <span className="shrink-0 text-dim">{r.source_category.replace("_", " ")} · {Math.round(r.similarity * 100)}% match</span>
                  </Link>
                </li>
              ))}
              {(s.related_signals ?? []).length === 0 && <li className="text-xs text-dim">No related signals found.</li>}
            </ul>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          <TrustScoreCard
            trustScore={Math.round(s.trust_score)}
            breakdown={{
              "Location": Math.round((s.location_consistency?.score ?? 0) * 100),
              "Time": Math.round((s.time_consistency?.score ?? 0) * 100),
              "Weather": Math.round((s.weather_evidence?.score ?? 0) * 100),
            }}
          />

          <div className="panel p-5">
            <SectionHeader title="Consistency Checks" />
            <ul className="space-y-3 text-xs">
              <li>
                <div className="flex justify-between"><span className="text-slate-300">Location consistency</span><span className="font-mono text-slate-100">{Math.round((s.location_consistency?.score ?? 0) * 100)}%</span></div>
                <p className="mt-0.5 text-[10px] text-dim">
                  {s.location_consistency?.distance_from_city_center_km != null
                    ? `${s.location_consistency.distance_from_city_center_km} km from ${s.city} reference point`
                    : s.location_consistency?.note ?? "—"}
                </p>
              </li>
              <li>
                <div className="flex justify-between"><span className="text-slate-300">Time consistency</span><span className="font-mono text-slate-100">{Math.round((s.time_consistency?.score ?? 0) * 100)}%</span></div>
                <p className="mt-0.5 text-[10px] text-dim">{s.time_consistency?.age_hours?.toFixed(1) ?? "?"}h since occurrence</p>
              </li>
              <li>
                <div className="flex justify-between"><span className="text-slate-300">Weather evidence</span><span className="font-mono text-slate-100">{Math.round((s.weather_evidence?.score ?? 0) * 100)}%</span></div>
                <p className="mt-0.5 text-[10px] text-dim">{s.weather_evidence?.note ?? "—"}</p>
              </li>
              {s.duplicate_of && (
                <li className="rounded-md border border-slate-500/40 bg-slate-500/10 p-2.5">
                  <p className="font-semibold text-slate-200">Duplicate analysis</p>
                  <p className="mt-1 text-[11px] text-dim">
                    Matches signal{" "}
                    <Link href={`/signals/${s.duplicate_of}`} className="font-mono text-signal hover:underline">{s.duplicate_of.slice(0, 8)}…</Link>{" "}
                    (score {Math.round(s.duplicate_score * 100)}%)
                  </p>
                </li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
