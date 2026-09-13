"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Command, MapPin, Radar, Radio, Database } from "lucide-react";
import { api } from "@/lib/api";
import { SearchResults } from "@/types";

/** Global search palette (Ctrl+K) — events, signals, sources, locations. */
export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(q.trim()), 250);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    if (open) {
      setQ("");
      setDebounced("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const { data, isFetching } = useQuery<SearchResults>({
    queryKey: ["palette", debounced],
    queryFn: () => api.get<SearchResults>(`/search?q=${encodeURIComponent(debounced)}`),
    enabled: open && debounced.length >= 2,
  });

  const go = (href: string) => {
    onClose();
    router.push(href);
  };

  const groups = useMemo(() => {
    if (!data) return [];
    return [
      { label: "Events", icon: Radar, items: data.events.map((e) => ({ id: e.id, title: e.title, sub: `${e.city}, ${e.state} · ${e.status}`, href: `/events/${e.id}` })) },
      { label: "Signals", icon: Radio, items: data.signals.map((s) => ({ id: s.id, title: s.headline, sub: `${s.source_category} · ${s.city}`, href: `/signals/${s.id}` })) },
      { label: "Sources", icon: Database, items: data.sources.map((s) => ({ id: s.id, title: s.name, sub: s.category, href: "/sources" })) },
      { label: "Locations", icon: MapPin, items: data.locations.map((l) => ({ id: `${l.city}-${l.state}`, title: l.label, sub: "Jump to live map", href: "/live-map" })) },
    ].filter((g) => g.items.length > 0);
  }, [data]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-start justify-center bg-black/60 p-4 pt-[12vh]"
          onClick={onClose}
          role="dialog"
          aria-modal="true"
          aria-label="Command palette"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.98, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -8 }}
            className="w-full max-w-xl overflow-hidden rounded-xl border border-ink-600 bg-ink-850 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 border-b border-ink-700 px-4 py-3">
              <Command size={16} className="text-signal" aria-hidden />
              <input
                ref={inputRef}
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") onClose();
                  if (e.key === "Enter" && groups[0]?.items[0]) go(groups[0].items[0].href);
                }}
                placeholder="Search event ID, signal ID, city, state, source…"
                className="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
                aria-label="Search query"
              />
              {isFetching && <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-signal border-t-transparent" aria-hidden />}
              <kbd className="rounded border border-ink-600 px-1 font-mono text-[10px] text-slate-500">ESC</kbd>
            </div>
            <div className="max-h-[50vh] overflow-y-auto p-2">
              {debounced.length < 2 && <p className="px-3 py-6 text-center text-xs text-dim">Type at least 2 characters — try “Mumbai”, “flood”, or a signal ID.</p>}
              {debounced.length >= 2 && groups.length === 0 && !isFetching && (
                <p className="px-3 py-6 text-center text-xs text-dim">No matching events, signals or sources.</p>
              )}
              {groups.map((g) => (
                <div key={g.label} className="mb-2">
                  <p className="px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-500">{g.label}</p>
                  <ul>
                    {g.items.map((item) => {
                      const Icon = g.icon;
                      return (
                        <li key={item.id}>
                          <button
                            onClick={() => go(item.href)}
                            className="focus-ring flex w-full items-center gap-3 rounded-md px-3 py-2 text-left hover:bg-ink-700/60"
                          >
                            <Icon size={14} className="shrink-0 text-signal" aria-hidden />
                            <span className="min-w-0 flex-1">
                              <span className="block truncate text-[13px] font-medium text-slate-200">{item.title}</span>
                              <span className="block truncate text-[11px] text-dim">{item.sub}</span>
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
