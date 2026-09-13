import React from "react";

export function TimelineScrubber({ hours, onChange }: { hours: number; onChange: (h: number) => void }) {
  return (
    <div className="absolute bottom-6 left-1/2 z-[1000] flex w-full max-w-xl -translate-x-1/2 flex-col gap-2 rounded-lg border border-ink-700/60 bg-ink-950/95 p-3 shadow-xl backdrop-blur-md">
      <div className="flex justify-between px-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
        <span>-30 Days</span>
        <span>-7 Days</span>
        <span>-3 Days</span>
        <span>-24 Hrs</span>
        <span className="text-signal">Now</span>
      </div>
      <div className="relative flex items-center">
        <input
          type="range"
          min="1"
          max="5"
          step="1"
          className="w-full cursor-pointer accent-signal"
          value={hours === 720 ? 1 : hours === 168 ? 2 : hours === 72 ? 3 : hours === 24 ? 4 : 5}
          onChange={(e) => {
            const v = Number(e.target.value);
            const val = v === 1 ? 720 : v === 2 ? 168 : v === 3 ? 72 : v === 4 ? 24 : 6;
            onChange(val);
          }}
          aria-label="Time window"
        />
      </div>
    </div>
  );
}
