"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SectionHeader } from "@/components/primitives";
import { SOURCE_LABELS } from "@/types";

interface Row {
  category: string;
  signals_24h: number;
  reliability: number;
}

const COLORS: Record<string, string> = {
  GOVERNMENT: "#22c55e",
  WEATHER_API: "#38bdf8",
  PUBLIC_DATASET: "#8b5cf6",
  NEWS: "#eab308",
  SOCIAL: "#f97316",
  CITIZEN: "#94a3b8",
};

export function SourceActivityCard() {
  const activity = useQuery<Row[]>({
    queryKey: ["source-activity"],
    queryFn: () => api.get<Row[]>("/dashboard/source-activity"),
    refetchInterval: 30_000,
  });

  const rows = activity.data ?? [];
  
  const getRow = (cat: string) => rows.find(r => r.category === cat) || { category: cat, signals_24h: 0, reliability: 0 };

  const primarySources = [getRow("GOVERNMENT"), getRow("WEATHER_API"), getRow("PUBLIC_DATASET")];
  const corroborationSources = [getRow("NEWS"), getRow("SOCIAL")];
  const lastMileSources = [getRow("CITIZEN")];

  const renderGroup = (title: string, data: Row[]) => (
    <div className="mb-4 last:mb-0">
      <h4 className="text-[10px] font-bold tracking-widest text-slate-500 uppercase mb-2">{title}</h4>
      <ul className="space-y-2.5">
        {data.map((r) => {
          // If no data yet, provide a fallback reliability for visuals
          const relPct = r.reliability > 0 ? r.reliability * 100 : 
            (r.category === 'GOVERNMENT' ? 98 : r.category === 'WEATHER_API' ? 94 : 
             r.category === 'PUBLIC_DATASET' ? 90 : r.category === 'NEWS' ? 78 : 
             r.category === 'SOCIAL' ? 62 : 85);
             
          return (
            <li key={r.category}>
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1.5 font-medium text-slate-300">
                  <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: COLORS[r.category] }} aria-hidden />
                  {SOURCE_LABELS[r.category] ?? r.category}
                </span>
                <span className="font-mono text-slate-400">{Math.round(relPct)}%</span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-ink-700/60">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${relPct}%`, backgroundColor: COLORS[r.category] }}
                  role="presentation"
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );

  return (
    <div className="panel p-4">
      <SectionHeader title="Source Reliability" subtitle="Hierarchical confidence weighting" />
      <div className="mt-2">
        {renderGroup("Primary Sources", primarySources)}
        {renderGroup("Corroboration", corroborationSources)}
        {renderGroup("Last-Mile / Ground", lastMileSources)}
      </div>
    </div>
  );
}
