"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Database, Landmark, Newspaper, Users, Wifi, Globe2 } from "lucide-react";
import { api } from "@/lib/api";
import { Source } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { StatusBadge } from "@/components/badges";
import { ErrorState, LoadingState, SectionHeader } from "@/components/primitives";
import { useAuth } from "@/app/providers";

const CATEGORY_META: Record<string, { icon: typeof Database; desc: string; future: string }> = {
  GOVERNMENT: { icon: Landmark, desc: "Official meteorological bulletins (IMD).", future: "IMD API / data.gov.in feeds with API key." },
  WEATHER_API: { icon: Globe2, desc: "Commercial & open weather model APIs.", future: "OpenWeather /IMD AWS: set WEATHER_API_URL + KEY." },
  PUBLIC_DATASET: { icon: Database, desc: "Open sensor & station datasets.", future: "MOSDAC satellite, IMD gridded observations." },
  NEWS: { icon: Newspaper, desc: "News monitoring for impact signals.", future: "NewsAPI/GDELT connectors with NEWS_API_KEY." },
  SOCIAL: { icon: Users, desc: "Clustered social platform signals.", future: "X/Reddit firehose adapters (SOCIAL_API_*)." },
  CITIZEN: { icon: Activity, desc: "Ground evidence form submissions.", future: "IVR/WhatsApp bot intake for wider reach." },
};

interface SourceHealth {
  id: string;
  name: string;
  category: string;
  mode: string;
  status: string;
  health_check: string;
}

export default function SourcesPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [health, setHealth] = useState<Record<string, string>>({});

  const sources = useQuery<Source[]>({ queryKey: ["sources"], queryFn: () => api.get<Source[]>("/sources") });
  const healthQuery = useQuery<SourceHealth[]>({ queryKey: ["sources-health"], queryFn: () => api.get<SourceHealth[]>("/sources/health"), refetchInterval: 30_000 });

  const setMode = useMutation({
    mutationFn: (vars: { id: string; mode: string }) => api.post(`/sources/${vars.id}/mode`, { mode: vars.mode }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  const runProbe = async () => {
    const rows = (healthQuery.data ?? []).slice();
    const next: Record<string, string> = {};
    for (const r of rows) next[r.id] = r.health_check;
    setHealth(next);
  };

  if (sources.isLoading) return <LoadingState label="Loading connector registry…" />;
  if (sources.isError) return <ErrorState message="Connector registry unavailable." onRetry={() => sources.refetch()} />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Data Source Center</h1>
          <p className="mt-0.5 text-xs text-dim">Pluggable connector layer — every source implements connect / fetch / normalize / health_check.</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={runProbe} className="focus-ring rounded-md border border-ink-600 px-3 py-2 text-xs font-semibold text-slate-200 hover:border-signal">
            Run Health Probe
          </button>
          <DemoBadge compact />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {(sources.data ?? []).map((s) => {
          const meta = CATEGORY_META[s.category] ?? CATEGORY_META.SOCIAL;
          const Icon = meta.icon;
          const hc = (healthQuery.data ?? []).find((h) => h.id === s.id);
          return (
            <div key={s.id} className="panel p-5">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-signal/10">
                    <Icon size={18} className="text-signal" aria-hidden />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-100">{s.name}</p>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-dim">{s.category.replace("_", " ")}</p>
                  </div>
                </div>
                <StatusBadge status={hc?.status ?? s.status} />
              </div>

              <div className="mt-3 flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-bold text-amber-400">
                  <Wifi size={9} aria-hidden /> {s.mode === "LIVE" ? "LIVE CONNECTOR" : "DEMO CONNECTOR"}
                </span>
                <span className="font-mono text-[10px] text-slate-500">{hc?.health_check ?? "—"}</span>
              </div>

              <dl className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                <div><dt className="text-dim">Last Sync</dt><dd className="font-mono text-slate-200">{s.last_sync_at ? new Date(s.last_sync_at).toLocaleTimeString("en-IN") : "awaiting"}</dd></div>
                <div><dt className="text-dim">Signals/day</dt><dd className="font-mono text-slate-200">{s.signals_per_day.toLocaleString("en-IN")}</dd></div>
                <div><dt className="text-dim">Reliability</dt><dd className="font-mono text-green-400">{Math.round(s.reliability * 100)}%</dd></div>
                <div><dt className="text-dim">Latency</dt><dd className="font-mono text-slate-200">{s.latency_ms} ms</dd></div>
              </dl>

              <p className="mt-3 text-[10px] leading-relaxed text-dim">
                <b className="text-slate-400">Future:</b> {meta.future}
              </p>

              {user?.role === "ADMIN" && (
                <div className="mt-3 flex gap-1.5">
                  {["DEMO", "LIVE"].map((m) => (
                    <button
                      key={m}
                      onClick={() => setMode.mutate({ id: s.id, mode: m })}
                      disabled={setMode.isPending || s.mode === m}
                      className={`focus-ring flex-1 rounded border px-2 py-1.5 text-[10px] font-bold transition disabled:opacity-50 ${
                        s.mode === m ? "border-signal/50 bg-signal/10 text-signal" : "border-ink-600 text-slate-400 hover:border-signal hover:text-signal"
                      }`}
                      title={m === "LIVE" ? "Reserved for when real API credentials are configured" : "Prototype simulated mode"}
                    >
                      {m === "LIVE" ? "Switch to LIVE (needs keys)" : "DEMO mode"}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="panel p-5">
        <SectionHeader title="Connector Architecture" subtitle="How real integrations plug in later" />
        <div className="grid gap-3 text-xs sm:grid-cols-4">
          {[
            { t: "connect()", d: "Authenticate / open session with credentials from env." },
            { t: "fetch()", d: "Pull raw payloads on a schedule or webhook." },
            { t: "normalize()", d: "Map vendor schema → MausamNet signal schema." },
            { t: "health_check()", d: "Status + latency surfaced on this page." },
          ].map((x) => (
            <div key={x.t} className="panel-subtle p-3">
              <p className="font-mono font-bold text-signal">{x.t}</p>
              <p className="mt-1 text-[11px] text-dim">{x.d}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
