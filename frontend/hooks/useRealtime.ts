"use client";

/** Realtime SSE hook: connects once per authenticated session, feeds
 * TanStack Query invalidation, toast notifications and the simulation store. */
import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getToken, REALTIME_URL } from "@/lib/api";
import { useSimulationStore } from "@/stores/simulation";

export interface RealtimeAlert {
  id: string;
  type: string;
  title: string;
  message: string;
  at: string;
}

type Listener = (a: RealtimeAlert) => void;

const listeners = new Set<Listener>();

export function subscribeAlerts(fn: Listener) {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

export function useRealtime(enabled: boolean) {
  const queryClient = useQueryClient();
  const setStatus = useSimulationStore((s) => s.setStatus);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) return;
    const token = getToken();
    const url = `${REALTIME_URL}/api/realtime/events${token ? `?token=${encodeURIComponent(token)}` : ""}`;
    const es = new EventSource(url);
    esRef.current = es;

    const invalidate = (...keys: string[]) => {
      keys.forEach((k) => queryClient.invalidateQueries({ queryKey: [k] }));
    };

    es.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data) as { type: string; payload: Record<string, unknown> };
        switch (msg.type) {
          case "new_signal":
            invalidate("signals", "dashboard", "map", "recent-signals");
            break;
          case "event_created":
          case "event_updated":
            invalidate("events", "dashboard", "map", "event", "verification-queue");
            if (msg.payload?.title) {
              const a: RealtimeAlert = {
                id: `ev-${msg.payload.id}-${Date.now()}`,
                type: "EVENT_UPDATED",
                title: String(msg.payload.title),
                message: `Confidence ${Math.round(Number(msg.payload.confidence ?? 0))}% · ${msg.payload.signal_count ?? "?"} signals`,
                at: new Date().toISOString(),
              };
              listeners.forEach((fn) => fn(a));
            }
            break;
          case "event_verified":
            invalidate("events", "dashboard", "analytics");
            break;
          case "verification_updated":
            invalidate("events", "verification-queue", "dashboard");
            break;
          case "alert_created":
            invalidate("alerts");
            if (msg.payload?.title) {
              listeners.forEach((fn) =>
                fn({
                  id: `al-${Date.now()}`,
                  type: "ALERT",
                  title: String(msg.payload.title),
                  message: String(msg.payload.message ?? ""),
                  at: new Date().toISOString(),
                })
              );
            }
            break;
          case "simulation_update":
            setStatus(msg.payload as never);
            break;
          case "dashboard_update":
            invalidate("dashboard", "analytics");
            break;
          case "anomaly_update":
            invalidate("anomalies", "map");
            break;
          default:
            break;
        }
      } catch {
        /* ignore malformed frames */
      }
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [enabled, queryClient, setStatus]);
}
