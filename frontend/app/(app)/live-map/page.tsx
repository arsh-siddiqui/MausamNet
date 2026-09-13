"use client";

import { useMemo, useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { MapPoint } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { ErrorState, LoadingState } from "@/components/primitives";
import IndiaMap from "@/components/map/IndiaMapDynamic";
import { MapToolbar, LayerState } from "@/components/map/MapToolbar";
import { MapLegend } from "@/components/map/MapLegend";
import { TimelineScrubber } from "@/components/map/TimelineScrubber";
import { ContextualPanel } from "@/components/map/ContextualPanel";
import { BottomEventStrip } from "@/components/map/BottomEventStrip";

export default function LiveMapPage() {
  const [hours, setHours] = useState(72);
  const [selected, setSelected] = useState<MapPoint | null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [legendOpen, setLegendOpen] = useState(true);
  const [resetTrigger, setResetTrigger] = useState(0);
  const [layers, setLayers] = useState<LayerState>({
    events: true,
    risk: true,
    rainfall: true,
    signals: true,
    anomalies: true,
  });

  const params = new URLSearchParams({ layer: "all", hours: String(hours), limit: "1200" });

  const points = useQuery<MapPoint[]>({
    queryKey: ["map", "all", hours],
    queryFn: () => api.get<MapPoint[]>(`/map/points?${params.toString()}`),
    refetchInterval: 20_000,
  });

  const toggleLayer = useCallback((layer: keyof LayerState) => {
    setLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  }, []);

  const select = useCallback((p: MapPoint) => {
    setSelected(p);
  }, []);

  const closePanel = () => setSelected(null);

  const activeEventsCount = useMemo(() => {
    return points.data?.filter(p => p.kind === "event").length || 0;
  }, [points.data]);

  const criticalEventsCount = useMemo(() => {
    return points.data?.filter(p => p.kind === "event" && p.severity === "CRITICAL").length || 0;
  }, [points.data]);

  const signalCount = useMemo(() => {
    return points.data?.filter(p => p.kind === "signal").length || 0;
  }, [points.data]);

  return (
    <div className={`flex flex-col gap-0 ${fullscreen ? "fixed inset-0 z-[100] bg-ink-950 p-0" : "h-[calc(100vh-100px)]"} bg-ink-950 overflow-hidden rounded-xl border border-ink-800 shadow-2xl relative`}>
      
      {/* MAP HEADER */}
      <div className="z-[500] shrink-0 bg-ink-950 border-b border-ink-800 p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-md">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            <span className="text-signal animate-pulse">●</span> LIVE NATIONAL WEATHER INTELLIGENCE
          </h1>
          <DemoBadge compact />
        </div>
        <p className="text-[12px] font-mono text-slate-300">
          <span className="font-bold text-slate-100">42</span> Active Events <span className="text-ink-600 mx-2">|</span> 
          <span className="font-bold text-slate-100">327</span> Clustered Signals <span className="text-ink-600 mx-2">|</span> 
          <span className="font-bold text-red-400">6</span> Critical
        </p>
      </div>

      <div className="relative flex-1 bg-ink-900">
        {points.isLoading ? (
          <div className="flex h-full items-center justify-center bg-ink-900"><LoadingState label="Initializing national layers…" /></div>
        ) : points.isError ? (
          <div className="flex h-full items-center justify-center bg-ink-900"><ErrorState message="Map data source unavailable." onRetry={() => points.refetch()} /></div>
        ) : (
          <IndiaMap 
            points={points.data ?? []} 
            onSelect={select} 
            selectedId={selected?.id ?? null} 
            height="100%" 
            layers={layers}
            resetTrigger={resetTrigger}
          />
        )}

        <MapToolbar 
          layers={layers} 
          onToggleLayer={toggleLayer} 
          onFullscreen={() => setFullscreen(f => !f)} 
          onResetView={() => setResetTrigger(v => v + 1)} 
        />
        <MapLegend open={legendOpen} onToggle={() => setLegendOpen(o => !o)} />
        
        {selected ? (
          <ContextualPanel selected={selected} onClose={closePanel} />
        ) : (
          // Empty State Prompt
          <div className="absolute bottom-24 right-4 z-[1000] rounded-xl border border-ink-800 bg-ink-950/80 p-4 shadow-xl backdrop-blur-md hidden md:block">
            <p className="text-xs font-semibold text-slate-300">MAP INTELLIGENCE</p>
            <p className="text-[11px] text-slate-400 mt-1">Click any event, cluster or anomaly<br/>to inspect its evidence.</p>
          </div>
        )}
      </div>
      
      {/* BOTTOM EVENT STRIP */}
      {points.data && (
        <div className="z-[500] shrink-0 bg-ink-950">
          <BottomEventStrip points={points.data} onSelect={select} />
          <TimelineScrubber hours={hours} onChange={setHours} />
        </div>
      )}
    </div>
  );
}
