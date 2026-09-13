"use client";

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { ScanSearch, Upload } from "lucide-react";
import { api } from "@/lib/api";
import { MediaAnalysis } from "@/types";
import { DemoBadge } from "@/components/DemoBadge";
import { EmptyState, ErrorState, LoadingState, SectionHeader } from "@/components/primitives";

const SAMPLES = [
  { label: "Flood scene (recycled test)", url: "https://demo.mausamnet.in/media/recycled_01.jpg" },
  { label: "Flood scene variant", url: "https://demo.mausamnet.in/media/recycled_02.jpg" },
  { label: "Generic social image", url: "https://demo.mausamnet.in/media/social_004.jpg" },
];

function FindingBadge({ finding }: { finding: string }) {
  const map: Record<string, { color: string; label: string }> = {
    POTENTIAL_RECYCLED: { color: "#ef4444", label: "POTENTIAL RECYCLED MEDIA" },
    NEEDS_REVIEW: { color: "#eab308", label: "NEEDS REVIEW" },
    NO_MATCH: { color: "#22c55e", label: "NO PRIOR MATCH" },
    AUTHENTIC_LIKELY: { color: "#22c55e", label: "LIKELY AUTHENTIC" },
  };
  const m = map[finding] ?? { color: "#94a3b8", label: finding };
  return (
    <span className="rounded px-2 py-1 text-[10px] font-bold uppercase tracking-wider" style={{ color: m.color, backgroundColor: `${m.color}16`, border: `1px solid ${m.color}44` }}>
      {m.label}
    </span>
  );
}

export default function MediaForensicsPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const analyze = useMutation({
    mutationFn: async (vars: { file?: File; url?: string }) => {
      const form = new FormData();
      if (vars.file) form.append("file", vars.file);
      if (vars.url) form.append("media_url", vars.url);
      return api.post<MediaAnalysis>("/ai/analyze-media", form);
    },
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Media Forensics</h1>
          <p className="mt-0.5 text-xs text-dim">Upload images to detect recycled disaster media and verify provenance.</p>
        </div>
        <DemoBadge compact />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {/* Upload / samples */}
        <div className="panel p-5">
          <SectionHeader title="Analyze Media" subtitle="Upload an image or run a demo sample" />
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const f = e.dataTransfer.files?.[0];
              if (f) analyze.mutate({ file: f });
            }}
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 transition ${dragOver ? "border-signal bg-signal/5" : "border-ink-600"}`}
          >
            <Upload size={28} className="text-slate-500" aria-hidden />
            <p className="mt-3 text-sm text-slate-300">Drop an image here, or</p>
            <button
              onClick={() => fileRef.current?.click()}
              className="focus-ring mt-2 rounded-md bg-signal px-4 py-2 text-xs font-bold text-ink-950 hover:bg-signal-dim"
            >
              Choose File
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) analyze.mutate({ file: f });
              }}
              aria-label="Upload image for forensics"
            />
            <p className="mt-2 text-[10px] text-slate-500">JPEG / PNG / WebP · max 8 MB</p>
          </div>

          <div className="mt-4">
            <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-dim">Demo Samples</p>
            <div className="flex flex-wrap gap-2">
              {SAMPLES.map((s) => (
                <button
                  key={s.url}
                  onClick={() => analyze.mutate({ url: s.url })}
                  className="focus-ring rounded-md border border-ink-600 px-3 py-1.5 text-[11px] font-semibold text-slate-200 hover:border-signal hover:text-signal"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Result */}
        <div className="panel p-5">
          <SectionHeader title="Forensic Report" subtitle="Explainable prototype analysis" />
          {analyze.isPending && <LoadingState label="Computing perceptual hash, matching corpus…" />}
          {analyze.isError && <ErrorState message={(analyze.error as Error)?.message ?? "Analysis failed."} onRetry={() => analyze.reset()} />}
          {!analyze.isPending && !analyze.data && (
            <EmptyState
              title="No analysis yet"
              hint="Upload an image or pick a demo sample. The prototype hashes the image and checks it against every previously analyzed medium."
            />
          )}
          {analyze.data && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <FindingBadge finding={analyze.data.finding} />
                <span className="font-mono text-[10px] text-slate-500">aHash {analyze.data.phash.slice(0, 12)}…</span>
              </div>

              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  { k: "Similarity", v: `${Math.round(analyze.data.similarity * 100)}%`, accent: analyze.data.similarity >= 0.9 },
                  { k: "Dimensions", v: analyze.data.width ? `${analyze.data.width}×${analyze.data.height}` : "—" },
                  { k: "EXIF", v: analyze.data.exif_ok ? "Present" : "Stripped" },
                  { k: "Captured", v: analyze.data.captured_at ? new Date(analyze.data.captured_at).toLocaleDateString("en-IN") : "Unknown" },
                ].map((m) => (
                  <div key={m.k} className="panel-subtle p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-dim">{m.k}</p>
                    <p className={`mt-1 font-mono text-sm font-bold ${m.accent ? "text-red-400" : "text-slate-100"}`}>{m.v}</p>
                  </div>
                ))}
              </div>

              <div className={`rounded-lg border p-4 ${
                analyze.data.similarity >= 0.9 ? 'border-red-500/40 bg-red-500/10' :
                analyze.data.similarity >= 0.75 ? 'border-orange-500/40 bg-orange-500/10' :
                analyze.data.similarity >= 0.5 ? 'border-yellow-500/40 bg-yellow-500/10' :
                'border-green-500/40 bg-green-500/10'
              }`}>
                <p className={`text-[11px] font-bold uppercase tracking-widest ${
                  analyze.data.similarity >= 0.9 ? 'text-red-400' :
                  analyze.data.similarity >= 0.75 ? 'text-orange-400' :
                  analyze.data.similarity >= 0.5 ? 'text-yellow-400' :
                  'text-green-400'
                }`}>
                  {analyze.data.similarity >= 0.9 ? '🔴 Potential Recycled Media' :
                   analyze.data.similarity >= 0.75 ? '🟠 Strong Similarity — Review' :
                   analyze.data.similarity >= 0.5 ? '🟡 Possible Match — Investigate' :
                   '🟢 No Significant Prior Match'}
                </p>
                
                <ul className={`mt-3 space-y-1.5 text-xs ${
                  analyze.data.similarity >= 0.9 ? 'text-red-300' :
                  analyze.data.similarity >= 0.75 ? 'text-orange-300' :
                  analyze.data.similarity >= 0.5 ? 'text-yellow-300' :
                  'text-green-300'
                }`}>
                  <li><span className="opacity-70 font-mono w-32 inline-block">Similarity:</span> {Math.round(analyze.data.similarity * 100)}%</li>
                  <li><span className="opacity-70 font-mono w-32 inline-block">Previous appearance:</span> {analyze.data.similarity >= 0.5 ? 'Detected' : 'Not detected'}</li>
                  {analyze.data.similarity >= 0.5 && analyze.data.previous_seen_at && (
                    <li><span className="opacity-70 font-mono w-32 inline-block">First seen:</span> {new Date(analyze.data.previous_seen_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}</li>
                  )}
                  <li><span className="opacity-70 font-mono w-32 inline-block">EXIF:</span> {analyze.data.exif_ok ? 'Present' : 'Stripped'}</li>
                  <li><span className="opacity-70 font-mono w-32 inline-block">{analyze.data.similarity >= 0.5 ? 'Confidence:' : 'Provenance:'}</span> {analyze.data.similarity >= 0.9 ? 'High' : analyze.data.similarity >= 0.5 ? 'Medium' : 'Unknown'}</li>
                </ul>
                
                {analyze.data.similarity >= 0.75 && (
                  <p className={`mt-3 text-[11px] ${analyze.data.similarity >= 0.9 ? 'text-red-200' : 'text-orange-200'} italic`}>
                    "The image is visually similar to previously observed disaster imagery. The system flags it for provenance verification instead of treating it as new evidence."
                  </p>
                )}
              </div>

              <p className="text-[10px] text-slate-500">
                Prototype: 64-bit average hash (aHash) + hamming similarity. Production roadmap: CLIP/ViT embeddings, C2PA provenance,
                reverse-image search APIs.
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="panel p-5">
        <SectionHeader title="Media Provenance & Recycle Detection" subtitle="End-to-end verification pipeline" />
        <div className="mb-6 flex flex-wrap items-center gap-2 rounded bg-ink-900/50 p-3 text-[10px] font-bold uppercase tracking-widest text-dim">
          <span className="text-signal">Upload</span>
          <span className="text-ink-600">→</span>
          <span className="text-signal">Normalize</span>
          <span className="text-ink-600">→</span>
          <span className="text-signal">Perceptual Hash</span>
          <span className="text-ink-600">→</span>
          <span className="text-signal">Similarity Search</span>
          <span className="text-ink-600">→</span>
          <span className="text-signal">Provenance Check</span>
          <span className="text-ink-600">→</span>
          <span className="text-slate-100">Verdict</span>
        </div>
        <div className="grid gap-3 text-xs text-slate-300 sm:grid-cols-4">
          {[
            { t: "1 · Decode", d: "Image decoded and normalized to 8×8 grayscale." },
            { t: "2 · Hash", d: "64-bit average hash computed — robust to resize/compress." },
            { t: "3 · Match", d: "Hamming distance against every stored media hash." },
            { t: "4 · Verdict", d: "≥90% similarity flagged as potential recycled media." },
          ].map((s) => (
            <div key={s.t} className="panel-subtle p-3">
              <p className="font-bold text-signal">{s.t}</p>
              <p className="mt-1 text-[11px] text-dim">{s.d}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 border-t border-ink-700/60 pt-4">
          <h3 className="mb-3 text-[10px] font-bold uppercase tracking-wider text-dim">Similarity Thresholds</h3>
          <div className="grid gap-2 sm:grid-cols-4">
            <div className="rounded border border-red-500/20 bg-red-500/5 p-2 text-xs">
              <span className="font-mono font-bold text-red-400">≥ 90%</span>
              <p className="mt-1 text-slate-300">🔴 Potential Recycled Media</p>
            </div>
            <div className="rounded border border-orange-500/20 bg-orange-500/5 p-2 text-xs">
              <span className="font-mono font-bold text-orange-400">75–89%</span>
              <p className="mt-1 text-slate-300">🟠 Strong Similarity — Review</p>
            </div>
            <div className="rounded border border-yellow-500/20 bg-yellow-500/5 p-2 text-xs">
              <span className="font-mono font-bold text-yellow-400">50–74%</span>
              <p className="mt-1 text-slate-300">🟡 Possible Match — Investigate</p>
            </div>
            <div className="rounded border border-green-500/20 bg-green-500/5 p-2 text-xs">
              <span className="font-mono font-bold text-green-400">&lt; 50%</span>
              <p className="mt-1 text-slate-300">🟢 No Significant Prior Match</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
