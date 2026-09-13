"use client";

import { useMemo } from "react";
import { EmptyState } from "@/components/primitives";

interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

const NODE_COLORS: Record<string, string> = {
  "IMD / Government": "#22c55e",
  "Weather APIs": "#38bdf8",
  News: "#eab308",
  Social: "#f97316",
  "Citizen Ground": "#94a3b8",
  "Public Datasets": "#8b5cf6",
  "Weather Observations": "#22d3ee",
  "Image Evidence": "#f472b6",
};

/** Radial evidence graph: sources → event node with confidence-labeled edges. */
export function EvidenceGraph({ graph }: { graph: { nodes: { id: string; label: string }[]; edges: GraphEdge[] } | null }) {
  const layout = useMemo(() => {
    if (!graph || graph.nodes.length === 0) return null;
    const sources = graph.nodes.filter((n) => n.id !== "event" && !n.id.startsWith("sig:"));
    const others = graph.nodes.filter((n) => n.id.startsWith("sig:"));
    const center = { x: 250, y: 155 };
    const positions: Record<string, { x: number; y: number }> = { event: center };
    const R = 118;
    sources.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(sources.length, 1) - Math.PI / 2;
      positions[n.id] = { x: center.x + R * Math.cos(angle), y: center.y + R * 0.78 * Math.sin(angle) };
    });
    others.forEach((n, i) => {
      positions[n.id] = { x: 30 + (i % 4) * 118, y: 290 };
    });
    return { positions, sources, others };
  }, [graph]);

  if (!graph || !layout) return <EmptyState title="Graph unavailable" hint="No evidence edges recorded for this event." />;

  return (
    <svg viewBox="0 0 500 330" className="w-full" role="img" aria-label="Evidence relationship graph">
      {graph.edges.map((edge, i) => {
        const a = layout.positions[edge.source];
        const b = layout.positions[edge.target];
        if (!a || !b) return null;
        const dashed = edge.relation === "DUPLICATE_OF" || edge.relation === "CONTRADICTS";
        const color = edge.relation === "CONTRADICTS" ? "#ef4444" : dashed ? "#94a3b8" : "#33476b";
        return (
          <g key={i}>
            <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={color} strokeWidth={1 + edge.weight * 2.2} strokeDasharray={dashed ? "4 4" : undefined} />
            {edge.source !== "event" && edge.target === "event" && (
              <text x={(a.x + b.x) / 2} y={(a.y + b.y) / 2 - 4} textAnchor="middle" fontSize="8.5" fill="#64748b">
                {Math.round(edge.weight * 100)}%
              </text>
            )}
          </g>
        );
      })}
      {graph.nodes.map((n) => {
        const pos = layout.positions[n.id];
        if (!pos) return null;
        const isEvent = n.id === "event";
        const color = isEvent ? "#38bdf8" : NODE_COLORS[n.label] ?? "#94a3b8";
        return (
          <g key={n.id}>
            {isEvent && <circle cx={pos.x} cy={pos.y} r={34} fill="rgba(56,189,248,0.08)" stroke="#38bdf8" strokeWidth={1.4} />}
            {!isEvent && <circle cx={pos.x} cy={pos.y} r={9} fill={color} opacity={0.85} />}
            <text
              x={pos.x}
              y={isEvent ? pos.y + 3 : pos.y - 15}
              textAnchor="middle"
              fontSize={isEvent ? 8.5 : 9}
              fontWeight="bold"
              fill={isEvent ? "#e2e8f0" : "#cbd5e1"}
            >
              {isEvent ? "EVENT" : n.label.length > 16 ? `${n.label.slice(0, 15)}…` : n.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
