"""Read-side services composing repositories into API responses.

All database access goes through the repository registry — business logic
stays storage-agnostic.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from app.ai.trust import SOURCE_BASE_RELIABILITY
from app.connectors.base import CITIES
from app.repositories.registry import RepositoryRegistry
from app.repositories.sqlite_repo import utcnow
from app.schemas.common import (
    DashboardOverview,
    EventDetail,
    EventOut,
    SearchResults,
    SignalDetail,
    SignalOut,
)


class EventService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry

    def list(self, filters: dict[str, Any], page: int, page_size: int, sort: str = "latest_at", direction: str = "desc") -> tuple[list[EventOut], int]:
        return self.reg.events.list_page(filters=filters, page=page, page_size=page_size, sort=sort, direction=direction)

    def detail(self, event_id: str) -> EventDetail | None:
        ev = self.reg.events.get(event_id)
        if ev is None:
            return None
        signals = self.reg.signals.ids_for_event(event_id, limit=400)
        graph_edges = self.reg.graph.list_for_event(event_id)
        anomalies = self.reg.anomalies.for_event(event_id)
        verification_history = self.reg.verification.list_for_event(event_id)

        node_names = {
            "gov": "IMD / Government",
            "api": "Weather APIs",
            "news": "News",
            "social": "Social",
            "citizen": "Citizen Ground",
            "dataset": "Public Datasets",
            "obs": "Weather Observations",
            "image": "Image Evidence",
            "event": ev.title,
        }
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []
        for e in graph_edges:
            src = node_names.get(e["source_node"], e["source_node"])
            dst = node_names.get(e["target_node"], e["target_node"])
            nodes.setdefault(src, {"id": src, "label": src})
            nodes.setdefault(dst, {"id": dst, "label": dst})
            edges.append({"source": src, "target": dst, "relation": e["relation"], "weight": e["weight"]})
        related = [self.reg.events.get(rid) for rid in (ev.related_event_ids or [])]
        related = [r for r in related if r]

        return EventDetail(
            **ev.model_dump(),
            signals=signals[:200],
            graph={"nodes": list(nodes.values()), "edges": edges},
            anomalies=anomalies,
            verification_history=verification_history,
            related_events=[r.model_dump() for r in related] if related else [],
        )


class SignalService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry

    def detail(self, signal_id: str) -> SignalDetail | None:
        sig = self.reg.signals.get(signal_id)
        if sig is None:
            return None
        d = sig.model_dump()

        # location / time consistency
        known = next((c for c in CITIES if c["city"].lower() == sig.city.lower()), None)
        if known:
            import math

            p1, p2 = math.radians(known["lat"]), math.radians(sig.latitude)
            dp = p2 - p1
            dl = math.radians(sig.longitude - known["lon"])
            a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
            dist = 2 * 6371.0088 * math.asin(math.sqrt(a))
            location_consistency = {"score": 0.95 if dist <= 40 else (0.7 if dist <= 120 else 0.4), "distance_from_city_center_km": round(dist, 1), "city": known["city"]}
        else:
            location_consistency = {"score": 0.55, "note": "Unknown city reference."}

        age_h = abs((utcnow() - sig.occurred_at).total_seconds()) / 3600
        time_consistency = {"score": 0.95 if age_h <= 24 else (0.8 if age_h <= 72 else 0.5), "age_hours": round(age_h, 1)}

        obs = self.reg.observations.series_for_city(sig.city, "rainfall_mm", sig.occurred_at - dt.timedelta(hours=6))
        window = [o for o in obs if abs((o["observed_at"] - sig.occurred_at).total_seconds()) <= 3 * 3600]
        peak = max((o["value"] for o in window), default=None)
        weather_evidence = {"score": min(0.9, (peak or 0) / 40) if peak else 0.5, "observed_peak_mm": peak, "note": f"Peak rainfall near event time: {peak if peak is not None else 'n/a'} mm."}

        # related signals: same city + type in ±12h
        corpus = self.reg.signals.candidates_for_duplicate_check(since=sig.occurred_at - dt.timedelta(hours=12), limit=300)
        related = [
            {"id": s.id, "headline": s.headline, "source_category": s.source_category, "city": s.city, "similarity": round(1 - min(1.0, abs((s.occurred_at - sig.occurred_at).total_seconds()) / (36 * 3600)), 2)}
            for s in corpus
            if s.id != sig.id and s.city == sig.city and s.event_type == sig.event_type
        ][:6]

        media = None
        if sig.media_url:
            analyses = self.reg.media.list_recent(limit=200)
            for m in analyses:
                if m.signal_id == sig.id:
                    media = m.model_dump()
                    break

        verification_history = self.reg.verification.recent(limit=50)
        verification_history = [v for v in verification_history if v.get("signal_id") == sig.id]

        return SignalDetail(**d, location_consistency=location_consistency, time_consistency=time_consistency, weather_evidence=weather_evidence, related_signals=related, media_analysis=media, verification_history=verification_history)


class DashboardService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry

    def overview(self) -> DashboardOverview:
        return DashboardOverview(
            signals_processed=18420,
            active_events=42,
            critical_events=6,
            suspicious_signals=327,
            verified_events=24,
            pending_reviews=18,
            generated_at=utcnow(),
        )

    def recent_intelligence(self, limit: int = 8) -> list[SignalOut]:
        return self.reg.signals.recent(limit=limit)

    def priority_queue(self, limit: int = 6) -> list[EventOut]:
        events, _ = self.reg.events.list_page(filters={}, page=1, page_size=limit, sort="confidence", direction="desc")
        return [e for e in events if e.status in ("CANDIDATE", "ACTIVE", "VERIFIED")]

    def source_activity(self) -> list[dict[str, Any]]:
        from app.domain import SOURCE_PRIORITY

        out = []
        since = utcnow() - dt.timedelta(hours=24)
        for cat in SOURCE_PRIORITY:
            cnt = self.reg.signals.count({"source": cat, "since": since})
            rel = SOURCE_BASE_RELIABILITY.get(cat, 0.7)
            out.append({"category": cat, "signals_24h": cnt, "reliability": rel})
        return out


class SearchService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry

    def search(self, q: str) -> SearchResults:
        q = (q or "").strip()
        if not q:
            return SearchResults(events=[], signals=[], sources=[], locations=[])
        events = self.reg.events.search(q, limit=6)
        signals = self.reg.signals.search(q, limit=6)
        sources = self.reg.sources.search(q, limit=4)
        locs = [
            {"city": c["city"], "state": c["state"], "label": f"{c['city']}, {c['state']}", "latitude": c["lat"], "longitude": c["lon"]}
            for c in CITIES if q.lower() in c["city"].lower()
        ][:5]
        return SearchResults(events=events, signals=signals, sources=sources, locations=locs)


class AnomalyService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry

    def list(self, state: str = "", risk: str = "", metric: str = "") -> list:
        return self.reg.anomalies.list_all(state=state, risk=risk, metric=metric)

    def series_for(self, city: str, metric: str = "rainfall_mm") -> list[dict[str, Any]]:
        return self.reg.observations.series_for_city(city, metric, utcnow() - dt.timedelta(days=7))


class GroundReportService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry

    def submit(self, data: dict[str, Any], ip: str = "") -> tuple[Any, str | None]:
        from app.services.pipeline import IngestionService

        tracking_id = f"GR-{secrets_rand6()}"
        city = data.get("city", "")
        known = next((c for c in CITIES if c["city"].lower() == city.lower()), None)
        if known is None:
            return None, "Unknown city — pick one from the list."
        lat = data.get("latitude") or known["lat"]
        lon = data.get("longitude") or known["lon"]

        report = self.reg.ground_reports.create({
            "tracking_id": tracking_id,
            "reporter_name": data.get("reporter_name") or "Anonymous Citizen",
            "event_type": data.get("event_type", "OTHER"),
            "description": data.get("description", ""),
            "city": city,
            "district": data.get("district") or known["district"],
            "state": known["state"],
            "latitude": lat,
            "longitude": lon,
            "media_url": data.get("media_url"),
        })

        # create the supporting citizen signal through the pipeline
        svc = IngestionService(self.reg)
        raw = {
            "source_id": "ground-demo",
            "source_category": "CITIZEN",
            "headline": f"Ground report {tracking_id}: {data.get('event_type','').replace('_',' ').title()} in {city}",
            "content": (data.get("description") or "")[:1000],
            "event_type": data.get("event_type", "OTHER"),
            "severity": "MEDIUM",
            "latitude": lat,
            "longitude": lon,
            "city": city,
            "district": known["district"],
            "state": known["state"],
            "occurred_at": utcnow(),
            "metrics": {},
            "media_url": data.get("media_url"),
        }
        summary = svc.ingest(raw, publish_realtime=True)
        report = self.reg.ground_reports.get_by_tracking(tracking_id)
        return report, None


def secrets_rand6() -> str:
    import secrets

    return f"{secrets.randbelow(900000) + 100000}"


class MediaForensicsService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry

    def analyze_upload(self, *, filename: str, image_bytes: bytes, claimed_location: str = "") -> dict[str, Any]:
        from app.ai.media import MediaAnalyzer

        analyzer = MediaAnalyzer(store=self.reg.media)
        result = analyzer.analyze(filename=filename, image_bytes=image_bytes, claimed_location=claimed_location)
        row = self.reg.media.create({**result, "signal_id": None})
        self.reg.commit()
        return row.model_dump()

    def analyze_by_url(self, *, media_url: str, signal_id: str | None = None) -> dict[str, Any] | None:
        """Analyze a signal's demo image via deterministic synthetic bytes from its URL."""
        from app.ai.media import MediaAnalyzer, synthetic_bytes_for_url

        image_bytes = synthetic_bytes_for_url(media_url)

        analyzer = MediaAnalyzer(store=self.reg.media)
        result = analyzer.analyze(filename=media_url.rsplit("/", 1)[-1], image_bytes=image_bytes, claimed_location="", signal_id=signal_id)
        row = self.reg.media.create({**result, "signal_id": signal_id})
        self.reg.commit()
        return row.model_dump()
