"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSimulationStore } from "@/stores/simulation";
import { SimulationStatus } from "@/types";

export function useSimulationStatus() {
  return useQuery<SimulationStatus>({
    queryKey: ["simulation-status"],
    queryFn: () => api.get<SimulationStatus>("/simulation/status"),
    refetchInterval: 20_000,
  });
}

export function useSimulationControls() {
  const qc = useQueryClient();
  const invalidate = () => {
    ["simulation-status", "simulation", "dashboard", "events", "signals", "map", "analytics", "alerts"].forEach((k) =>
      qc.invalidateQueries({ queryKey: [k] })
    );
  };

  const start = useMutation({
    mutationFn: (vars: { speed?: number; scenario?: string }) =>
      api.post<SimulationStatus>("/simulation/start", { speed: vars.speed ?? 1, scenario: vars.scenario ?? "general" }),
    onSuccess: (s) => {
      useSimulationStore.getState().setStatus(s);
      invalidate();
    },
  });
  const pause = useMutation({
    mutationFn: () => api.post<SimulationStatus>("/simulation/pause"),
    onSuccess: (s) => {
      useSimulationStore.getState().setStatus(s);
      invalidate();
    },
  });
  const reset = useMutation({
    mutationFn: () => api.post<SimulationStatus>("/simulation/reset"),
    onSuccess: (s) => {
      useSimulationStore.getState().setStatus(s);
      invalidate();
    },
  });
  return { start, pause, reset };
}
