"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { Circle, MapContainer, TileLayer, Tooltip, useMap, Marker, GeoJSON } from "react-leaflet";
import L from "leaflet";
import useSupercluster from "use-supercluster";
// @ts-ignore
import { HeatmapLayer } from "react-leaflet-heatmap-layer-v3";
import { MapPoint, SEVERITY_COLORS } from "@/types";
import { LayerState } from "./MapToolbar";

const SEVERITY_RADIUS: Record<string, number> = {
  LOW: 7,
  MEDIUM: 11,
  HIGH: 15,
  CRITICAL: 20,
};

function getSourceIcon(cat?: string | null) {
  switch (cat) {
    case "GOVERNMENT": return "🏛️";
    case "WEATHER_API": return "📡";
    case "NEWS": return "📰";
    case "SOCIAL": return "📱";
    case "GROUND": return "📍";
    default: return "•";
  }
}

function MapStateSync({ onBoundsChange }: { onBoundsChange: (b: L.LatLngBounds, z: number) => void }) {
  const map = useMap();
  useEffect(() => {
    function update() {
      onBoundsChange(map.getBounds(), map.getZoom());
    }
    update();
    map.on("moveend", update);
    return () => {
      map.off("moveend", update);
    };
  }, [map, onBoundsChange]);
  return null;
}

function FitIndia({ trigger }: { trigger: number }) {
  const map = useMap();
  useEffect(() => {
    if (trigger > 0) {
      map.flyToBounds([[7.0, 68.0], [36.0, 97.0]], { duration: 1.5 });
    }
  }, [trigger, map]);
  return null;
}

function SelectedRing({ point }: { point: MapPoint }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([point.latitude, point.longitude], Math.max(map.getZoom(), 8), { duration: 1 });
  }, [point, map]);
  
  const color = SEVERITY_COLORS[point.severity || "MEDIUM"] || "#38bdf8";

  return (
    <>
      <Circle
        center={[point.latitude, point.longitude]}
        radius={25000}
        pathOptions={{ color, weight: 1, fillColor: color, fillOpacity: 0.15 }}
      >
        <Tooltip direction="top" offset={[0, -10]} opacity={1} permanent className="risk-zone-tooltip">
          <div className="bg-ink-950/80 backdrop-blur border border-ink-700 px-2 py-1 rounded text-[9px] font-mono text-slate-300 tracking-wider">
            <span style={{ color }}>●</span> {point.severity || "HIGH"} RISK ZONE
          </div>
        </Tooltip>
      </Circle>
      <Circle
        center={[point.latitude, point.longitude]}
        radius={25000}
        pathOptions={{ color, weight: 1.5, fill: false, className: "animate-pulse opacity-50" }}
      />
    </>
  );
}

interface IndiaMapProps {
  points: MapPoint[];
  onSelect?: (p: MapPoint) => void;
  selectedId?: string | null;
  height?: string;
  layers?: LayerState;
  resetTrigger?: number;
  hideStateTooltip?: boolean;
}

const DEFAULT_LAYERS: LayerState = { events: true, risk: true, rainfall: true, signals: true, anomalies: true };

export default function IndiaMap({ 
  points, 
  onSelect, 
  selectedId = null, 
  height = "600px", 
  layers = DEFAULT_LAYERS, 
  resetTrigger = 0,
  hideStateTooltip = false
}: IndiaMapProps) {
  const [bounds, setBounds] = useState<L.LatLngBounds | null>(null);
  const [zoom, setZoom] = useState(5);

  const geoJsonPoints = useMemo(() => {
    return points
      .filter((p) => {
        if (p.kind === "event" && !layers.events) return false;
        if (p.kind === "signal" && !layers.signals) return false;
        if (p.kind === "anomaly" && !layers.anomalies) return false;
        
        // Progressive Disclosure logic
        if (p.kind === "signal" && zoom < 7) return false; // Hide individual signals at low zoom
        
        return true;
      })
      .map((p) => ({
        type: "Feature" as const,
        properties: { cluster: false, pointId: p.id, point: p },
        geometry: { type: "Point" as const, coordinates: [p.longitude, p.latitude] },
      }));
  }, [points, layers, zoom]);

  const { clusters, supercluster } = useSupercluster({
    points: geoJsonPoints,
    bounds: bounds ? [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()] : undefined,
    zoom,
    options: { radius: 60, maxZoom: 14 },
  });

  const selectedPoint = useMemo(() => points.find((p) => p.id === selectedId), [points, selectedId]);

  const handleBoundsChange = useCallback((b: L.LatLngBounds, z: number) => {
    setBounds(b);
    setZoom(z);
  }, []);

  return (
    <div style={{ height }} className="relative w-full overflow-hidden rounded-lg border border-ink-700/70 bg-[#1e2329]">
      <MapContainer
        center={[22.5, 82]}
        zoom={5}
        minZoom={4}
        maxZoom={18}
        scrollWheelZoom
        style={{ height: "100%", width: "100%", zIndex: 10 }}
        preferCanvas
      >
        <MapStateSync onBoundsChange={handleBoundsChange} />
        <FitIndia trigger={resetTrigger} />

        <TileLayer
          attribution="&copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        />

        <StateLayer points={points} selectedId={selectedId} hideStateTooltip={hideStateTooltip} />

        {layers.rainfall && (
          <HeatmapLayer
            fitBoundsOnLoad={false}
            points={points.filter((p) => p.kind === "signal" && p.event_type === "RAINFALL")}
            longitudeExtractor={(m: MapPoint) => m.longitude}
            latitudeExtractor={(m: MapPoint) => m.latitude}
            intensityExtractor={() => 20}
            radius={25}
            blur={25}
            gradient={{ 0.2: "#3b82f6", 0.4: "#22d3ee", 0.6: "#2dd4bf", 0.8: "#facc15", 1.0: "#ef4444" }}
          />
        )}

        {/* RISK ZONES */}
        {layers.risk && points.filter((p) => p.kind === "event" && (p.severity === "CRITICAL" || p.severity === "HIGH")).map((p) => (
          <Circle
            key={`risk-${p.id}`}
            center={[p.latitude, p.longitude]}
            radius={p.severity === "CRITICAL" ? 60000 : 40000}
            pathOptions={{ 
              color: SEVERITY_COLORS[p.severity], 
              weight: 0, 
              fillColor: SEVERITY_COLORS[p.severity], 
              fillOpacity: p.severity === "CRITICAL" ? 0.2 : 0.1, 
              className: "pointer-events-none" 
            }}
          />
        ))}

        {selectedPoint && <SelectedRing point={selectedPoint} />}

          {clusters.map((cluster) => {
            const [longitude, latitude] = cluster.geometry.coordinates;
            const { cluster: isCluster, point_count: pointCount } = cluster.properties;
  
            if (isCluster) {
              const size = pointCount < 20 ? 24 : pointCount < 50 ? 28 : 34;
              const icon = L.divIcon({
                html: `<div style="width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center; background: rgba(148, 163, 184, 0.15); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 50%; color: #94a3b8; font-weight: 500; font-size: 10px; backdrop-filter: blur(2px); cursor: pointer;">${pointCount}</div>`,
                className: "",
                iconSize: [size, size],
                iconAnchor: [size / 2, size / 2],
              });

            return (
              <Marker
                key={`cluster-${cluster.id}`}
                position={[latitude, longitude]}
                icon={icon}
                eventHandlers={{
                  click: (e) => {
                    // Simulate selecting a cluster to open contextual panel. 
                    // In a real app we might have a specific MapPoint for cluster.
                    // For now, we just zoom in.
                    if (!supercluster) return;
                    const expansionZoom = Math.min(supercluster.getClusterExpansionZoom(cluster.id as number), 14);
                    e.target._map?.flyTo([latitude, longitude], expansionZoom);
                  },
                }}
              >
                <Tooltip direction="top" offset={[0, -10]}>
                  <div className="text-[11px] leading-snug">
                    <p className="font-bold">SIGNAL CLUSTER</p>
                    <p>{pointCount} signals in this area</p>
                    <p className="text-signal">Click to zoom into cluster</p>
                  </div>
                </Tooltip>
              </Marker>
            );
          }

          const p = cluster.properties.point as MapPoint;
          const color = p.kind === "anomaly" ? "#c084fc" : SEVERITY_COLORS[p.severity] || "#38bdf8";
          const isSelected = selectedId === p.id;
          
          let iconHtml = "";
          if (p.kind === "event") {
            // Event halo, small circle
            iconHtml = `<div style="width: 12px; height: 12px; background: ${color}; border-radius: 50%; border: 2px solid #1e2329; box-shadow: 0 0 12px ${color}; cursor: pointer;"></div>`;
          } else if (p.kind === "anomaly") {
            iconHtml = `<div style="width: 10px; height: 10px; background: #c084fc; transform: rotate(45deg); border: 1px solid #e9d5ff; box-shadow: 0 0 8px #c084fc; cursor: pointer;"></div>`;
          } else {
            iconHtml = `<div style="width: 20px; height: 20px; background: ${color}22; border: 1px solid ${color}88; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; cursor: pointer;">${getSourceIcon(p.source_category)}</div>`;
          }

          if (isSelected) {
            iconHtml = `<div style="transform: scale(1.4); transition: transform 0.2s;">${iconHtml}</div>`;
          }

          const icon = L.divIcon({
            html: iconHtml,
            className: "",
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          });

          return (
            <Marker
              key={`${p.kind}-${p.id}`}
              position={[latitude, longitude]}
              icon={icon}
              eventHandlers={{ click: () => onSelect?.(p) }}
            >
              {p.kind === "anomaly" && (
                <Tooltip direction="top" offset={[0, -10]}>
                  <div className="text-[11px] leading-snug font-sans min-w-[140px]">
                    <div style={{ fontWeight: "bold", textTransform: "uppercase", marginBottom: "4px", color: "#f8fafc", fontSize: "12px", letterSpacing: "0.05em" }}>{p.title.split(' ')[0]}</div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "4px", color: "#94a3b8" }}>
                      <span>Rainfall anomaly:</span> <span style={{ color: "#c084fc", fontWeight: "bold" }}>+{Math.round(p.deviation_pct || 0)}%</span>
                      <span>Risk:</span> <span style={{ color: SEVERITY_COLORS[p.severity] || "#fff", fontWeight: "bold" }}>{p.severity}</span>
                    </div>
                    <p style={{ color: "#38bdf8", marginTop: "6px", fontWeight: "bold" }}>View analysis →</p>
                  </div>
                </Tooltip>
              )}
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}

function StateLayer({ points, selectedId, hideStateTooltip }: { points: MapPoint[], selectedId?: string | null, hideStateTooltip?: boolean }) {
  const [geoData, setGeoData] = useState<any>(null);
  const map = useMap();

  useEffect(() => {
    fetch('/india_states.geojson')
      .then(res => res.json())
      .then(data => setGeoData(data))
      .catch(err => console.error("Could not load states geojson", err));
  }, []);

  if (!geoData) return null;

  return (
    <GeoJSON
      data={geoData}
      style={{
        color: "#ffffff",
        weight: 1,
        fillColor: "transparent",
        fillOpacity: 0,
        opacity: 0.1,
        className: "state-boundary"
      }}
      onEachFeature={(feature, layer) => {
        const stateName = feature.properties.NAME_1 || feature.properties.st_nm || feature.properties.ST_NM || "Unknown State";
        
        // Calculate state stats
        let activeEvents = 0;
        let criticalEvents = 0;
        let totalSignals = 0;
        let totalAnomalies = 0;
        let totalConfidence = 0;
        let confidenceCount = 0;

        points.forEach(p => {
          // Normalize string comparison
          if (p.state && stateName && p.state.toLowerCase() === stateName.toLowerCase()) {
            if (p.kind === "event") {
              activeEvents++;
              if (p.severity === "CRITICAL") criticalEvents++;
              if (p.confidence != null) {
                totalConfidence += p.confidence;
                confidenceCount++;
              }
            } else if (p.kind === "signal") {
              totalSignals++;
            } else if (p.kind === "anomaly") {
              totalAnomalies++;
            }
          }
        });

        const avgConfidence = confidenceCount > 0 ? Math.round(totalConfidence / confidenceCount) : 0;

        // Add tooltip
        if (!selectedId && !hideStateTooltip) {
          const tooltipContent = `
            <div style="font-family: inherit; min-width: 120px;">
              <div style="font-weight: bold; text-transform: uppercase; margin-bottom: 4px; color: #f8fafc; font-size: 12px; letter-spacing: 0.05em;">${stateName}</div>
              <div style="font-size: 11px; color: #94a3b8; display: grid; grid-template-columns: 1fr auto; gap: 4px;">
                <span>Active Events:</span> <span style="color: #38bdf8; font-weight: bold;">${activeEvents}</span>
                <span>Critical:</span> <span style="color: #f87171; font-weight: bold;">${criticalEvents}</span>
                <span>Signals:</span> <span style="color: #cbd5e1; font-weight: bold;">${totalSignals}</span>
                <span>Anomalies:</span> <span style="color: #c084fc; font-weight: bold;">${totalAnomalies}</span>
                <span>Confidence:</span> <span style="color: #cbd5e1; font-weight: bold;">${avgConfidence}%</span>
              </div>
            </div>
          `;
          layer.bindTooltip(tooltipContent, { direction: 'auto', opacity: 0.9, className: 'state-tooltip bg-ink-950 border border-ink-800 rounded p-2 shadow-xl backdrop-blur-md' });
        }

        // Hover effect & Click to zoom
        layer.on({
          mouseover: (e) => {
            const l = e.target;
            l.setStyle({ weight: 2, color: "#38bdf8", fillOpacity: 0.1, fillColor: "#38bdf8", opacity: 0.8 });
            if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
              l.bringToFront();
            }
          },
          mouseout: (e) => {
            const l = e.target;
            l.setStyle({ weight: 1, color: "#ffffff", fillOpacity: 0, opacity: 0.2 });
          },
          click: (e) => {
            map.flyToBounds(e.target.getBounds(), { duration: 1 });
          }
        });
      }}
    />
  );
}
