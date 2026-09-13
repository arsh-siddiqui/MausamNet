/** Simulation store — mirrored from SSE simulation_update events. */
import { create } from "zustand";
import { SimulationStatus } from "@/types";

interface SimulationStore {
  status: SimulationStatus | null;
  setStatus: (s: SimulationStatus) => void;
}

export const useSimulationStore = create<SimulationStore>((set) => ({
  status: null,
  setStatus: (s) => set({ status: s }),
}));
