"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { Event } from "@/types";
import { SectionHeader } from "@/components/primitives";

interface WhyThisEventCardProps {
  event: Event;
}

export function WhyThisEventCard({ event }: WhyThisEventCardProps) {
  const confidence = event.confidence || 0;
  const trustScore = event.trust_score || 0;
  const explanations = event.fusion?.explanations || [
    "✓ Anomaly detected in baseline data",
    "✓ Corroborated by external sources",
    "✓ Spatial and temporal clustering",
  ];

  return (
    <div className="panel p-5 relative overflow-hidden group border-signal/20 shadow-[0_0_15px_rgba(56,189,248,0.05)]">
      <SectionHeader title="WHY THIS EVENT?" subtitle={event.title} />
      
      <div className="mt-4 grid gap-6 md:grid-cols-2">
        <div className="space-y-3 font-mono text-sm text-slate-300 bg-ink-900/50 p-4 rounded-lg border border-ink-700/50">
          {explanations.map((exp, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className={exp.startsWith("✓") ? "text-signal font-bold" : "text-slate-400"}>
                {exp}
              </span>
            </div>
          ))}
        </div>
        
        <div className="space-y-6 flex flex-col justify-center">
          <div>
            <div className="flex justify-between text-xs font-bold uppercase tracking-wider mb-1.5">
              <span className="text-slate-400">AI Confidence</span>
              <span className="text-signal">{Math.round(confidence)}%</span>
            </div>
            <div className="h-2.5 w-full bg-ink-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-signal transition-all duration-1000" 
                style={{ width: `${confidence}%` }}
              />
            </div>
          </div>
          
          <div>
            <div className="flex justify-between text-xs font-bold uppercase tracking-wider mb-1.5">
              <span className="text-slate-400">Source Agreement</span>
              <span className="text-blue-400">{Math.round(trustScore)}%</span>
            </div>
            <div className="h-2.5 w-full bg-ink-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all duration-1000" 
                style={{ width: `${trustScore}%` }}
              />
            </div>
          </div>
          
          <div className="flex items-center justify-between pt-2 border-t border-ink-800">
            <span className="text-xs text-dim font-medium">
              {event.signal_count} signals · Multiple sources
            </span>
            <Link
              href={`/events/${event.id}`}
              className="focus-ring flex items-center gap-1.5 rounded-lg bg-signal px-4 py-2 text-xs font-bold text-ink-950 transition hover:bg-signal-dim shadow-[0_0_10px_rgba(56,189,248,0.3)]"
            >
              INVESTIGATE EVENT <ArrowRight size={14} aria-hidden />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
