"""Analytics service — all figures derived from live repository queries so
charts respond to filters and simulation updates."""
from __future__ import annotations

import datetime as dt
from typing import Any

from app.ai.trust import SOURCE_BASE_RELIABILITY
from app.domain import EVENT_TYPE_LABELS, SOURCE_PRIORITY
from app.repositories.registry import RepositoryRegistry
from app.repositories.sqlite_repo import utcnow
from app.schemas.common import (
    AnalyticsOverview,
    EventTrendPoint,
    SourceReliabilityRow,
    StateRow,
)


class AnalyticsService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry

    def overview(self, *, state: str = "", event_type: str = "", days: int = 14) -> AnalyticsOverview:
        filters: dict[str, Any] = {}
        if state:
            filters["state"] = state
        if event_type:
            filters["event_type"] = event_type

        since = utcnow() - dt.timedelta(days=days)
        events = self.reg.events.list_all(filters, limit=600)
        events = [e for e in events if e.started_at >= since or e.status in ("ACTIVE", "CANDIDATE", "VERIFIED")]

        # ---- SQL aggregates over signals -------------------------------------
        agg = self.reg.signals.analytics_aggregates(filters)
        by_state_sig = agg["by_state"]
        by_day_suspicious = agg["by_day_suspicious"]
        by_source = agg["by_source"]

        # ---- daily buckets -----------------------------------------------------
        buckets: dict[str, dict[str, int]] = {}
        for i in range(days - 1, -1, -1):
            day = (utcnow() - dt.timedelta(days=i)).date().isoformat()
            buckets[day] = {"events": 0, "signals": 0}
        for e in events:
            day = e.started_at.date().isoformat()
            if day in buckets:
                buckets[day]["events"] += 1
        by_day_signals = self.reg.signals.count_by_day(days=days, filters=filters)
        for day in buckets:
            buckets[day]["signals"] = by_day_signals.get(day, 0)
        trend = [EventTrendPoint(bucket=day, events=vals["events"], signals=vals["signals"]) for day, vals in sorted(buckets.items())]

        # ---- state ranking ------------------------------------------------------
        state_map: dict[str, dict[str, Any]] = {}
        for e in events:
            row = state_map.setdefault(e.state, {"events": 0, "verified": 0, "critical": 0, "conf_sum": 0.0, "signals": 0, "suspicious": 0})
            row["events"] += 1
            row["verified"] += 1 if e.status == "VERIFIED" else 0
            row["critical"] += 1 if e.severity in ("HIGH", "CRITICAL") else 0
            row["conf_sum"] += e.confidence
        for st, srow in by_state_sig.items():
            row = state_map.setdefault(st, {"events": 0, "verified": 0, "critical": 0, "conf_sum": 0.0, "signals": 0, "suspicious": 0})
            row["signals"] = srow["signals"]
            row["suspicious"] = srow["suspicious"]

        state_rows: list[StateRow] = []
        for st, row in state_map.items():
            n_sig = row["signals"]
            state_rows.append(StateRow(
                state=st,
                signals=n_sig,
                events=row["events"],
                verified_pct=round(100 * row["verified"] / row["events"], 1) if row["events"] else 0.0,
                suspicious_pct=round(100 * row["suspicious"] / n_sig, 1) if n_sig else 0.0,
                critical=row["critical"],
                avg_confidence=round(row["conf_sum"] / row["events"], 1) if row["events"] else 0.0,
            ))
        state_rows.sort(key=lambda r: (r.signals, r.events), reverse=True)

        # ---- categories ----------------------------------------------------------
        cat_map: dict[str, int] = {}
        for e in events:
            cat_map[e.event_type] = cat_map.get(e.event_type, 0) + 1
        event_categories = [
            {"name": EVENT_TYPE_LABELS.get(k, k), "value": v} for k, v in sorted(cat_map.items(), key=lambda kv: -kv[1])
        ]

        # ---- verification rate -----------------------------------------------------
        ver_buckets = {day: {"events": 0, "signals": 0} for day in buckets}
        for e in events:
            if e.status == "VERIFIED":
                day = e.latest_at.date().isoformat()
                if day in ver_buckets:
                    ver_buckets[day]["events"] += 1
        verification_rate = [EventTrendPoint(bucket=day, **vals) for day, vals in sorted(ver_buckets.items())]

        # ---- suspicious trend ---------------------------------------------------------
        suspicious_trend = [EventTrendPoint(bucket=day, events=0, signals=by_day_suspicious.get(day, 0)) for day in sorted(buckets)]

        # ---- source reliability ----------------------------------------------------------
        source_reliability = []
        for cat in SOURCE_PRIORITY:
            row = by_source.get(cat, {"n": 0, "verified": 0, "suspicious": 0, "trust_sum": 0.0})
            n = row["n"]
            source_reliability.append(SourceReliabilityRow(
                category=cat,
                signals=n,
                verified_pct=round(100 * row["verified"] / n, 1) if n else 0.0,
                suspicious_pct=round(100 * row["suspicious"] / n, 1) if n else 0.0,
                avg_trust=round(row["trust_sum"] / n, 1) if n else 0.0,
                reliability=round(100 * SOURCE_BASE_RELIABILITY.get(cat, 0.7), 0),
            ))

        # ---- hourly + severity ---------------------------------------------------------------
        hour_map = {h: 0 for h in range(24)}
        for e in events:
            hour_map[e.started_at.hour] += 1
        hourly = [{"hour": f"{h:02d}:00", "events": hour_map[h]} for h in range(24)]

        sev_map = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for e in events:
            sev_map[e.severity] = sev_map.get(e.severity, 0) + 1
        severity_distribution = [{"severity": k, "count": v} for k, v in sev_map.items()]

        return AnalyticsOverview(
            event_trend=trend,
            state_ranking=state_rows[:12],
            event_categories=event_categories,
            verification_rate=verification_rate,
            suspicious_trend=suspicious_trend,
            source_reliability=source_reliability,
            hourly_distribution=hourly,
            severity_distribution=severity_distribution,
            states=state_rows,
        )
