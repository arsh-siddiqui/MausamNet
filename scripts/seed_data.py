"""Deterministic demo data generation for MausamNet seeding.

Uses a fixed RNG seed so every fresh database has identical demo content —
critical for reproducible judge demos and tests.
"""
from __future__ import annotations

import datetime as dt
import random

from app.connectors.base import CITIES
from app.domain import EVENT_TYPES, SOURCE_LABELS, SOURCE_PRIORITY

SOURCE_DEFAULTS = [
    {"id": "imd-demo", "name": "Government Weather (IMD Demo)", "category": "GOVERNMENT", "mode": "DEMO", "status": "OPERATIONAL", "reliability": 0.98, "signals_per_day": 240, "latency_ms": 45},
    {"id": "wxapi-demo", "name": "Weather APIs (Demo)", "category": "WEATHER_API", "mode": "DEMO", "status": "OPERATIONAL", "reliability": 0.93, "signals_per_day": 1850, "latency_ms": 120},
    {"id": "dataset-demo", "name": "Public Datasets (Demo)", "category": "PUBLIC_DATASET", "mode": "DEMO", "status": "OPERATIONAL", "reliability": 0.90, "signals_per_day": 420, "latency_ms": 200},
    {"id": "news-demo", "name": "News Intelligence (Demo)", "category": "NEWS", "mode": "DEMO", "status": "OPERATIONAL", "reliability": 0.87, "signals_per_day": 610, "latency_ms": 350},
    {"id": "social-demo", "name": "Social Intelligence (Demo)", "category": "SOCIAL", "mode": "DEMO", "status": "OPERATIONAL", "reliability": 0.74, "signals_per_day": 2400, "latency_ms": 500},
    {"id": "ground-demo", "name": "Ground Evidence (Demo)", "category": "CITIZEN", "mode": "DEMO", "status": "OPERATIONAL", "reliability": 0.62, "signals_per_day": 120, "latency_ms": 800},
]


def generate_observations(days: int = 21, rng: random.Random | None = None) -> list[dict]:
    rng = rng or random.Random(7)
    rows = []
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    for city in CITIES:
        base_rain = rng.uniform(2, 12)
        monsoonish = city["state"] in ("Maharashtra", "Kerala", "Karnataka", "Goa", "Assam", "West Bengal", "Odisha")
        for d in range(days, -1, -1):
            for hour in (6, 14, 22):
                t = now - dt.timedelta(days=d)
                t = t.replace(hour=hour, minute=rng.randrange(0, 59))
                season_factor = 1.0
                if monsoonish and now.month in (6, 7, 8, 9):
                    season_factor = 2.2
                rainfall = max(0.0, rng.gauss(base_rain * season_factor, 4))
                # Mumbai: inject the signature anomaly on the final day
                if city["city"] == "Mumbai" and d == 0:
                    rainfall = 96.0 if hour == 14 else 42.0
                rows.append({
                    "city": city["city"], "district": city["district"], "state": city["state"],
                    "latitude": city["lat"], "longitude": city["lon"],
                    "observed_at": t,
                    "rainfall_mm": round(rainfall, 1),
                    "temp_c": round(rng.gauss(31, 4), 1),
                    "wind_kph": round(abs(rng.gauss(14, 6)), 1),
                    "humidity": round(min(99, max(20, rng.gauss(70, 15))), 0),
                    "visibility_km": round(min(10, max(0.05, rng.gauss(6, 3))), 2),
                })
    return rows


def generate_signals(count: int, observations: list[dict], rng: random.Random | None = None) -> list[dict]:
    """Generate classified/trust-scored signals across 14 days, clustered by city/time."""
    from app.ai.classifier import DemoEventClassifier
    from app.ai.trust import DemoTrustEngine

    rng = rng or random.Random(11)
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    classifier = DemoEventClassifier()
    trust_engine = DemoTrustEngine()

    # observation lookup for weather evidence
    rain_by_city: dict[str, list[tuple[dt.datetime, float]]] = {}
    for o in observations:
        rain_by_city.setdefault(o["city"], []).append((o["observed_at"], o["rainfall_mm"]))

    def weather_score(city: str, t: dt.datetime, metrics: dict) -> float:
        window = [(ot, v) for ot, v in rain_by_city.get(city, []) if abs((ot - t).total_seconds()) <= 3 * 3600]
        peak = max((v for _, v in window), default=None)
        claimed = metrics.get("rainfall_mm")
        if peak is not None and claimed is not None:
            return 0.9 if peak / max(claimed, 1) >= 0.6 else 0.6
        if peak is not None and peak >= 15:
            return 0.75
        return 0.5

    rows = []
    for i in range(count):
        city = rng.choice(CITIES)
        # 30% of signals belong to "burst clusters" (hotspots)
        if rng.random() < 0.3:
            city = rng.choice(CITIES[:8])
        t = now - dt.timedelta(hours=rng.uniform(0, 14 * 24))
        if rng.random() < 0.5:
            t = t.replace(minute=rng.randrange(0, 60))
        ev = rng.choice(EVENT_TYPES[:-1])
        sev = rng.choices(["LOW", "MEDIUM", "HIGH", "CRITICAL"], weights=[0.3, 0.4, 0.2, 0.1])[0]
        metrics: dict = {}
        if ev in ("RAINFALL", "FLOOD"):
            metrics["rainfall_mm"] = round({"LOW": 10, "MEDIUM": 30, "HIGH": 70, "CRITICAL": 130}[sev] * (0.8 + 0.4 * rng.random()), 1)
        elif ev == "THUNDERSTORM":
            metrics["wind_kph"] = round({"LOW": 30, "MEDIUM": 48, "HIGH": 68, "CRITICAL": 88}[sev], 0)
        elif ev == "HEATWAVE":
            metrics["temp_c"] = round({"LOW": 39, "MEDIUM": 41, "HIGH": 43, "CRITICAL": 45}[sev], 1)
        elif ev == "FOG":
            metrics["visibility_km"] = round({"LOW": 0.9, "MEDIUM": 0.4, "HIGH": 0.18, "CRITICAL": 0.06}[sev], 2)
        elif ev == "DUST_STORM":
            metrics["wind_kph"] = round({"LOW": 35, "MEDIUM": 52, "HIGH": 72, "CRITICAL": 92}[sev], 0)
        elif ev == "STRONG_WIND":
            metrics["wind_kph"] = round({"LOW": 40, "MEDIUM": 56, "HIGH": 76, "CRITICAL": 96}[sev], 0)

        cat = rng.choices(SOURCE_PRIORITY, weights=[0.18, 0.22, 0.10, 0.15, 0.25, 0.10])[0]
        label = ev.replace("_", " ").title()
        headline_templates = {
            "GOVERNMENT": f"IMD {'orange' if sev in ('HIGH','CRITICAL') else 'yellow'} alert: {label} over {city['city']}, {city['state']}",
            "WEATHER_API": f"Model output: {label} near {city['city']} — significant signatures",
            "PUBLIC_DATASET": f"Station observation {city['city']}: {label} parameters logged",
            "NEWS": f"{city['city']}: {label} disrupts normal life, authorities respond",
            "SOCIAL": f"Multiple reports of {label} from {city['city']} residents",
            "CITIZEN": f"Ground observation: {label} in {city['city']} area",
        }
        headline = headline_templates[cat]

        cls = classifier.classify(headline, "", metrics)
        wx = weather_score(city["city"], t, metrics)
        cross = 0.6 if city["tier"] == 1 else 0.35
        trust = trust_engine.score({
            "source_category": cat, "headline": headline, "content": "",
            "media_url": None, "weather_evidence": {"score": wx},
            "location_component": 0.9, "time_component": 0.9,
            "cross_source_agreement": cross, "duplicate_score": 0.1,
        })

        dup_roll = rng.random()
        is_dup = dup_roll < 0.07
        suspicious = trust["trust_score"] < 55 or (dup_roll >= 0.07 and dup_roll < 0.12 and cat in ("SOCIAL", "NEWS"))

        rows.append({
            "source_id": {"GOVERNMENT": "imd-demo", "WEATHER_API": "wxapi-demo", "PUBLIC_DATASET": "dataset-demo", "NEWS": "news-demo", "SOCIAL": "social-demo", "CITIZEN": "ground-demo"}[cat],
            "source_category": cat,
            "headline": headline,
            "content": f"Simulated {SOURCE_LABELS.get(cat, cat).lower()} signal for {city['city']}. DEMO DATA.",
            "media_url": f"https://demo.mausamnet.in/media/{rng.randrange(1,60):03d}.jpg" if (cat == "SOCIAL" and rng.random() < 0.4) else None,
            "event_type": ev,
            "severity": sev,
            "status": "DUPLICATE" if is_dup else ("SUSPICIOUS" if suspicious else "CLASSIFIED"),
            "latitude": city["lat"] + rng.uniform(-0.08, 0.08),
            "longitude": city["lon"] + rng.uniform(-0.08, 0.08),
            "city": city["city"],
            "district": city["district"],
            "state": city["state"],
            "occurred_at": t,
            "ingested_at": t + dt.timedelta(minutes=rng.uniform(1, 20)),
            "ai_confidence": cls["confidence"],
            "ai_label": cls["event_type"],
            "trust_score": trust["trust_score"],
            "duplicate_of": None,
            "duplicate_score": round(0.8 + 0.15 * rng.random(), 2) if is_dup else round(rng.uniform(0.05, 0.45), 2),
            "suspicious": suspicious,
            "suspicious_reasons": (["Low trust score"] if trust["trust_score"] < 55 else []) + (["Similar content detected elsewhere"] if suspicious and trust["trust_score"] >= 55 else []),
            "metrics": metrics,
            "event_id": None,
            "explanation": trust["explanation"],
        })
    return rows


def build_clusters(signals: list[dict], rng: random.Random | None = None, min_signals: int = 7) -> list[list[dict]]:
    from app.ai.clustering import DemoEventClusterer

    rng = rng or random.Random(23)
    clusterer = DemoEventClusterer(radius_km=90, time_window_hours=20, min_signals=min_signals)
    return clusterer.cluster(signals)


def generate_alerts(events: list, rng: random.Random | None = None) -> list[dict]:
    rng = rng or random.Random(31)
    rows = []
    for e in events[:12]:
        if e.severity in ("HIGH", "CRITICAL"):
            rows.append({
                "type": "HIGH_RISK_EVENT", "severity": e.severity,
                "title": f"High-risk event: {e.title}",
                "message": f"Confidence {e.confidence:.0f}% with {e.signal_count} signals — {e.city}, {e.state}.",
                "event_id": e.id, "created_at": e.latest_at,
            })
    return rows
