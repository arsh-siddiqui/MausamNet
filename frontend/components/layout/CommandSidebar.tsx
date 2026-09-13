"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ChevronLeft,
  Database,
  FileCheck,
  LayoutDashboard,
  Map,
  Radio,
  Radar,
  Server,
  Settings,
  ShieldCheck,
  Waves,
} from "lucide-react";
import { DemoBadge } from "@/components/DemoBadge";

const NAV = [
  {
    section: "Command Center",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/live-map", label: "Live Intelligence Map", icon: Map },
    ],
  },
  {
    section: "Intelligence",
    items: [
      { href: "/events", label: "Events", icon: Radar },
      { href: "/signals", label: "Signal Explorer", icon: Radio },
      { href: "/media-forensics", label: "Media Forensics", icon: FileCheck },
      { href: "/anomalies", label: "Anomalies", icon: AlertTriangle },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
    ],
  },
  {
    section: "Operations",
    items: [
      { href: "/verification", label: "Verification Center", icon: ShieldCheck },
      { href: "/ground-reports", label: "Ground Reports", icon: Waves },
    ],
  },
  {
    section: "Administration",
    roles: ["ADMIN"],
    items: [
      { href: "/sources", label: "Data Sources", icon: Database },
      { href: "/system", label: "System Health", icon: Server },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function CommandSidebar({ collapsed, onToggle, userRole }: { collapsed: boolean; onToggle: () => void; userRole?: string }) {
  const pathname = usePathname();
  
  // Filter NAV by userRole
  const filteredNav = NAV.filter((group) => {
    if (group.roles && !group.roles.includes(userRole || "")) return false;
    return true;
  });

  return (
    <aside
      className={`flex h-full flex-col border-r border-ink-700/70 bg-ink-900/90 transition-all duration-200 ${collapsed ? "w-16" : "w-64"}`}
      aria-label="Primary navigation"
    >
      <div className="flex items-center gap-2.5 border-b border-ink-700/70 px-4 py-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-signal/15">
          <Activity className="h-4.5 w-4.5 text-signal" size={18} aria-hidden />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-bold tracking-tight text-slate-100">MausamNet</p>
            <p className="truncate text-[9px] font-semibold uppercase tracking-widest text-dim">Weather Intelligence</p>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-4 overflow-y-auto px-2 py-4">
        {filteredNav.map((group) => (
          <div key={group.section}>
            {!collapsed && (
              <p className="mb-1 px-3 text-[10px] font-bold uppercase tracking-widest text-slate-500">{group.section}</p>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      aria-current={active ? "page" : undefined}
                      className={`focus-ring group flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition ${
                        active
                          ? "bg-signal/10 text-signal"
                          : "text-slate-400 hover:bg-ink-800 hover:text-slate-200"
                      }`}
                    >
                      <Icon size={16} className="shrink-0" aria-hidden />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                      {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-signal" aria-hidden />}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="space-y-2 border-t border-ink-700/70 p-3">
        {!collapsed && <DemoBadge compact />}
        <button
          onClick={onToggle}
          className="focus-ring flex w-full items-center justify-center gap-2 rounded-md border border-ink-700 px-2 py-1.5 text-[11px] font-semibold text-dim hover:border-signal/40 hover:text-signal"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft size={14} className={`transition-transform ${collapsed ? "rotate-180" : ""}`} aria-hidden />
          {!collapsed && "Collapse"}
        </button>
      </div>
    </aside>
  );
}
