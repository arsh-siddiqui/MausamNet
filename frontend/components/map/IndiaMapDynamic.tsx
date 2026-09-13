"use client";

import dynamic from "next/dynamic";

/** Leaflet needs window — loaded client-side only with a graceful skeleton. */
const IndiaMap = dynamic(() => import("@/components/map/IndiaMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[420px] w-full items-center justify-center rounded-lg border border-ink-700/70 bg-ink-900/60">
      <div className="flex items-center gap-3 text-sm text-dim">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-signal border-t-transparent" aria-hidden />
        Loading national map…
      </div>
    </div>
  ),
});

export default IndiaMap;
