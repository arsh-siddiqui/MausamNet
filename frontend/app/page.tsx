"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Database,
  FileCheck,
  Globe2,
  Landmark,
  Newspaper,
  Radar,
  ShieldCheck,
  Users,
  Network,
  CheckCircle2,
  Eye,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DemoBadge } from "@/components/DemoBadge";

interface PublicStats {
  signals_processed: number;
  active_events: number;
  suspicious_signals: number;
  states_monitored: number;
  demo: boolean;
}

const SOURCES = [
  { icon: Landmark, label: "Government Data", desc: "Meteorological bulletins & alerts" },
  { icon: Globe2, label: "Weather APIs", desc: "Model output & nowcasts" },
  { icon: Database, label: "Public Datasets", desc: "Open sensor & station feeds" },
  { icon: Newspaper, label: "News Signals", desc: "Impact reporting at scale" },
  { icon: Users, label: "Social Signals", desc: "Clustered citizen chatter" },
  { icon: Activity, label: "Ground Evidence", desc: "On-the-ground observations" },
];

const PIPELINE = [
  { label: "Signals", desc: "6 source categories ingested & normalized" },
  { label: "AI Analysis", desc: "Classification, trust scoring, dedup" },
  { label: "Evidence Fusion", desc: "Spatio-temporal correlation" },
  { label: "Event Detection", desc: "Many signals â†’ one unique event" },
  { label: "Risk Assessment", desc: "Severity & confidence prioritization" },
  { label: "Human Verification", desc: "Analyst-in-the-loop approval" },
];

const CAPABILITIES = [
  { icon: Radar, title: "Event Intelligence", desc: "Reconstruct unique weather events from thousands of fragmented signals." },
  { icon: ShieldCheck, title: "WeatherTrust AI", desc: "Explainable trust scoring with per-component breakdowns." },
  { icon: FileCheck, title: "Media Forensics", desc: "Perceptual hashing detects recycled images before they mislead." },
  { icon: Activity, title: "Anomaly Detection", desc: "Statistical deviation engine flags what the baseline can't explain." },
  { icon: BarChart3, title: "Geospatial Analytics", desc: "State, source and severity intelligence across the nation." },
  { icon: ShieldCheck, title: "Human Verification", desc: "Verifier workflows with audit trails for every decision." },
];

function LiveIntelligenceMapVisual() {
  return (
    <div className="relative w-full max-w-xl rounded-xl border border-ink-600 bg-ink-900 shadow-2xl overflow-hidden font-mono select-none mx-auto lg:mx-0">
      <div className="border-b border-ink-700 bg-ink-800 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse"></span>
          <span className="text-xs font-bold text-slate-300 tracking-wider">LIVE NATIONAL INTELLIGENCE</span>
        </div>
        <span className="text-[10px] text-slate-500 font-bold">INDIA</span>
      </div>
      
      <div className="relative bg-ink-950 h-[320px] w-full overflow-hidden">
        <Image
          src="/hero-map.jpg"
          alt="MausamNet Intelligence Map"
          fill
          className="object-cover object-center"
          priority
        />
      </div>
      
      <div className="border-t border-ink-700 bg-ink-800 p-3 flex justify-between items-center text-xs">
         <div className="flex gap-4 text-slate-300">
           <span><strong className="text-signal">42</strong> EVENTS</span>
           <span><strong className="text-signal">327</strong> SIGNALS</span>
         </div>
         <span className="text-slate-500 font-bold">SYSTEM: ACTIVE</span>
      </div>
    </div>
  );
}

export default function LandingPage() {
  const stats = useQuery<PublicStats>({
    queryKey: ["public-stats"],
    queryFn: () => api.get<PublicStats>("/public/stats"),
  });

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-signal/15">
            <Activity className="text-signal" size={20} aria-hidden />
          </div>
          <div>
            <p className="text-base font-bold tracking-tight">MausamNet</p>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-dim">National Weather Intelligence</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm font-semibold text-slate-300 hover:text-white transition hidden sm:block">
            Sign In
          </Link>
          <Link href="/login" className="focus-ring rounded-md bg-signal/10 border border-signal/30 px-4 py-2 text-sm font-semibold text-signal hover:bg-signal/20 transition">
            Launch Demo
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto grid max-w-7xl items-center gap-10 px-6 pb-16 pt-10 lg:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h1 className="text-5xl font-extrabold tracking-tight text-slate-50 lg:text-6xl">MausamNet</h1>
          <p className="mt-2 text-xl font-semibold text-signal">National Weather Intelligence & Verification Platform</p>
          <p className="mt-4 max-w-xl text-base leading-relaxed text-slate-400">
            Turning fragmented weather signals into trusted, actionable intelligence. MausamNet fuses government, API, dataset, news,
            social and ground evidence into verified weather events â€” with explainable AI confidence and human oversight.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/login"
              className="focus-ring inline-flex items-center gap-2 rounded-lg bg-signal px-6 py-3 text-sm font-bold text-ink-950 shadow-lg shadow-signal/20 transition hover:bg-signal-dim"
            >
              Enter National Command Center <ArrowRight size={16} aria-hidden />
            </Link>
            <a
              href="#how-it-works"
              className="focus-ring inline-flex items-center gap-2 rounded-lg border border-ink-500 px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-signal hover:text-signal"
            >
              Explore Platform
            </a>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, delay: 0.15 }} className="flex justify-center lg:justify-end">
          <LiveIntelligenceMapVisual />
        </motion.div>
      </section>

      {/* Live Intelligence Strip */}
      <section className="border-y border-ink-700 bg-ink-900/80 overflow-hidden">
        <div className="mx-auto max-w-7xl px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
             <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse"></span>
             <span className="text-sm font-bold tracking-widest text-slate-200 uppercase">Live Intelligence</span>
             <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-ink-800 border border-ink-600 text-slate-400">DEMO DATA</span>
          </div>
          <div className="flex flex-wrap items-center justify-center md:justify-end gap-x-6 gap-y-2 text-sm font-semibold text-slate-300">
             <div className="flex items-center gap-2"><span className="text-signal">â€¢</span> 42 Active Events</div>
             <div className="flex items-center gap-2"><span className="text-red-400">â€¢</span> 6 Critical</div>
             <div className="flex items-center gap-2"><span className="text-blue-400">â€¢</span> 18 States</div>
             <div className="flex items-center gap-2"><span className="text-yellow-400">â€¢</span> 327 Clustered Signals</div>
          </div>
        </div>
      </section>

      {/* Multi-source intelligence */}
      <section className="border-b border-ink-700/50 bg-ink-900/40 py-16">
        <div className="mx-auto max-w-7xl px-6">
          <h2 className="text-center text-2xl font-bold tracking-tight text-slate-100">Multi-Source Intelligence</h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {SOURCES.map((s, i) => (
              <motion.div key={s.label} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }} className="panel p-5 bg-ink-800/50 border border-ink-700">
                <s.icon className="text-signal" size={22} aria-hidden />
                <p className="mt-3 text-sm font-bold text-slate-100">{s.label}</p>
                <p className="mt-1 text-xs text-dim">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* The Problem: Why Traditional Data Isn't Enough */}
      <section className="py-20 border-b border-ink-700/50 bg-ink-900/20">
        <div className="mx-auto max-w-5xl px-6">
           <h2 className="text-center text-3xl font-bold tracking-tight text-slate-100">Why Traditional Weather Data Isn't Enough</h2>
           
           <div className="mt-16 flex flex-col md:flex-row items-center justify-center gap-10">
              {/* Problem side */}
              <div className="flex-1 flex flex-col items-center">
                 <div className="bg-ink-800 border border-red-500/20 p-6 rounded-xl flex flex-col items-center gap-3 w-full max-w-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500/10 via-red-500/40 to-red-500/10"></div>
                    <span className="text-sm font-bold text-slate-300">Government Data</span>
                    <span className="text-ink-600 font-bold">+</span>
                    <span className="text-sm font-bold text-slate-300">Weather APIs</span>
                    <span className="text-ink-600 font-bold">+</span>
                    <span className="text-sm font-bold text-slate-300">News Reports</span>
                    <span className="text-ink-600 font-bold">+</span>
                    <span className="text-sm font-bold text-slate-300">Social Signals</span>
                    <span className="text-ink-600 font-bold">+</span>
                    <span className="text-sm font-bold text-slate-300">Ground Observations</span>
                 </div>
                 <div className="h-10 w-px bg-gradient-to-b from-red-500/20 to-red-500/80 my-2"></div>
                 <ArrowRight className="text-red-500/80 rotate-90 mb-2" size={20} />
                 <span className="text-sm font-bold text-red-400 bg-red-400/10 px-4 py-3 rounded-lg border border-red-400/20 text-center shadow-lg shadow-red-500/5 w-full max-w-sm">Thousands of disconnected signals</span>
              </div>

              {/* Arrow */}
              <div className="hidden md:flex flex-col items-center justify-center">
                 <ArrowRight className="text-ink-500" size={32} />
                 <span className="text-[10px] uppercase font-bold text-signal mt-2 tracking-widest">MausamNet</span>
              </div>

              {/* Solution side */}
              <div className="flex-1 flex flex-col items-center w-full">
                 <div className="bg-signal/5 border border-signal/30 p-8 rounded-xl flex flex-col items-center justify-center h-full min-h-[300px] w-full max-w-sm shadow-[0_0_30px_rgba(14,165,233,0.1)]">
                    <Network className="text-signal mb-6" size={48} />
                    <span className="text-2xl font-black text-white text-center leading-tight">Many Signals</span>
                    <ArrowRight className="text-slate-500 rotate-90 my-3" size={20} />
                    <span className="text-2xl font-black text-signal text-center leading-tight">One Intelligence<br/>Picture</span>
                 </div>
              </div>
           </div>
        </div>
      </section>

      {/* Intelligence Pipeline */}
      <section id="how-it-works" className="py-20 border-b border-ink-700/50">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-3xl font-bold tracking-tight text-slate-100">Intelligence Pipeline</h2>
          <ol className="mt-12 space-y-0 max-w-2xl mx-auto">
            {PIPELINE.map((p, i) => (
              <motion.li key={p.label} initial={{ opacity: 0, x: -12 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.06 }} className="relative flex gap-6 pb-8 last:pb-0">
                {i < PIPELINE.length - 1 && <span className="absolute left-[19px] top-10 h-full w-px bg-ink-700" aria-hidden />}
                <span className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 border-signal/40 bg-ink-900 font-mono text-sm font-bold text-signal shadow-[0_0_15px_rgba(14,165,233,0.15)]">
                  {i + 1}
                </span>
                <div className="pt-2">
                  <p className="text-base font-bold text-slate-100">{p.label}</p>
                  <p className="text-sm text-slate-400 mt-1">{p.desc}</p>
                </div>
              </motion.li>
            ))}
          </ol>
        </div>
      </section>

      {/* We Reconstruct Events */}
      <section className="py-24 border-b border-ink-700/50 bg-ink-950 relative overflow-hidden">
        {/* Abstract background glows */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-3xl h-full bg-signal/5 blur-[100px] pointer-events-none"></div>
        
        <div className="mx-auto max-w-5xl px-6 relative z-10">
           <div className="text-center mb-16">
             <h2 className="text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-50">
               We Don't Just Collect Reports. <br className="hidden sm:block" />
               <span className="text-signal mt-2 inline-block">We Reconstruct Weather Events.</span>
             </h2>
             <p className="mt-6 max-w-2xl mx-auto text-lg text-slate-400 leading-relaxed">
               MausamNet combines independent weather, media and geographic evidence to reconstruct emerging weather events and quantify confidence.
             </p>
           </div>
           
           {/* Visual Diagram */}
           <div className="max-w-4xl mx-auto flex flex-col items-center mt-20">
              <div className="grid grid-cols-3 gap-y-4 gap-x-2 w-full text-center items-center">
                 {/* Top */}
                 <div className="col-start-2 flex flex-col items-center">
                    <div className="bg-ink-800 border border-ink-600 px-4 py-2 rounded-lg font-bold text-xs sm:text-sm text-slate-200 shadow-md">IMD / GOVERNMENT</div>
                    <div className="h-10 w-px bg-signal/60 mx-auto"></div>
                    <ArrowRight className="text-signal rotate-90 mx-auto -mt-2" size={18} />
                 </div>
                 
                 {/* Middle Row */}
                 <div className="flex items-center justify-end">
                    <div className="bg-ink-800 border border-ink-600 px-4 py-2 rounded-lg font-bold text-xs sm:text-sm text-slate-200 shadow-md">WEATHER API</div>
                    <div className="w-6 sm:w-12 h-px bg-signal/60"></div>
                    <ArrowRight className="text-signal -ml-2" size={18} />
                 </div>
                 
                 <div className="bg-signal/15 border-2 border-signal/80 px-4 py-6 sm:px-8 sm:py-8 rounded-2xl flex flex-col items-center justify-center shadow-[0_0_40px_rgba(14,165,233,0.25)] relative z-10 backdrop-blur-sm">
                    <Activity className="text-signal mb-3" size={36} />
                    <span className="text-2xl font-black text-white tracking-widest">EVENT</span>
                 </div>
                 
                 <div className="flex items-center justify-start">
                    <ArrowRight className="text-signal rotate-180 -mr-2 z-10" size={18} />
                    <div className="w-6 sm:w-12 h-px bg-signal/60"></div>
                    <div className="bg-ink-800 border border-ink-600 px-4 py-2 rounded-lg font-bold text-xs sm:text-sm text-slate-200 shadow-md">NEWS</div>
                 </div>
                 
                 {/* Bottom stack */}
                 <div className="col-start-2 flex flex-col items-center">
                    <ArrowRight className="text-signal -rotate-90 mx-auto -mb-2 z-10" size={18} />
                    <div className="h-6 w-px bg-signal/60 mx-auto"></div>
                    <div className="bg-ink-800 border border-ink-600 px-4 py-2 rounded-lg font-bold text-xs sm:text-sm text-slate-200 mb-3 shadow-md">SOCIAL</div>
                    
                    <ArrowRight className="text-signal -rotate-90 mx-auto -mb-2 z-10" size={18} />
                    <div className="h-6 w-px bg-signal/60 mx-auto"></div>
                    <div className="bg-ink-800 border border-ink-600 px-4 py-2 rounded-lg font-bold text-xs sm:text-sm text-slate-200 shadow-md">GROUND DATA</div>
                 </div>
              </div>
              
              <div className="mt-16">
                 <div className="bg-signal text-ink-950 font-black text-2xl px-10 py-4 rounded-full shadow-[0_0_30px_rgba(14,165,233,0.5)] border-2 border-white/20">
                    CONFIDENCE: 94%
                 </div>
              </div>
           </div>
        </div>
      </section>

      {/* Signature Scenario */}
      <section className="py-24 border-b border-ink-700/50 bg-ink-900/30">
        <div className="mx-auto max-w-4xl px-6">
           <h2 className="text-center text-xs font-bold tracking-widest uppercase text-signal mb-3">Signature Scenario</h2>
           <h3 className="text-center text-3xl sm:text-4xl font-bold text-slate-100 mb-16">Mumbai Extreme Rainfall</h3>
           
           <div className="relative max-w-xl mx-auto">
             <div className="absolute left-[1.125rem] top-4 bottom-4 w-px bg-ink-700"></div>
             
             <ul className="space-y-6">
               {[
                 { icon: Activity, text: "Rainfall anomaly detected by statistical engine", time: "09:12" },
                 { icon: Globe2, text: "Weather API signals increase across sensor networks", time: "09:45" },
                 { icon: Newspaper, text: "Local news reports waterlogging", time: "10:15" },
                 { icon: Users, text: "Social media cluster detected with user videos", time: "10:30" },
                 { icon: Network, text: "Flood event reconstructed by MausamNet AI", time: "10:32", highlight: true },
                 { icon: FileCheck, text: "Old image flagged as suspicious by Media Forensics", time: "10:35" },
                 { icon: CheckCircle2, text: "94% Confidence Reached", time: "10:38", highlight: true },
                 { icon: ShieldCheck, text: "Human verification by IMD Analyst", time: "10:45" },
               ].map((step, idx) => (
                 <motion.li key={idx} initial={{ opacity: 0, x: -20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: idx * 0.1 }} className="relative flex items-center gap-6">
                   <div className={`h-10 w-10 shrink-0 rounded-full flex items-center justify-center relative z-10 ${step.highlight ? 'bg-signal text-ink-950 shadow-[0_0_15px_rgba(14,165,233,0.4)]' : 'bg-ink-800 border border-ink-600 text-slate-300'}`}>
                     <step.icon size={18} />
                   </div>
                   <div className={`flex-1 rounded-xl p-4 ${step.highlight ? 'bg-signal/10 border border-signal/30' : 'bg-ink-800/40 border border-ink-700/50'}`}>
                      <div className="flex justify-between items-center gap-4">
                        <span className={`font-semibold text-sm sm:text-base leading-snug ${step.highlight ? 'text-signal' : 'text-slate-200'}`}>{step.text}</span>
                        <span className="text-xs text-slate-500 font-mono font-bold bg-ink-900/50 px-2 py-1 rounded">{step.time}</span>
                      </div>
                   </div>
                 </motion.li>
               ))}
             </ul>
           </div>
           
           <div className="mt-16 flex justify-center">
             <Link href="/events/EV-MUM-001" className="focus-ring inline-flex items-center gap-2 rounded-xl bg-ink-800 border border-ink-600 px-8 py-4 text-sm font-bold text-slate-200 hover:border-signal hover:text-signal shadow-lg transition">
               <Eye size={18} /> View Example Event
             </Link>
           </div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="border-b border-ink-700/50 bg-ink-900/40 py-20">
        <div className="mx-auto max-w-7xl px-6">
          <h2 className="text-center text-3xl font-bold tracking-tight text-slate-100">Key Capabilities</h2>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {CAPABILITIES.map((c, i) => (
              <motion.div key={c.title} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }} className="panel p-6 bg-ink-800/50 border border-ink-700">
                <c.icon className="text-signal" size={24} aria-hidden />
                <p className="mt-4 text-base font-bold text-slate-100">{c.title}</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{c.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Why Sources Matter */}
      <section className="py-20 border-b border-ink-700/50 bg-ink-900/20">
        <div className="mx-auto max-w-4xl px-6">
           <h2 className="text-center text-3xl font-bold tracking-tight text-slate-100 mb-12">Why Sources Matter</h2>
           
           <div className="overflow-x-auto rounded-xl border border-ink-700 bg-ink-900/50 mb-8 shadow-xl">
             <table className="w-full text-left text-sm whitespace-nowrap sm:whitespace-normal">
               <thead className="bg-ink-800/80 text-slate-300 border-b border-ink-700">
                 <tr>
                   <th className="p-5 font-bold uppercase tracking-wider text-xs">Source</th>
                   <th className="p-5 font-bold uppercase tracking-wider text-xs">Role in Intelligence Picture</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-ink-700/50 text-slate-400">
                 <tr className="hover:bg-ink-800/30 transition"><td className="p-5 font-semibold text-slate-200 flex items-center gap-3"><Landmark size={18} className="text-signal"/> Government</td><td className="p-5">Authoritative meteorological evidence</td></tr>
                 <tr className="hover:bg-ink-800/30 transition"><td className="p-5 font-semibold text-slate-200 flex items-center gap-3"><Globe2 size={18} className="text-signal"/> Weather API</td><td className="p-5">Independent weather measurements</td></tr>
                 <tr className="hover:bg-ink-800/30 transition"><td className="p-5 font-semibold text-slate-200 flex items-center gap-3"><Newspaper size={18} className="text-signal"/> News</td><td className="p-5">Event discovery & corroboration</td></tr>
                 <tr className="hover:bg-ink-800/30 transition"><td className="p-5 font-semibold text-slate-200 flex items-center gap-3"><Users size={18} className="text-signal"/> Social</td><td className="p-5">High-volume local signals</td></tr>
                 <tr className="hover:bg-ink-800/30 transition"><td className="p-5 font-semibold text-slate-200 flex items-center gap-3"><Database size={18} className="text-signal"/> Public datasets</td><td className="p-5">Historical & contextual evidence</td></tr>
                 <tr className="hover:bg-ink-800/30 transition"><td className="p-5 font-semibold text-slate-200 flex items-center gap-3"><Activity size={18} className="text-signal"/> Ground evidence</td><td className="p-5">Local supporting evidence</td></tr>
               </tbody>
             </table>
           </div>
           
           <div className="bg-signal/10 border-l-4 border-signal p-6 rounded-r-xl shadow-md">
             <p className="text-lg font-bold text-slate-100">No single source determines the final event confidence.</p>
           </div>
        </div>
      </section>

      {/* Trust & Security */}
      <section className="py-20 border-b border-ink-700/50 bg-ink-900/40">
        <div className="mx-auto max-w-5xl px-6 text-center">
           <h2 className="text-3xl font-bold text-slate-100 mb-12">Explainable. Evidence-backed. Human-supervised.</h2>
           
           <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-3 text-sm font-bold text-slate-300">
              <div className="bg-ink-800 px-6 py-3 rounded-xl border border-ink-600 shadow-md w-full sm:w-auto">AI analyzes</div>
              <ArrowRight className="text-signal rotate-90 sm:rotate-0" size={20} />
              <div className="bg-ink-800 px-6 py-3 rounded-xl border border-ink-600 shadow-md w-full sm:w-auto">Evidence is compared</div>
              <ArrowRight className="text-signal rotate-90 sm:rotate-0" size={20} />
              <div className="bg-ink-800 px-6 py-3 rounded-xl border border-ink-600 shadow-md w-full sm:w-auto">Confidence is calculated</div>
              <ArrowRight className="text-signal rotate-90 sm:rotate-0" size={20} />
              <div className="bg-signal/10 px-6 py-3 rounded-xl border-2 border-signal text-signal shadow-[0_0_15px_rgba(14,165,233,0.2)] w-full sm:w-auto">Human verifies</div>
           </div>
        </div>
      </section>

      {/* Stats (Prototype Intelligence Snapshot) */}
      <section className="py-20 bg-ink-950">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-100">Prototype Intelligence Snapshot</h2>
            <div className="mt-4 inline-flex items-center gap-2 bg-ink-800 border border-ink-600 px-3 py-1.5 rounded text-xs font-bold text-slate-400 uppercase tracking-widest">
              <span className="h-2 w-2 rounded-full bg-signal"></span>
              Simulated Data
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {[
              { label: "Signals Processed", value: "18,420" },
              { label: "Active Events", value: 42 },
              { label: "Critical Events", value: 6 },
              { label: "States Monitored", value: 18 },
            ].map((s) => (
              <div key={s.label} className="panel p-8 text-center bg-ink-900/50 border border-ink-700 shadow-lg">
                <p className="font-mono text-4xl lg:text-5xl font-black text-signal">{s.value}</p>
                <p className="mt-3 text-xs font-bold uppercase tracking-widest text-slate-400">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-ink-700/50 py-10 text-center bg-ink-900">
        <p className="mx-auto max-w-3xl px-6 text-[11px] leading-relaxed text-slate-500 font-medium">
          Prototype uses simulated/demo intelligence sources. Confidence scores are analytical indicators and do not replace official
          meteorological warnings or authorized disaster-management decisions.
        </p>
      </footer>
    </div>
  );
}
