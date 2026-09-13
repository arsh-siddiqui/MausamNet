"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ClipboardCheck, Waves } from "lucide-react";
import { api } from "@/lib/api";
import { EVENT_TYPES, EVENT_TYPE_LABELS, GroundReport } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { SectionHeader } from "@/components/primitives";

const CITIES = [
  "Mumbai", "Pune", "Nagpur", "Nashik", "Delhi", "Gurugram", "Ahmedabad", "Surat", "Jaipur", "Bengaluru",
  "Hyderabad", "Chennai", "Kolkata", "Kochi", "Bhubaneswar", "Guwahati", "Lucknow", "Patna", "Srinagar",
  "Chandigarh", "Indore", "Bhopal", "Visakhapatnam", "Dehradun", "Ranchi", "Raipur", "Shimla", "Jodhpur", "Amritsar",
];

export default function GroundReportsPage() {
  const [form, setForm] = useState({ event_type: "FLOOD", description: "", city: "Mumbai", district: "", reporter_name: "" });
  const [tracking, setTracking] = useState<GroundReport | null>(null);
  const [error, setError] = useState("");

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = useMutation({
    mutationFn: () => api.post<GroundReport>("/ground-reports", { ...form, state: "" }),
    onSuccess: (data) => {
      setTracking(data);
      setForm((f) => ({ ...f, description: "" }));
      setError("");
    },
    onError: (e: Error) => setError(e.message),
  });

  const recent = useQuery<{ items: GroundReport[]; total: number }>({
    queryKey: ["ground-reports"],
    queryFn: () => api.get("/ground-reports?page_size=10"),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Ground Evidence</h1>
          <p className="mt-0.5 max-w-3xl text-xs text-dim">
            Citizen observations provide localized supporting evidence to supplement larger weather and media intelligence streams.
            They are never treated as a primary source.
          </p>
        </div>
        <DemoBadge compact />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {/* Form */}
        <div className="panel p-5">
          <SectionHeader title="Submit Observation" subtitle="Goes through the same AI pipeline as every other signal — flagged as CITIZEN category" />
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit.mutate();
            }}
            className="space-y-4"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="g-type" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Event Type</label>
                <select id="g-type" className="input-base" value={form.event_type} onChange={set("event_type")}>
                  {EVENT_TYPES.map((t) => <option key={t} value={t}>{EVENT_TYPE_LABELS[t]}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="g-city" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">City</label>
                <select id="g-city" className="input-base" value={form.city} onChange={set("city")}>
                  {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label htmlFor="g-loc" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Location Detail (area / landmark)</label>
              <input id="g-loc" className="input-base" value={form.district} onChange={set("district")} placeholder="e.g. Andheri East, near metro station" />
            </div>
            <div>
              <label htmlFor="g-desc" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Description</label>
              <textarea id="g-desc" required minLength={10} rows={4} className="input-base resize-none" value={form.description} onChange={set("description")} placeholder="Describe what you are observing: water level, visibility, damage…" />
            </div>
            <div>
              <label htmlFor="g-name" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Your Name (optional)</label>
              <input id="g-name" className="input-base" value={form.reporter_name} onChange={set("reporter_name")} placeholder="Anonymous Citizen" />
            </div>

            {error && (
              <div role="alert" className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs font-medium text-red-400">{error}</div>
            )}

            <button
              type="submit"
              disabled={submit.isPending}
              className="focus-ring flex w-full items-center justify-center gap-2 rounded-lg bg-signal px-4 py-3 text-sm font-bold text-ink-950 transition hover:bg-signal-dim disabled:opacity-60"
            >
              {submit.isPending ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-950 border-t-transparent" aria-hidden /> : <Waves size={15} aria-hidden />}
              Submit Ground Evidence
            </button>
          </form>

          {tracking && (
            <div className="mt-4 rounded-lg border border-green-500/40 bg-green-500/10 p-4" role="status">
              <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-green-400">
                <ClipboardCheck size={13} aria-hidden /> Report received
              </p>
              <p className="mt-1.5 text-sm text-slate-100">
                Tracking ID: <span className="font-mono font-bold text-green-300">{tracking.tracking_id}</span>
              </p>
              <p className="mt-1 text-[11px] text-dim">
                Your observation entered the AI pipeline as a CITIZEN signal with trust scoring, duplicate detection and optional event
                clustering. Keep this ID to check status.
              </p>
            </div>
          )}
        </div>

        {/* Context + recent */}
        <div className="space-y-4">
          <div className="panel p-5">
            <SectionHeader title="How ground evidence is used" />
            <ul className="space-y-2 text-xs leading-relaxed text-slate-300">
              <li>1 · Weighted <b>lowest</b> of all six source categories in evidence fusion.</li>
              <li>2 · Cross-checked against weather observations — claims that contradict sensor data are flagged.</li>
              <li>3 · Helpful to confirm impacts (water depth, visibility) inside events already detected from authoritative sources.</li>
              <li>4 · Never triggers public warnings by itself.</li>
            </ul>
          </div>
          <div className="panel p-5">
            <SectionHeader title="Recent Submissions" subtitle={`${recent.data?.total ?? 0} total in prototype database`} />
            <ul className="max-h-72 space-y-1.5 overflow-y-auto pr-1">
              {(recent.data?.items ?? []).map((r) => (
                <li key={r.id} className="rounded border border-ink-700/60 p-2.5 text-[11px]">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono font-bold text-signal">{r.tracking_id}</span>
                    <span className="text-dim">{r.city} · {EVENT_TYPE_LABELS[r.event_type] ?? r.event_type}</span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-slate-300">{r.description}</p>
                  <p className="mt-1 text-dim">{new Date(r.created_at).toLocaleString("en-IN")} · status {r.status}</p>
                </li>
              ))}
              {(recent.data?.items ?? []).length === 0 && <li className="py-4 text-center text-xs text-dim">No ground reports yet.</li>}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
