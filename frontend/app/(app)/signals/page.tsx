"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Copy, Search } from "lucide-react";
import { api } from "@/lib/api";
import { EVENT_TYPES, EVENT_TYPE_LABELS, SEVERITIES, SignalsPage, SOURCE_CATEGORIES, SOURCE_LABELS } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { RiskBadge, StatusBadge } from "@/components/badges";
import { EmptyState, ErrorState, LoadingState } from "@/components/primitives";

export default function SignalExplorerPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [source, setSource] = useState("");
  const [eventType, setEventType] = useState("");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [suspiciousOnly, setSuspiciousOnly] = useState(searchParams.get("suspicious") === "true");
  const [sort, setSort] = useState("occurred_at");
  const [dir, setDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [copied, setCopied] = useState("");

  const onSearch = (v: string) => {
    setQ(v);
    clearTimeout((window as unknown as { __sigTimer?: number }).__sigTimer);
    (window as unknown as { __sigTimer?: number }).__sigTimer = window.setTimeout(() => {
      setDebounced(v.trim());
      setPage(1);
    }, 300);
  };

  const params = new URLSearchParams({ page: String(page), page_size: "15", sort, direction: dir });
  if (debounced) params.set("q", debounced);
  if (source) params.set("source", source);
  if (eventType) params.set("event_type", eventType);
  if (severity) params.set("severity", severity);
  if (status) params.set("status", status);
  if (suspiciousOnly) params.set("suspicious_only", "true");

  const signals = useQuery<SignalsPage>({
    queryKey: ["signals", params.toString()],
    queryFn: () => api.get<SignalsPage>(`/signals?${params.toString()}`),
    placeholderData: keepPreviousData,
    refetchInterval: 15_000,
  });

  const toggleSort = (col: string) => {
    if (sort === col) setDir((d) => (d === "desc" ? "asc" : "desc"));
    else {
      setSort(col);
      setDir("desc");
    }
  };

  const copyId = (id: string) => {
    navigator.clipboard?.writeText(id);
    setCopied(id);
    setTimeout(() => setCopied(""), 1200);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Signal Explorer</h1>
          <p className="mt-0.5 text-xs text-dim">Raw incoming intelligence before clustering — every feed, every report, every ping.</p>
        </div>
        <DemoBadge compact />
      </div>

      {/* Signal Intelligence Summary */}
      <div className="panel p-4 flex flex-wrap items-center justify-between gap-4 border-signal/20 bg-ink-900/50">
        <div>
          <h2 className="text-xs font-bold tracking-widest text-slate-500 uppercase">Signal Intelligence</h2>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-300">
          <div><span className="font-bold text-slate-100 text-sm">18,001</span> SIGNALS</div>
          <div className="h-3 w-px bg-ink-700"></div>
          <div><span className="font-bold text-orange-400 text-sm">372</span> SUSPICIOUS</div>
          <div className="h-3 w-px bg-ink-700"></div>
          <div><span className="font-bold text-sky-400 text-sm">451</span> CLUSTERED</div>
          <div className="h-3 w-px bg-ink-700"></div>
          <div><span className="font-bold text-red-400 text-sm">286</span> HIGH RISK</div>
          <div className="h-3 w-px bg-ink-700"></div>
          <div><span className="font-bold text-green-400 text-sm">439</span> VERIFIED</div>
        </div>
      </div>

      {/* Filters */}
      <div className="panel flex flex-wrap items-end gap-3 p-3">
        <div className="min-w-56 flex-1">
          <label htmlFor="sq" className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-dim">Search</label>
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-2.5 text-slate-500" aria-hidden />
            <input id="sq" className="input-base pl-8" placeholder="Headline, city, ID…" value={q} onChange={(e) => onSearch(e.target.value)} />
          </div>
        </div>
        <div>
          <label htmlFor="ssrc" className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-dim">Source</label>
          <select id="ssrc" className="input-base w-40 py-1.5" value={source} onChange={(e) => { setPage(1); setSource(e.target.value); }}>
            <option value="">All</option>
            {SOURCE_CATEGORIES.map((s) => <option key={s} value={s}>{SOURCE_LABELS[s]}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="stype" className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-dim">Event type</label>
          <select id="stype" className="input-base w-40 py-1.5" value={eventType} onChange={(e) => { setPage(1); setEventType(e.target.value); }}>
            <option value="">All</option>
            {EVENT_TYPES.map((t) => <option key={t} value={t}>{EVENT_TYPE_LABELS[t]}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="ssev" className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-dim">Severity</label>
          <select id="ssev" className="input-base w-32 py-1.5" value={severity} onChange={(e) => { setPage(1); setSeverity(e.target.value); }}>
            <option value="">All</option>
            {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="sstat" className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-dim">Status</label>
          <select id="sstat" className="input-base w-36 py-1.5" value={status} onChange={(e) => { setPage(1); setStatus(e.target.value); }}>
            <option value="">All</option>
            {["NEW", "CLASSIFIED", "SUSPICIOUS", "DUPLICATE", "VERIFIED", "REJECTED"].map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <label className="flex items-center gap-2 pb-2 text-xs text-slate-300">
          <input type="checkbox" checked={suspiciousOnly} onChange={(e) => { setPage(1); setSuspiciousOnly(e.target.checked); }} className="h-3.5 w-3.5 accent-signal" />
          Suspicious only
        </label>
      </div>

      {signals.isLoading && <LoadingState label="Loading signals…" />}
      {signals.isError && <ErrorState message="Signal feed unavailable." onRetry={() => signals.refetch()} />}
      {signals.data && signals.data.items.length === 0 && (
        <EmptyState title="No matching signals." hint="Try clearing filters — or start the live simulation." />
      )}

      {signals.data && signals.data.items.length > 0 && (
        <>
          <div className="panel overflow-x-auto">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead>
                <tr className="border-b border-ink-700/70 text-[10px] uppercase tracking-wider text-dim">
                  <th className="px-3 py-3">ID</th>
                  <th className="cursor-pointer px-3 py-3 hover:text-signal" onClick={() => toggleSort("source_category")}>Source</th>
                  <th className="px-3 py-3">Headline / Event</th>
                  <th className="px-3 py-3">Location</th>
                  <th className="cursor-pointer px-3 py-3 hover:text-signal" onClick={() => toggleSort("occurred_at")}>Timestamp</th>
                  <th className="cursor-pointer px-3 py-3 hover:text-signal" onClick={() => toggleSort("ai_confidence")}>AI Class</th>
                  <th className="cursor-pointer px-3 py-3 hover:text-signal" onClick={() => toggleSort("trust_score")}>Trust</th>
                  <th className="px-3 py-3">Flags</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {signals.data.items.map((s) => (
                  <tr 
                    key={s.id} 
                    className={`border-b border-ink-700/40 transition hover:bg-ink-800/60 cursor-pointer ${s.suspicious ? "bg-orange-500/5" : ""}`}
                    onClick={(e) => {
                      if (!(e.target as HTMLElement).closest('button') && !(e.target as HTMLElement).closest('a')) {
                        router.push(`/signals/${s.id}`);
                      }
                    }}
                  >
                    <td className="px-3 py-2.5">
                      <button onClick={(e) => { e.stopPropagation(); copyId(s.id); }} title="Copy ID" className="focus-ring flex items-center gap-1 font-mono text-[10px] text-slate-400 hover:text-signal">
                        {s.id.slice(0, 8)}… <Copy size={9} aria-hidden />
                      </button>
                      {copied === s.id && <span className="text-[9px] text-signal">copied!</span>}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-300">{SOURCE_LABELS[s.source_category] ?? s.source_category}</td>
                    <td className="max-w-[280px] px-3 py-2.5">
                      <Link href={`/signals/${s.id}`} className="focus-ring block truncate text-xs font-medium text-slate-100 hover:text-signal">{s.headline}</Link>
                      {s.event_id ? (
                        <Link href={`/events/${s.event_id}`} onClick={(e) => e.stopPropagation()} className="text-[10px] text-signal hover:underline">→ member event</Link>
                      ) : (
                        <span className="text-[10px] text-slate-600">unclustered</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-300">{s.city}</td>
                    <td className="px-3 py-2.5 font-mono text-[10px] text-dim">{new Date(s.occurred_at).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</td>
                    <td className="px-3 py-2.5">
                      <p className="text-[11px] font-semibold text-slate-200">{EVENT_TYPE_LABELS[s.event_type] ?? s.event_type}</p>
                      <p className="font-mono text-[9px] text-dim">{Math.round(s.ai_confidence * 100)}% confidence</p>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-2 text-[10px] leading-none">
                        <span className={`tracking-[2px] ${s.trust_score >= 80 ? "text-green-400" : s.trust_score >= 55 ? "text-sky-400" : "text-orange-400"}`}>
                          {"█".repeat(Math.round(s.trust_score / 10))}<span className="text-ink-700/60">{"█".repeat(10 - Math.round(s.trust_score / 10))}</span>
                        </span>
                        <span className={`font-mono font-bold ${s.trust_score >= 80 ? "text-green-400" : s.trust_score >= 55 ? "text-sky-400" : "text-orange-400"}`}>{Math.round(s.trust_score)}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      {s.duplicate_of && <StatusBadge status="DUPLICATE" />}
                      {s.suspicious && <RiskBadge severity="HIGH" className="ml-1" />}
                      {!s.duplicate_of && !s.suspicious && <span className="text-[10px] text-slate-600">—</span>}
                    </td>
                    <td className="px-3 py-2.5"><StatusBadge status={s.status} /></td>
                    <td className="px-3 py-2.5 text-right">
                      <Link href={`/signals/${s.id}`} className="focus-ring inline-flex items-center gap-1 rounded bg-ink-800 px-2 py-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-300 hover:bg-signal hover:text-ink-950 transition-colors">
                        View <ChevronRight size={12} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-xs text-dim">
              Page {signals.data.page} of {signals.data.pages} · {signals.data.total.toLocaleString("en-IN")} signals
            </p>
            <div className="flex gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="focus-ring rounded border border-ink-600 p-1.5 text-slate-300 disabled:opacity-40 hover:border-signal" aria-label="Previous page">
                <ChevronLeft size={14} aria-hidden />
              </button>
              <button onClick={() => setPage((p) => Math.min(signals.data!.pages, p + 1))} disabled={page >= signals.data.pages} className="focus-ring rounded border border-ink-600 p-1.5 text-slate-300 disabled:opacity-40 hover:border-signal" aria-label="Next page">
                <ChevronRight size={14} aria-hidden />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
