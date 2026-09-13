"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Bell, LogOut, Moon, Search, Sun, Zap } from "lucide-react";
import { api, User } from "@/lib/api";
import { useTheme } from "@/app/providers";
import { DemoBadge } from "@/components/DemoBadge";
import { AlertsPage, Alert } from "@/types";
import { RiskBadge } from "@/components/badges";
import { useSimulationControls } from "@/hooks/useSimulation";

export function TopNavigation({ onOpenSearch, user }: { onOpenSearch: () => void; user: User | null }) {
  const { theme, toggle } = useTheme();
  const qc = useQueryClient();
  const [openBell, setOpenBell] = useState(false);
  const [openProfile, setOpenProfile] = useState(false);

  const alerts = useQuery<AlertsPage>({
    queryKey: ["alerts"],
    queryFn: () => api.get<AlertsPage>("/alerts?page_size=12"),
    refetchInterval: 30_000,
  });
  const unread = (alerts.data?.items ?? []).filter((a: Alert) => !a.read_at).length;

  const { start, pause } = useSimulationControls();
  const sim = useQuery<{ running: boolean }>({ queryKey: ["simulation-status"] });

  useEffect(() => {
    const close = () => {
      setOpenBell(false);
      setOpenProfile(false);
    };
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, []);

  const markAll = async () => {
    await api.post("/alerts/read-all");
    qc.invalidateQueries({ queryKey: ["alerts"] });
  };

  return (
    <header className="flex h-14 items-center gap-3 border-b border-ink-700/70 bg-ink-900/80 px-4">
      <button
        onClick={(e) => {
          e.stopPropagation();
          onOpenSearch();
        }}
        className="focus-ring flex h-9 w-72 items-center gap-2 rounded-md border border-ink-600 bg-ink-850 px-3 text-sm text-slate-500 hover:border-signal/40"
        aria-label="Open command palette search (Ctrl+K)"
      >
        <Search size={14} aria-hidden />
        <span className="flex-1 text-left">Search events, signals, cities…</span>
        <kbd className="rounded border border-ink-600 px-1 font-mono text-[10px]">Ctrl K</kbd>
      </button>

      <div className="ml-auto flex items-center gap-2">
        <DemoBadge compact />

        {/* Simulation quick controls */}
        <div className="hidden items-center gap-1 rounded-md border border-ink-600 bg-ink-850 px-1.5 py-1 md:flex" title="Live intelligence simulation">
          <Zap size={13} className={sim.data?.running ? "text-amber-400" : "text-slate-500"} aria-hidden />
          {sim.data?.running ? (
            <button onClick={() => pause.mutate()} className="focus-ring rounded px-1.5 text-[11px] font-semibold text-slate-300 hover:text-signal">
              PAUSE SIM
            </button>
          ) : (
            <button onClick={() => start.mutate({ speed: 1 })} className="focus-ring rounded px-1.5 text-[11px] font-semibold text-slate-300 hover:text-signal">
              START SIM
            </button>
          )}
        </div>

        {/* Notifications */}
        <div className="relative" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => setOpenBell((v) => !v)}
            className="focus-ring relative flex h-9 w-9 items-center justify-center rounded-md border border-ink-600 bg-ink-850 text-slate-300 hover:border-signal/40"
            aria-label={`Notifications (${unread} unread)`}
          >
            <Bell size={15} aria-hidden />
            {unread > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-0.5 text-[9px] font-bold text-white">
                {unread > 9 ? "9+" : unread}
              </span>
            )}
          </button>
          <AnimatePresence>
            {openBell && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="absolute right-0 top-11 z-50 w-96 rounded-lg border border-ink-600 bg-ink-850 shadow-2xl"
                role="dialog"
                aria-label="Notifications"
              >
                <div className="flex items-center justify-between border-b border-ink-700 px-4 py-2.5">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-300">Notifications</p>
                  <button onClick={markAll} className="focus-ring text-[11px] font-semibold text-signal hover:underline">
                    Mark all read
                  </button>
                </div>
                <ul className="max-h-96 overflow-y-auto">
                  {(alerts.data?.items ?? []).length === 0 && (
                    <li className="px-4 py-6 text-center text-xs text-dim">No notifications yet.</li>
                  )}
                  {(alerts.data?.items ?? []).map((a) => (
                    <li key={a.id} className={`border-b border-ink-700/50 px-4 py-3 ${!a.read_at ? "bg-signal/5" : ""}`}>
                      <Link href={a.event_id ? `/events/${a.event_id}` : a.signal_id ? `/signals/${a.signal_id}` : "#"} onClick={() => setOpenBell(false)} className="block">
                        <div className="flex items-center justify-between gap-2">
                          <p className="truncate text-xs font-semibold text-slate-200">{a.title}</p>
                          <RiskBadge severity={a.severity} />
                        </div>
                        <p className="mt-0.5 line-clamp-2 text-[11px] text-dim">{a.message}</p>
                        <p className="mt-1 font-mono text-[10px] text-slate-500">{new Date(a.created_at).toLocaleString("en-IN")}</p>
                      </Link>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Theme */}
        <button
          onClick={toggle}
          className="focus-ring flex h-9 w-9 items-center justify-center rounded-md border border-ink-600 bg-ink-850 text-slate-300 hover:border-signal/40"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? <Sun size={15} aria-hidden /> : <Moon size={15} aria-hidden />}
        </button>

        {/* Profile */}
        <div className="relative" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => setOpenProfile((v) => !v)}
            className="focus-ring flex h-9 items-center gap-2 rounded-md border border-ink-600 bg-ink-850 px-2.5"
            aria-label="User profile menu"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-signal/20 text-[10px] font-bold text-signal">
              {(user?.full_name ?? "U").slice(0, 1)}
            </span>
            <span className="hidden text-xs font-semibold text-slate-200 lg:block">{user?.role ?? "—"}</span>
          </button>
          <AnimatePresence>
            {openProfile && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="absolute right-0 top-11 z-50 w-60 rounded-lg border border-ink-600 bg-ink-850 p-3 shadow-2xl"
                role="dialog"
                aria-label="Profile"
              >
                <p className="text-sm font-semibold text-slate-100">{user?.full_name}</p>
                <p className="truncate text-xs text-dim">{user?.email}</p>
                <p className="mt-1 inline-flex rounded border border-signal/40 bg-signal/10 px-1.5 py-0.5 text-[10px] font-bold text-signal">{user?.role}</p>
                <Link href="/settings" className="focus-ring mt-3 block rounded border border-ink-600 px-3 py-1.5 text-center text-xs font-semibold text-slate-200 hover:border-signal">
                  Settings
                </Link>
                <button
                  onClick={() => {
                    clearAndGo();
                  }}
                  className="focus-ring mt-2 flex w-full items-center justify-center gap-2 rounded border border-red-500/40 px-3 py-1.5 text-xs font-semibold text-red-400 hover:bg-red-500/10"
                >
                  <LogOut size={13} aria-hidden /> Sign out
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}

function clearAndGo() {
  import("@/lib/api").then(({ clearSession }) => {
    clearSession();
    window.location.href = "/login";
  });
}
