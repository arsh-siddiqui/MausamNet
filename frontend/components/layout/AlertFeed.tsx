"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { RealtimeAlert, subscribeAlerts } from "@/hooks/useRealtime";

/** Bottom-right realtime toast feed fed by the SSE stream. */
export function AlertFeed() {
  const [items, setItems] = useState<RealtimeAlert[]>([]);

  useEffect(
    () =>
      subscribeAlerts((a) => {
        setItems((prev) => [a, ...prev].slice(0, 4));
        setTimeout(() => setItems((prev) => prev.filter((i) => i.id !== a.id)), 6000);
      }),
    []
  );

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[90] flex w-80 flex-col gap-2" aria-live="polite">
      <AnimatePresence>
        {items.map((a) => (
          <motion.div
            key={a.id}
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 40 }}
            className="pointer-events-auto rounded-lg border border-signal/30 bg-ink-850/95 p-3 shadow-2xl"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-signal">
                  <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-signal" aria-hidden /> {a.type.replace(/_/g, " ")}
                </p>
                <p className="mt-0.5 truncate text-xs font-semibold text-slate-100">{a.title}</p>
                <p className="truncate text-[11px] text-dim">{a.message}</p>
              </div>
              <button
                onClick={() => setItems((prev) => prev.filter((i) => i.id !== a.id))}
                className="focus-ring rounded p-1 text-slate-500 hover:text-slate-200"
                aria-label="Dismiss alert"
              >
                <X size={12} aria-hidden />
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
