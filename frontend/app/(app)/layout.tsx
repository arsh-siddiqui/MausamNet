"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CommandSidebar } from "@/components/layout/CommandSidebar";
import { TopNavigation } from "@/components/layout/TopNavigation";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { AlertFeed } from "@/components/layout/AlertFeed";
import { useAuth } from "@/app/providers";
import { useRealtime } from "@/hooks/useRealtime";
import { LoadingState } from "@/components/primitives";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, ready } = useAuth();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);

  useRealtime(!!user);

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, user, router]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!ready) return <LoadingState label="Initializing command center…" />;
  if (!user) return <LoadingState label="Redirecting to sign-in…" />;

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="hidden md:block">
        <CommandSidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} userRole={user.role} />
      </div>
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavigation onOpenSearch={() => setPaletteOpen(true)} user={user} />
        <main className="min-h-0 flex-1 overflow-y-auto p-4 lg:p-6">{children}</main>
        <footer className="border-t border-ink-700/50 px-4 py-2 text-[10px] leading-relaxed text-slate-500">
          Data sources are continuously updated. Confidence scores are analytical indicators and do not replace official meteorological warnings or authorized disaster-management decisions.
        </footer>
      </div>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      <AlertFeed />
    </div>
  );
}
