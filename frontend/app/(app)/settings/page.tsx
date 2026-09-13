"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/app/providers";
import { DemoBadge } from "@/components/DemoBadge";
import { ErrorState, LoadingState, SectionHeader } from "@/components/primitives";

interface SettingsShape {
  trust_weights: Record<string, number>;
  risk_thresholds: Record<string, number>;
  simulation_speed: number;
  source_modes: Record<string, string>;
}

const TABS = ["Profile", "Notifications", "Display", "Trust Engine", "Simulation", "System"] as const;

const TRUST_WEIGHT_LABELS: Record<string, string> = {
  source_reliability: "Source reliability",
  text_evidence: "Text evidence",
  media_evidence: "Media evidence",
  location_consistency: "Location consistency",
  time_consistency: "Time consistency",
  weather_evidence: "Weather evidence",
  cross_source_agreement: "Cross-source agreement",
  duplicate_penalty: "Duplicate penalty",
};

export default function SettingsPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [tab, setTab] = useState<(typeof TABS)[number]>("Profile");
  const [draft, setDraft] = useState<SettingsShape | null>(null);
  const [saved, setSaved] = useState("");

  const settings = useQuery<SettingsShape>({
    queryKey: ["settings"],
    queryFn: () => api.get<SettingsShape>("/settings"),
  });

  useEffect(() => {
    if (settings.data && !draft) setDraft(settings.data);
  }, [settings.data, draft]);

  const save = useMutation({
    mutationFn: (payload: Partial<SettingsShape>) => api.put<SettingsShape>("/settings", payload),
    onSuccess: (d) => {
      setDraft(d);
      qc.invalidateQueries({ queryKey: ["settings"] });
      setSaved("Saved — engine behavior updated for future evaluations.");
      setTimeout(() => setSaved(""), 3000);
    },
  });

  const isAdmin = user?.role === "ADMIN";
  if (settings.isLoading || !draft) return <LoadingState label="Loading settings…" />;
  if (settings.isError) return <ErrorState message="Settings unavailable." onRetry={() => settings.refetch()} />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Settings</h1>
          <p className="mt-0.5 text-xs text-dim">Profile, display and engine configuration. Admin-only fields are enforced server-side.</p>
        </div>
        <DemoBadge compact />
      </div>

      <div className="panel flex flex-wrap gap-1 p-1.5" role="tablist" aria-label="Settings sections">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            role="tab"
            aria-selected={tab === t}
            className={`focus-ring rounded-md px-3.5 py-2 text-xs font-semibold ${tab === t ? "bg-signal/15 text-signal" : "text-slate-400 hover:bg-ink-700/50"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Profile" && (
        <div className="panel max-w-xl p-5">
          <SectionHeader title="Profile" />
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-ink-700/50 pb-2"><dt className="text-dim">Full name</dt><dd className="font-semibold text-slate-100">{user?.full_name}</dd></div>
            <div className="flex justify-between border-b border-ink-700/50 pb-2"><dt className="text-dim">Email</dt><dd className="font-mono text-xs text-slate-100">{user?.email}</dd></div>
            <div className="flex justify-between border-b border-ink-700/50 pb-2"><dt className="text-dim">Organization</dt><dd className="text-slate-100">{user?.organization || "—"}</dd></div>
            <div className="flex justify-between"><dt className="text-dim">Role</dt><dd className="font-bold text-signal">{user?.role}</dd></div>
          </dl>
        </div>
      )}

      {tab === "Notifications" && (
        <div className="panel max-w-xl p-5">
          <SectionHeader title="Notifications" subtitle="Prototype: all alert types are enabled globally" />
          <ul className="space-y-2 text-sm text-slate-300">
            {["High-risk event", "Suspicious signal", "Duplicate found", "New verification task", "Event verified", "Data source degraded"].map((n) => (
              <li key={n} className="flex items-center justify-between rounded border border-ink-700/60 px-3 py-2">
                {n}
                <span className="rounded bg-green-500/10 px-1.5 py-0.5 text-[10px] font-bold text-green-400">ENABLED</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {tab === "Display" && (
        <div className="panel max-w-xl p-5">
          <SectionHeader title="Display" subtitle="Theme persists to localStorage" />
          <p className="text-xs text-dim">Use the sun/moon toggle in the top bar. Dark command-center theme is default; light mode restyles panels, tables, charts and the map popups.</p>
        </div>
      )}

      {tab === "Trust Engine" && (
        <div className="panel max-w-2xl p-5">
          <SectionHeader
            title="Trust Engine Weights"
            subtitle={isAdmin ? "Component weights for WeatherTrust scoring (0–1)" : "Admin-only — read only"}
          />
          <div className="space-y-3">
            {Object.entries(draft.trust_weights).map(([k, v]) => (
              <div key={k} className="flex items-center gap-3">
                <label htmlFor={`tw-${k}`} className="w-52 text-xs text-slate-300">{TRUST_WEIGHT_LABELS[k] ?? k}</label>
                <input
                  id={`tw-${k}`}
                  type="range"
                  min={0}
                  max={0.5}
                  step={0.01}
                  value={v}
                  disabled={!isAdmin}
                  onChange={(e) => setDraft({ ...draft, trust_weights: { ...draft.trust_weights, [k]: Number(e.target.value) } })}
                  className="flex-1 accent-signal"
                />
                <span className="w-12 text-right font-mono text-xs text-slate-200">{v.toFixed(2)}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[10px] text-slate-500">
            Duplicate threshold: <b>{draft.risk_thresholds.duplicate_threshold}</b> · suspicious below trust <b>{draft.risk_thresholds.suspicious_trust_below}</b> · high confidence <b>{draft.risk_thresholds.high_confidence}</b>
          </p>
          {isAdmin && (
            <button
              onClick={() => save.mutate({ trust_weights: draft.trust_weights })}
              disabled={save.isPending}
              className="focus-ring mt-4 flex items-center gap-2 rounded-lg bg-signal px-4 py-2 text-xs font-bold text-ink-950 hover:bg-signal-dim disabled:opacity-60"
            >
              <Save size={13} aria-hidden /> Save Trust Weights
            </button>
          )}
        </div>
      )}

      {tab === "Simulation" && (
        <div className="panel max-w-xl p-5">
          <SectionHeader title="Simulation" subtitle={isAdmin ? "Default speed applied on next start" : "Admin-only — read only"} />
          <div className="flex items-center gap-3">
            <label htmlFor="sim-speed" className="w-40 text-xs text-slate-300">Default speed</label>
            <input
              id="sim-speed"
              type="range"
              min={0.5}
              max={5}
              step={0.5}
              value={draft.simulation_speed}
              disabled={!isAdmin}
              onChange={(e) => setDraft({ ...draft, simulation_speed: Number(e.target.value) })}
              className="flex-1 accent-signal"
            />
            <span className="w-10 text-right font-mono text-xs text-slate-200">{draft.simulation_speed}x</span>
          </div>
          {isAdmin && (
            <button
              onClick={() => save.mutate({ simulation_speed: draft.simulation_speed })}
              disabled={save.isPending}
              className="focus-ring mt-4 flex items-center gap-2 rounded-lg bg-signal px-4 py-2 text-xs font-bold text-ink-950 hover:bg-signal-dim disabled:opacity-60"
            >
              <Save size={13} aria-hidden /> Save
            </button>
          )}
        </div>
      )}

      {tab === "System" && (
        <div className="panel max-w-2xl p-5">
          <SectionHeader title="System" subtitle="Security posture of the prototype" />
          <ul className="space-y-2 text-xs text-slate-300">
            {[
              "Passwords hashed with bcrypt (cost 12) — never stored in plain text.",
              "JWT access + refresh tokens (HS256); tokens never exposed in UI storage beyond localStorage in this prototype.",
              "Role-based authorization enforced server-side on every mutating route.",
              "Request validation via Pydantic; upload type/size limits on media forensics.",
              "Rate limiting on auth + submission endpoints (per-process, swap for Redis in production).",
              "Audit log for register/login/verification/settings actions.",
              "Secrets stay in environment configuration — the UI never exposes API keys.",
            ].map((x) => (
              <li key={x} className="flex gap-2 rounded border border-ink-700/60 px-3 py-2">
                <span className="text-green-400" aria-hidden>✓</span> {x}
              </li>
            ))}
          </ul>
        </div>
      )}

      {saved && (
        <div className="fixed bottom-5 left-1/2 z-[95] -translate-x-1/2 rounded-lg border border-green-500/40 bg-ink-850 px-4 py-2.5 text-xs font-semibold text-green-300 shadow-2xl" role="status">
          {saved}
        </div>
      )}
    </div>
  );
}
