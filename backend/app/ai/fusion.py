"""Evidence fusion — combines heterogeneous signals into event confidence.

Weights each source category by reliability and support strength, checks
spatial/temporal coherence of member signals, then produces a fused
confidence plus the Evidence Matrix used across the UI.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from app.domain import SOURCE_PRIORITY

SOURCE_RELIABILITY = {
    "GOVERNMENT": 0.98,
    "WEATHER_API": 0.93,
    "PUBLIC_DATASET": 0.90,
    "NEWS": 0.87,
    "SOCIAL": 0.74,
    "CITIZEN": 0.62,
}


def fusion_components(
    signals: list[dict[str, Any]],
    *,
    latitude: float,
    longitude: float,
    radius_km: float = 60.0,
) -> dict[str, float]:
    """Meteorological / spatial / temporal / source-reliability / media /
    cross-source agreement components in [0,1]."""
    import math

    if not signals:
        return {
            "meteorological": 0.0,
            "spatial_consistency": 0.0,
            "temporal_consistency": 0.0,
            "source_reliability": 0.0,
            "media_authenticity": 0.5,
            "cross_source_agreement": 0.0,
        }

    def hav(lat1, lon1, lat2, lon2):
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = p2 - p1, math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * 6371.0088 * math.asin(math.sqrt(a))

    # meteorological evidence: share of gov/api/dataset signals with metrics
    meteo = [s for s in signals if s.get("source_category") in ("GOVERNMENT", "WEATHER_API", "PUBLIC_DATASET")]
    meteo_score = min(1.0, len(meteo) / 4 + (0.15 if any((s.get("metrics") or {}) for s in meteo) else 0))

    # spatial: fraction of signals within radius of centroid
    n = len(signals)
    clat = sum(s.get("latitude", 0) for s in signals) / n
    clon = sum(s.get("longitude", 0) for s in signals) / n
    within = sum(1 for s in signals if hav(clat, clon, s.get("latitude", 0), s.get("longitude", 0)) <= radius_km)
    spatial = within / n

    # temporal: fraction within 6h of the median time
    times = sorted([_parse(s.get("occurred_at")) for s in signals if _parse(s.get("occurred_at"))])
    temporal = 1.0
    if times:
        median = times[len(times) // 2]
        within_t = sum(1 for t in times if abs((t - median).total_seconds()) / 3600 <= 6)
        temporal = within_t / len(times)

    # source reliability: mean baseline of member categories, weighted by count
    rel = sum(SOURCE_RELIABILITY.get(s.get("source_category"), 0.6) for s in signals) / n

    # media authenticity: share of signals with media that are not suspicious
    with_media = [s for s in signals if s.get("media_url")]
    media_score = 0.55
    if with_media:
        clean = sum(1 for s in with_media if not s.get("suspicious"))
        media_score = 0.55 + 0.4 * (clean / len(with_media))

    # cross-source agreement: distinct categories present
    cats = {s.get("source_category") for s in signals}
    cross = min(1.0, len(cats) / 5)

    return {
        "meteorological": round(meteo_score, 3),
        "spatial_consistency": round(spatial, 3),
        "temporal_consistency": round(temporal, 3),
        "source_reliability": round(rel, 3),
        "media_authenticity": round(media_score, 3),
        "cross_source_agreement": round(cross, 3),
    }


def fuse_event_confidence(components: dict[str, float], weights: dict[str, float] | None = None) -> float:
    weights = weights or {
        "meteorological": 0.25,
        "spatial_consistency": 0.15,
        "temporal_consistency": 0.10,
        "source_reliability": 0.20,
        "media_authenticity": 0.10,
        "cross_source_agreement": 0.20,
    }
    total = sum(components.get(k, 0) * w for k, w in weights.items())
    return round(max(0.05, min(0.99, total)) * 100, 1)


def evidence_matrix(signals: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per-category strength for the Evidence Matrix UI."""
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for s in signals:
        by_cat.setdefault(s.get("source_category", "OTHER"), []).append(s)

    matrix: dict[str, dict[str, Any]] = {}
    for cat in SOURCE_PRIORITY:
        items = by_cat.get(cat, [])
        if not items:
            matrix[cat] = {"strength": "ABSENT", "weight": 0.0, "count": 0, "note": "No signals from this category."}
            continue
        rel = SOURCE_RELIABILITY.get(cat, 0.6)
        avg_trust = sum(s.get("trust_score", 0) for s in items) / len(items)
        strength = "STRONG" if (rel >= 0.85 and avg_trust >= 70) or len(items) >= 25 else ("SUPPORTING" if avg_trust >= 55 or len(items) >= 5 else "WEAK")
        matrix[cat] = {
            "strength": strength,
            "weight": round(rel * avg_trust / 100, 3),
            "count": len(items),
            "note": f"{len(items)} signal(s), avg trust {avg_trust:.0f}.",
        }
    return matrix


def explain_components(components: dict[str, float]) -> list[str]:
    out: list[str] = []
    checks = [
        ("meteorological", 0.6, "✓ Strong meteorological evidence", "⚠ Meteorological evidence limited"),
        ("cross_source_agreement", 0.6, "✓ Multiple independent source categories agree", "⚠ Few independent source categories"),
        ("spatial_consistency", 0.7, "✓ Spatial clustering detected", "⚠ Signals geographically scattered"),
        ("temporal_consistency", 0.7, "✓ Time alignment confirmed", "⚠ Signals spread over a long window"),
        ("source_reliability", 0.75, "✓ Member sources are reliable", "⚠ Member sources vary in reliability"),
        ("media_authenticity", 0.8, "✓ No major duplicate media found", "⚠ Media authenticity needs review"),
    ]
    for key, threshold, ok, warn in checks:
        v = components.get(key, 0)
        out.append(ok if v >= threshold else warn)
    return out


def _parse(v: Any) -> dt.datetime | None:
    if isinstance(v, dt.datetime):
        return v
    if isinstance(v, str):
        try:
            return dt.datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None
