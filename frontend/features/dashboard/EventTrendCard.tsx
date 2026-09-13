"use client";

import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import { AnalyticsOverview } from "@/types";
import { SectionHeader } from "@/components/primitives";

export function EventTrendCard() {
  const analytics = useQuery<AnalyticsOverview>({
    queryKey: ["analytics", "dashboard-mini"],
    queryFn: () => api.get<AnalyticsOverview>("/analytics/overview?days=10"),
    refetchInterval: 60_000,
  });

  return (
    <div className="panel p-4">
      <SectionHeader title="Event Trend" subtitle="Events & signals · last 10 days" />
      <div className="h-48">
        {analytics.isLoading ? (
          <div className="flex h-full items-center justify-center text-xs text-dim">Loading trend…</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={analytics.data?.event_trend ?? []} margin={{ top: 4, right: 4, bottom: 0, left: -18 }}>
              <defs>
                <linearGradient id="gEvents" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.02} />
                </linearGradient>
                <linearGradient id="gSignals" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1a2941" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="bucket" tick={{ fill: "#64748b", fontSize: 9 }} tickFormatter={(v: string) => v.slice(5)} />
              <YAxis tick={{ fill: "#64748b", fontSize: 9 }} />
              <Tooltip
                contentStyle={{ background: "#111c30", border: "1px solid #243654", borderRadius: 8, fontSize: 11 }}
                labelStyle={{ color: "#94a3b8" }}
              />
              <Area type="monotone" dataKey="signals" stroke="#22c55e" fill="url(#gSignals)" strokeWidth={1.4} name="Signals" />
              <Area type="monotone" dataKey="events" stroke="#38bdf8" fill="url(#gEvents)" strokeWidth={1.6} name="Events" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
