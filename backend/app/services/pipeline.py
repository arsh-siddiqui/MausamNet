"""Ingestion pipeline — turns a raw signal into intelligence.

Raw signal
  → AI classification
  → duplicate detection
  → trust scoring (with weather/location/time/cross-source evidence)
  → event clustering (attach or create)
  → event aggregate rebuild (fusion, evidence, graph, timeline)
  → alerts + realtime publish

Used by connectors/simulation, ground reports and the manual POST /signals API.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from app.ai.classifier import DemoEventClassifier
from app.ai.clustering import DemoEventClusterer
from app.ai.duplicate import SpatialTemporalDuplicateDetector
from app.ai.fusion import evidence_matrix, explain_components, fuse_event_confidence, fusion_components
from app.ai.trust import DemoTrustEngine
from app.domain import SEVERITY_ORDER
from app.repositories.registry import RepositoryRegistry
from app.repositories.sqlite_repo import utcnow as _utcnow

CLASSIFIER = DemoEventClassifier()
TRUST = DemoTrustEngine()
DUPLICATES = SpatialTemporalDuplicateDetector()
CLUSTERER = DemoEventClusterer(radius_km=60.0, time_window_hours=12.0, min_signals=2)


def _hav(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def weather_evidence(registry: RepositoryRegistry, city: str, occurred_at: dt.datetime, metrics: dict[str, Any]) -> dict[str, Any]:
    """Compare claimed metrics against nearby observations."""
    obs = registry.observations.series_for_city(city, "rainfall_mm", occurred_at - dt.timedelta(hours=6))
    window = [o for o in obs if abs((o["observed_at"] - occurred_at).total_seconds()) <= 3 * 3600]
    peak = max((o["value"] for o in window), default=None)
    score = 0.5
    note = "No nearby observations in window."
    claimed_rain = metrics.get("rainfall_mm")
    if peak is not None:
        if claimed_rain is not None:
            ratio = peak / max(claimed_rain, 1.0)
            score = 0.9 if ratio >= 0.6 else (0.7 if ratio >= 0.3 else 0.45)
            note = f"Observed peak {peak:.1f} mm vs claimed {claimed_rain:.0f} mm."
        elif peak >= 15:
            score = 0.75
            note = f"Observed rainfall {peak:.1f} mm supports wet-weather claim."
    if metrics.get("temp_c") is not None and metrics["temp_c"] >= 39:
        score = max(score, 0.85)
        note = f"Heat claim consistent with sensors." if peak is None else note
    if metrics.get("visibility_km") is not None and metrics["visibility_km"] <= 0.5:
        score = max(score, 0.8)
        note = f"Low-visibility claim plausible."
    return {"score": score, "note": note, "observed_peak_mm": peak}


def location_component(lat: float, lon: float, city: str) -> float:
    from app.connectors.base import CITIES

    known = next((c for c in CITIES if c["city"].lower() == city.lower()), None)
    if known is None:
        return 0.55
    dist = _hav(lat, lon, known["lat"], known["lon"])
    return 0.95 if dist <= 40 else (0.75 if dist <= 120 else 0.5)


def time_component(occurred_at: dt.datetime) -> float:
    age_h = abs((dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - occurred_at).total_seconds()) / 3600
    return 0.95 if age_h <= 24 else (0.8 if age_h <= 72 else 0.55)


def cross_source_agreement(registry: RepositoryRegistry, *, event_type: str, latitude: float, longitude: float, occurred_at: dt.datetime, exclude_id: str | None) -> float:
    since = occurred_at - dt.timedelta(hours=12)
    corpus = registry.signals.candidates_for_duplicate_check(since=since, limit=600)
    cats = {
        s.source_category
        for s in corpus
        if s.id != exclude_id
        and s.event_type == event_type
        and _hav(s.latitude, s.longitude, latitude, longitude) <= 80
    }
    return min(1.0, len(cats) / 5)


class IngestionService:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self.reg = registry
        self.thresholds = None  # loaded lazily (settings store needs session-bound store)

    # ------------------------------------------------------------------
    def ingest(self, raw: dict[str, Any], *, publish_realtime: bool = True) -> dict[str, Any]:
        """Run the full pipeline for one raw signal. Returns summary."""
        from app.settings_store import SettingsStore

        store = SettingsStore(self.reg)
        thresholds = store.risk_thresholds()
        weights = store.trust_weights()

        now = _utcnow()
        occurred_at = raw.get("occurred_at") or now
        if isinstance(occurred_at, str):
            occurred_at = dt.datetime.fromisoformat(occurred_at.replace("Z", "+00:00")).replace(tzinfo=None)
        metrics = raw.get("metrics") or {}

        # 1) classification ------------------------------------------------
        cls = CLASSIFIER.classify(raw.get("headline", ""), raw.get("content", ""), metrics)
        event_type = raw.get("event_type") or cls["event_type"]
        severity = raw.get("severity") or cls["severity"]

        # 2) duplicate detection ---------------------------------------------
        corpus = self.reg.signals.candidates_for_duplicate_check(since=occurred_at - dt.timedelta(hours=48), limit=800)
        dup = DUPLICATES.check(
            {
                "id": None,
                "headline": raw.get("headline", ""),
                "content": raw.get("content", ""),
                "latitude": raw.get("latitude", 0),
                "longitude": raw.get("longitude", 0),
                "occurred_at": occurred_at,
                "media_phash": raw.get("media_phash", ""),
            },
            [s.model_dump() for s in corpus],
        )

        # 3) evidence components for trust ------------------------------------
        wx = weather_evidence(self.reg, raw.get("city", ""), occurred_at, metrics)
        loc = location_component(raw.get("latitude", 0), raw.get("longitude", 0), raw.get("city", ""))
        tim = time_component(occurred_at)
        cross = cross_source_agreement(
            self.reg, event_type=event_type, latitude=raw.get("latitude", 0),
            longitude=raw.get("longitude", 0), occurred_at=occurred_at, exclude_id=None,
        )

        trust = TRUST.score({
            "source_category": raw.get("source_category", "SOCIAL"),
            "headline": raw.get("headline", ""),
            "content": raw.get("content", ""),
            "media_url": raw.get("media_url"),
            "weather_evidence": wx,
            "location_component": loc,
            "time_component": tim,
            "cross_source_agreement": cross,
            "duplicate_score": dup["score"],
            "weights": weights,
        })

        # 4) suspicious flags ---------------------------------------------------
        suspicious_reasons: list[str] = []
        if trust["trust_score"] < thresholds["suspicious_trust_below"]:
            suspicious_reasons.append("Low trust score")
        if dup["score"] >= thresholds["partial_duplicate"] and dup["score"] < thresholds["duplicate_threshold"]:
            suspicious_reasons.append("Similar content detected elsewhere")
        if dup["is_duplicate"]:
            suspicious_reasons.append("Near-duplicate of earlier signal")
        if (metrics.get("rainfall_mm") or 0) > 150 and raw.get("source_category") in ("SOCIAL", "CITIZEN"):
            suspicious_reasons.append("Extraordinary claim from low-reliability source")

        status = "NEW"
        if dup["is_duplicate"]:
            status = "DUPLICATE"
        elif suspicious_reasons:
            status = "SUSPICIOUS"
        elif cls["confidence"] >= 0.4:
            status = "CLASSIFIED"

        signal = self.reg.signals.create({
            "source_id": raw.get("source_id") or {
                "GOVERNMENT": "imd-demo", "WEATHER_API": "wxapi-demo", "NEWS": "news-demo",
                "SOCIAL": "social-demo", "PUBLIC_DATASET": "dataset-demo", "CITIZEN": "ground-demo",
            }.get(raw.get("source_category"), "social-demo"),
            "source_category": raw.get("source_category", "SOCIAL"),
            "headline": raw.get("headline", "")[:300],
            "content": raw.get("content", ""),
            "media_url": raw.get("media_url"),
            "event_type": event_type,
            "severity": severity,
            "status": status,
            "latitude": raw.get("latitude", 0.0),
            "longitude": raw.get("longitude", 0.0),
            "city": raw.get("city", ""),
            "district": raw.get("district", ""),
            "state": raw.get("state", ""),
            "occurred_at": occurred_at,
            "ai_confidence": cls["confidence"],
            "ai_label": cls["event_type"],
            "trust_score": trust["trust_score"],
            "duplicate_of": dup["match_signal_id"] if dup["is_duplicate"] else None,
            "duplicate_score": dup["score"],
            "suspicious": bool(suspicious_reasons) or dup["is_duplicate"],
            "suspicious_reasons": suspicious_reasons,
            "metrics": metrics,
            "explanation": trust["explanation"] + cls["explanation"] + ([f"Duplicate analysis: {dup['reason']}"] if dup["score"] >= 0.3 else []),
        })

        if dup["is_duplicate"]:
            self.reg.alerts.create({
                "type": "DUPLICATE_FOUND",
                "severity": "LOW",
                "title": "Duplicate signal detected",
                "message": f"{signal.headline[:120]} — {dup['reason']}",
                "signal_id": signal.id,
            })

        event_summary = None
        if status != "DUPLICATE":
            event_summary = self._attach_to_event(signal.model_dump(), store=store, publish_realtime=publish_realtime)

        if publish_realtime:
            from app import realtime

            realtime.publish("new_signal", {"signal_id": signal.id, "headline": signal.headline, "source_category": signal.source_category, "city": signal.city})
            if event_summary:
                realtime.publish("event_updated", {"event_id": event_summary["event"].id, "title": event_summary["event"].title})

        self.reg.commit()
        # re-fetch so event_id / status reflect post-clustering state
        refreshed = self.reg.signals.get(signal.id)
        return {
            "signal": refreshed or signal,
            "classification": cls,
            "trust": trust,
            "duplicate": dup,
            "event": event_summary["event"] if event_summary else None,
            "event_created": bool(event_summary and event_summary.get("created")),
        }

    # ------------------------------------------------------------------
    def _attach_to_event(self, signal_dict: dict[str, Any], *, store, publish_realtime: bool) -> dict[str, Any] | None:
        from app.settings_store import SettingsStore  # noqa: F401  (typing clarity)

        open_ev = self.reg.events.open_event_near(
            event_type=signal_dict["event_type"],
            latitude=signal_dict["latitude"],
            longitude=signal_dict["longitude"],
            radius_km=60.0,
            since=signal_dict["occurred_at"] - dt.timedelta(hours=12),
        )
        created = False
        if open_ev is None:
            ev = self.reg.events.create({
                "title": f"{signal_dict['city']} {signal_dict['event_type'].replace('_',' ').title()}",
                "event_type": signal_dict["event_type"],
                "severity": signal_dict["severity"],
                "status": "CANDIDATE",
                "latitude": signal_dict["latitude"],
                "longitude": signal_dict["longitude"],
                "city": signal_dict["city"],
                "district": signal_dict["district"],
                "state": signal_dict["state"],
                "started_at": signal_dict["occurred_at"],
                "latest_at": signal_dict["occurred_at"],
                "signal_count": 0,
                "timeline": [{
                    "at": signal_dict["occurred_at"].isoformat(),
                    "label": "First signal detected",
                    "detail": f"{signal_dict['source_category']} signal: {signal_dict['headline'][:100]}",
                }],
            })
            open_ev = ev
            created = True

        self.reg.signals.set_event([signal_dict["id"]], open_ev.id)
        summary = self.rebuild_event(open_ev.id)
        if created and summary["event"].confidence >= 70:
            self.reg.alerts.create({
                "type": "HIGH_RISK_EVENT",
                "severity": summary["event"].severity,
                "title": f"High-risk event: {summary['event'].title}",
                "message": f"Confidence {summary['event'].confidence:.0f}% with {summary['event'].signal_count} signals.",
                "event_id": summary["event"].id,
            })
        return {"event": summary["event"], "created": created}

    # ------------------------------------------------------------------
    def rebuild_event(self, event_id: str) -> dict[str, Any]:
        """Recompute fusion/confidence/evidence/graph/timeline for an event."""
        from app.settings_store import SettingsStore

        store = SettingsStore(self.reg)
        weights = store.trust_weights()
        ev = self.reg.events.get(event_id)
        if ev is None:
            raise ValueError("Event not found")
        signals = self.reg.signals.ids_for_event(event_id, limit=600)
        dicts = [s.model_dump() for s in signals]

        if not dicts:
            return {"event": ev, "components": {}}

        lats = [d["latitude"] for d in dicts]
        lons = [d["longitude"] for d in dicts]
        clat, clon = sum(lats) / len(lats), sum(lons) / len(lons)

        components = fusion_components(dicts, latitude=clat, longitude=clon, radius_km=60.0)
        confidence = fuse_event_confidence(components)
        avg_trust = sum(d["trust_score"] for d in dicts) / len(dicts)
        severity = max((d["severity"] for d in dicts), key=lambda s: SEVERITY_ORDER.get(s, 0))
        latest = max(d["occurred_at"] for d in dicts)
        started = min(d["occurred_at"] for d in dicts)

        # radius: max distance from centroid (capped)
        radius = min(80.0, max((_hav(clat, clon, d["latitude"], d["longitude"]) for d in dicts), default=10.0)) or 10.0

        # growth rate: signals in last 60m vs the prior 60m
        recent = sum(1 for d in dicts if latest - d["occurred_at"] <= dt.timedelta(hours=1))
        prior = sum(1 for d in dicts if dt.timedelta(hours=1) < latest - d["occurred_at"] <= dt.timedelta(hours=2))
        growth = round(recent / max(prior, 1), 2)

        peak_rain = max((d["metrics"].get("rainfall_mm") or 0) for d in dicts)
        peak_wind = max((d["metrics"].get("wind_kph") or 0) for d in dicts)
        max_temp = max((d["metrics"].get("temp_c") or 0) for d in dicts)

        description = (
            f"Clustered intelligence event near {ev.city}, {ev.state} comprising {len(dicts)} independent signals "
            f"across {len({d['source_category'] for d in dicts})} source categories. Peak reported values: "
            f"{peak_rain:.0f} mm rainfall, {peak_wind:.0f} kph wind. DEMO DATA."
        )

        status = ev.status
        if status in ("CANDIDATE", "ACTIVE"):
            status = "ACTIVE" if confidence >= 60 else "CANDIDATE"

        timeline = list(ev.timeline or [])
        milestone_labels = {1: "AI classification", 4: "Evidence fusion", 8: "High confidence reached"}
        if len(dicts) in milestone_labels:
            timeline.append({"at": latest.isoformat(), "label": milestone_labels[len(dicts)], "detail": f"{len(dicts)} signals fused; confidence {confidence:.0f}%."})
        timeline = timeline[-80:]

        metrics = {
            "growth_rate": growth,
            "peak_rainfall_mm": peak_rain,
            "peak_wind_kph": peak_wind,
            "max_temp_c": max_temp,
            "radius_km": round(radius, 1),
            "source_breakdown": {cat: sum(1 for d in dicts if d["source_category"] == cat) for cat in {d["source_category"] for d in dicts}},
        }

        self.reg.events.update(event_id, {
            "latitude": clat,
            "longitude": clon,
            "severity": severity,
            "status": status,
            "signal_count": len(dicts),
            "confidence": confidence,
            "trust_score": round(avg_trust, 1),
            "latest_at": latest,
            "started_at": started,
            "description": description,
            "fusion": {**components, "confidence": confidence, "explanations": explain_components(components)},
            "evidence": evidence_matrix(dicts),
            "timeline": timeline,
            "metrics": metrics,
        })

        # evidence rows + graph edges
        self.reg.evidence.replace_for_event(event_id, [
            {"event_id": event_id, "category": cat, "strength": m["strength"], "weight": m["weight"], "signal_ids": [], "note": m["note"]}
            for cat, m in evidence_matrix(dicts).items()
        ])
        self.reg.graph.replace_for_event(event_id, self._build_graph_edges(dicts, confidence))

        # related events (same type, nearby, overlapping window)
        candidates = self.reg.events.list_all({"event_type": ev.event_type}, limit=50)
        related = [
            c.id for c in candidates
            if c.id != event_id and _hav(clat, clon, c.latitude, c.longitude) <= 300
            and abs((c.latest_at - latest).total_seconds()) <= 72 * 3600
        ][:3]
        self.reg.events.set_related(event_id, related)

        # anomaly linkage
        for an in self.reg.anomalies.list_all(limit=100):
            if an.event_id is None and an.city == ev.city and an.metric == "RAINFALL" and _hav(clat, clon, an.latitude, an.longitude) <= 80:
                self.reg.anomalies.link_event(an.id, event_id)

        self.reg.commit()
        updated = self.reg.events.get(event_id)
        return {"event": updated, "components": components}

    # ------------------------------------------------------------------
    def _build_graph_edges(self, dicts: list[dict[str, Any]], confidence: float) -> list[dict[str, Any]]:
        cats = {}
        for d in dicts:
            cats.setdefault(d["source_category"], []).append(d["trust_score"])

        edges: list[dict[str, Any]] = []
        for cat, trusts in cats.items():
            node = {
                "GOVERNMENT": "gov",
                "WEATHER_API": "api",
                "NEWS": "news",
                "SOCIAL": "social",
                "PUBLIC_DATASET": "dataset",
                "CITIZEN": "citizen",
            }.get(cat, cat.lower())
            edges.append({"source_node": node, "target_node": "event", "relation": "SUPPORTS", "weight": round(sum(trusts) / len(trusts) / 100, 2)})

        edges.append({"source_node": "obs", "target_node": "gov", "relation": "SUPPORTS", "weight": 0.9})
        edges.append({"source_node": "obs", "target_node": "api", "relation": "SUPPORTS", "weight": 0.85})
        if any(d.get("media_url") for d in dicts):
            social_weight = round(sum(t for t in cats.get("SOCIAL", [60])) / max(len(cats.get("SOCIAL", [1])), 1) / 100, 2)
            edges.append({"source_node": "image", "target_node": "social", "relation": "SUPPORTS", "weight": social_weight})
        for d in dicts:
            if d.get("duplicate_of"):
                edges.append({"source_node": f"sig:{d['id'][:8]}", "target_node": f"sig:{d['duplicate_of'][:8]}", "relation": "DUPLICATE_OF", "weight": round(d.get("duplicate_score", 0), 2)})
        if cats.get("CITIZEN"):
            edges.append({"source_node": "citizen", "target_node": "event", "relation": "LOCATED_NEAR", "weight": 0.7})
        return edges


SIGNAL_TO_NODE = {
    "GOVERNMENT": "IMD / Government",
    "WEATHER_API": "Weather APIs",
    "NEWS": "News",
    "SOCIAL": "Social",
    "PUBLIC_DATASET": "Public Datasets",
    "CITIZEN": "Citizen Ground",
}
