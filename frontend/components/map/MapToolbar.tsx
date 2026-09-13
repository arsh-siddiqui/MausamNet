import React from "react";
import { Layers, Droplets, Activity, Maximize2, Map } from "lucide-react";

export interface LayerState {
  events: boolean;
  risk: boolean;
  rainfall: boolean;
  signals: boolean;
  anomalies: boolean;
}

export function MapToolbar({
  layers,
  onToggleLayer,
  onFullscreen,
  onResetView,
}: {
  layers: LayerState;
  onToggleLayer: (layer: keyof LayerState) => void;
  onFullscreen: () => void;
  onResetView: () => void;
}) {
  const Toggle = ({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) => (
    <button
      onClick={onClick}
      className={`focus-ring flex items-center gap-2 rounded-md border px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider transition-colors ${
        active ? "border-signal/50 bg-signal/15 text-signal" : "border-ink-700/60 text-slate-400 hover:border-ink-600 hover:text-slate-300"
      }`}
      aria-pressed={active}
    >
      {icon}
      {label}
    </button>
  );

  return (
    <div className="absolute left-4 top-4 z-[1000] flex flex-col gap-2">
      <div className="flex gap-2 rounded-lg border border-ink-700/60 bg-ink-950/90 p-2 shadow-xl backdrop-blur-md">
        <Toggle active={layers.events} onClick={() => onToggleLayer("events")} icon={<Layers size={14} />} label="Events" />
        <Toggle active={layers.risk} onClick={() => onToggleLayer("risk")} icon={<Activity size={14} />} label="Risk Zones" />
        <Toggle active={layers.rainfall} onClick={() => onToggleLayer("rainfall")} icon={<Droplets size={14} />} label="Rainfall" />
        <Toggle active={layers.signals} onClick={() => onToggleLayer("signals")} icon={<span className="text-[14px]">📡</span>} label="Signals" />
        <Toggle active={layers.anomalies} onClick={() => onToggleLayer("anomalies")} icon={<span className="text-[14px]">✨</span>} label="Anomalies" />
      </div>
      <div className="flex gap-2">
        <button
          onClick={onResetView}
          className="focus-ring flex items-center justify-center gap-1.5 rounded-md border border-ink-700/60 bg-ink-950/90 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 shadow-md backdrop-blur-md hover:border-ink-600 hover:text-slate-300"
          aria-label="Reset view to India"
        >
          <Map size={13} />
          Reset View
        </button>
        <button
          onClick={onFullscreen}
          className="focus-ring flex items-center justify-center gap-1.5 rounded-md border border-ink-700/60 bg-ink-950/90 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 shadow-md backdrop-blur-md hover:border-ink-600 hover:text-slate-300"
          aria-label="Toggle Fullscreen"
        >
          <Maximize2 size={13} />
          Fullscreen
        </button>
      </div>
    </div>
  );
}
