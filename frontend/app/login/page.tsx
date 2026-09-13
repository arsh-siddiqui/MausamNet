"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { Activity, LogIn, Rocket } from "lucide-react";
import { api, DemoAccount, setSession, User } from "@/lib/api";
import { useAuth } from "@/app/providers";
import { DemoBadge } from "@/components/DemoBadge";

interface TokenResponseShape {
  access_token: string;
  refresh_token: string;
  user: User;
}

const FALLBACK_DEMOS: DemoAccount[] = [
  { email: "analyst@mausamnet.demo", password: "", role: "ANALYST", label: "Launch Analyst Demo" },
  { email: "verifier@mausamnet.demo", password: "", role: "VERIFIER", label: "Launch Verifier Demo" },
  { email: "admin@mausamnet.demo", password: "", role: "ADMIN", label: "Launch Admin Demo" },
];

/** Minimal India grid visual for the left panel background. */
function MiniMap() {
  return (
    <svg viewBox="0 0 300 260" className="h-full w-full opacity-30" aria-hidden>
      <defs>
        <pattern id="mgrid" width="24" height="24" patternUnits="userSpaceOnUse">
          <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#1a2941" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="300" height="260" fill="url(#mgrid)" />
      <path d="M60 60 L105 45 L150 52 L185 40 L225 55 L245 82 L272 92 L290 118 L278 148 L252 175 L232 206 L205 232 L180 242 L160 220 L135 196 L105 172 L84 136 L68 100 Z" fill="rgba(56,189,248,0.06)" stroke="#243654" strokeWidth="1.2" />
      <circle cx="150" cy="110" r="6" fill="#ef4444" opacity="0.85" />
      <circle cx="120" cy="150" r="4" fill="#f97316" opacity="0.8" />
      <circle cx="205" cy="90" r="4" fill="#38bdf8" opacity="0.8" />
      <circle cx="185" cy="180" r="4" fill="#22c55e" opacity="0.8" />
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const { refresh } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [demoList, setDemoList] = useState<DemoAccount[]>(FALLBACK_DEMOS);

  useEffect(() => {
    api
      .get<DemoAccount[]>("/auth/demo-accounts")
      .then(setDemoList)
      .catch(() => setDemoList(FALLBACK_DEMOS));
  }, []);

  const login = useMutation({
    mutationFn: (creds: { email: string; password: string }) => api.post<TokenResponseShape>("/auth/login", creds),
    onSuccess: (data) => {
      setSession(data.access_token, data.user);
      refresh();
      router.push("/dashboard");
    },
    onError: (e: Error) => setError(e.message),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    login.mutate({ email, password });
  };

  const demoLogin = (acct: DemoAccount) => {
    setError("");
    login.mutate({ email: acct.email, password: acct.password });
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Left brand panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-ink-900 p-10 lg:flex">
        <div className="absolute inset-0">
          <MiniMap />
        </div>
        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-signal/15">
              <Activity className="text-signal" size={22} aria-hidden />
            </div>
            <div>
              <p className="text-lg font-bold tracking-tight">MausamNet</p>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-dim">National Weather Intelligence</p>
            </div>
          </div>
        </div>
        <div className="relative max-w-md">
          <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-slate-50">
            Turning fragmented weather signals into trusted, actionable intelligence.
          </h1>
          <p className="mt-4 text-sm leading-relaxed text-slate-400">
            Multi-source fusion · AI event intelligence · Explainable trust scoring · Human verification
          </p>
          <div className="mt-6">
            <DemoBadge compact />
          </div>
        </div>
        <p className="relative text-[10px] text-slate-500">National Weather Intelligence & Verification Platform</p>
      </div>

      {/* Right form */}
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="mb-6 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-signal/15">
              <Activity className="text-signal" size={20} aria-hidden />
            </div>
            <p className="text-lg font-bold">MausamNet</p>
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Sign in to the Command Center</h2>
          <p className="mt-1 text-sm text-dim">Authorized analysts & verifiers only.</p>

          <form onSubmit={submit} className="mt-8 space-y-4">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Email</label>
              <input id="email" type="email" required autoComplete="email" className="input-base" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@gov.in" />
            </div>
            <div>
              <label htmlFor="password" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Password</label>
              <input id="password" type="password" required autoComplete="current-password" className="input-base" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-xs text-slate-400">
                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="h-3.5 w-3.5 rounded border-ink-500 bg-ink-850 accent-signal" />
                Remember me
              </label>
              <span className="cursor-not-allowed text-xs text-slate-600" title="Placeholder for production deployment">Forgot password?</span>
            </div>
            {error && (
              <div role="alert" className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs font-medium text-red-400">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={login.isPending}
              className="focus-ring flex w-full items-center justify-center gap-2 rounded-lg bg-signal px-4 py-3 text-sm font-bold text-ink-950 transition hover:bg-signal-dim disabled:opacity-60"
            >
              {login.isPending ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-950 border-t-transparent" aria-hidden /> : <LogIn size={16} aria-hidden />}
              Sign In
            </button>
          </form>

          <div className="mt-6 flex items-center justify-between text-xs">
            <span className="text-dim">New analyst?</span>
            <Link href="/register" className="font-semibold text-signal hover:underline">Create an account</Link>
          </div>

          <div className="mt-8 rounded-lg border border-ink-700 p-4">
            <p className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300">
              <Rocket size={13} className="text-amber-400" aria-hidden /> Demo Access
            </p>
            <div className="grid gap-2">
              {demoList.map((d) => (
                <button
                  key={d.role}
                  onClick={() => (d.password ? demoLogin(d) : setError("Demo credentials unavailable — is the backend running?"))}
                  disabled={login.isPending}
                  className="focus-ring flex items-center justify-between rounded-md border border-ink-600 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-signal hover:text-signal disabled:opacity-50"
                >
                  {d.label}
                  <span className="rounded border border-signal/40 bg-signal/10 px-1.5 py-0.5 text-[9px] font-bold text-signal">{d.role}</span>
                </button>
              ))}
            </div>
            <p className="mt-2 text-[10px] text-slate-500">Demo credentials are provisioned by backend configuration (no hard-coded secrets).</p>
          </div>
        </div>
      </div>
    </div>
  );
}
