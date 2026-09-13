"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { Activity, UserPlus } from "lucide-react";
import { api, setSession, User } from "@/lib/api";
import { useAuth } from "@/app/providers";

interface TokenResponseShape {
  access_token: string;
  user: User;
}

export default function RegisterPage() {
  const router = useRouter();
  const { refresh } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    organization: "",
    password: "",
    confirm_password: "",
    role: "ANALYST",
  });
  const [error, setError] = useState("");

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const register = useMutation({
    mutationFn: () => api.post<TokenResponseShape>("/auth/register", form),
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
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match");
      return;
    }
    register.mutate();
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-lg">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-signal/15">
            <Activity className="text-signal" size={20} aria-hidden />
          </div>
          <div>
            <p className="text-lg font-bold tracking-tight">MausamNet</p>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-dim">Analyst Registration</p>
          </div>
        </div>

        <div className="panel p-6">
          <h1 className="text-xl font-bold tracking-tight">Create your account</h1>
          <p className="mt-1 text-xs text-dim">Prototype registration — ADMIN role cannot be self-assigned.</p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="full_name" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Full Name</label>
                <input id="full_name" required minLength={2} className="input-base" value={form.full_name} onChange={set("full_name")} placeholder="Priya Sharma" />
              </div>
              <div>
                <label htmlFor="org" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Organization</label>
                <input id="org" className="input-base" value={form.organization} onChange={set("organization")} placeholder="NDMA / IMD / State SDMA" />
              </div>
            </div>
            <div>
              <label htmlFor="reg-email" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Email</label>
              <input id="reg-email" type="email" required className="input-base" value={form.email} onChange={set("email")} placeholder="analyst@agency.gov.in" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="reg-pass" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Password</label>
                <input id="reg-pass" type="password" required minLength={8} className="input-base" value={form.password} onChange={set("password")} placeholder="Min 8 characters" />
              </div>
              <div>
                <label htmlFor="reg-pass2" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Confirm Password</label>
                <input id="reg-pass2" type="password" required minLength={8} className="input-base" value={form.confirm_password} onChange={set("confirm_password")} placeholder="Repeat password" />
              </div>
            </div>
            <div>
              <label htmlFor="role" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-dim">Role</label>
              <select id="role" className="input-base" value={form.role} onChange={set("role")}>
                <option value="ANALYST">ANALYST — monitor & analyze intelligence</option>
                <option value="VERIFIER">VERIFIER — approve / reject events</option>
              </select>
              <p className="mt-1 text-[10px] text-slate-500">ADMIN accounts are provisioned by system administrators only.</p>
            </div>

            {error && (
              <div role="alert" className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs font-medium text-red-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={register.isPending}
              className="focus-ring flex w-full items-center justify-center gap-2 rounded-lg bg-signal px-4 py-3 text-sm font-bold text-ink-950 transition hover:bg-signal-dim disabled:opacity-60"
            >
              {register.isPending ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-950 border-t-transparent" aria-hidden /> : <UserPlus size={16} aria-hidden />}
              Create Account
            </button>
          </form>

          <p className="mt-4 text-center text-xs text-dim">
            Already registered?{" "}
            <Link href="/login" className="font-semibold text-signal hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
