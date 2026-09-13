"""DemoEventClusterer — groups many signals into one unique event.

Clustering keys: event type + spatial proximity (haversine) + temporal
proximity + source spread. Deterministic; a production version would swap
in DBSCAN/HDBSCAN over embedding vectors.
"""
from __future__ import annotations

import datetime as dt
from typing import Any


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def _parse(v: Any) -> dt.datetime | None:
    if isinstance(v, dt.datetime):
        return v
    if isinstance(v, str):
        try:
            return dt.datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


class EventClusterer:
    def cluster(self, signals: list[dict[str, Any]], **kwargs) -> list[list[dict[str, Any]]]:
        raise NotImplementedError


class DemoEventClusterer(EventClusterer):
    """Greedy centroid clustering.

    A signal joins a cluster when:
    - event type matches
    - it is within radius_km of the cluster centroid
    - it is within time_window_hours of the cluster's first signal
    """

    def __init__(self, radius_km: float = 60.0, time_window_hours: float = 12.0, min_signals: int = 2) -> None:
        self.radius_km = radius_km
        self.time_window_hours = time_window_hours
        self.min_signals = min_signals

    def cluster(self, signals: list[dict[str, Any]], **kwargs) -> list[list[dict[str, Any]]]:
        # sort by time so clusters grow chronologically
        def time_key(s: dict[str, Any]):
            return _parse(s.get("occurred_at")) or dt.datetime.max

        ordered = sorted(signals, key=time_key)
        clusters: list[dict[str, Any]] = []

        for sig in ordered:
            etype = sig.get("event_type")
            lat, lon = sig.get("latitude", 0.0), sig.get("longitude", 0.0)
            t = _parse(sig.get("occurred_at"))
            placed = False
            for cl in clusters:
                if cl["event_type"] != etype:
                    continue
                if t and cl["start"] and (t - cl["start"]).total_seconds() / 3600 > self.time_window_hours:
                    continue
                if _haversine_km(lat, lon, cl["centroid_lat"], cl["centroid_lon"]) <= self.radius_km:
                    cl["members"].append(sig)
                    n = len(cl["members"])
                    cl["centroid_lat"] = (cl["centroid_lat"] * (n - 1) + lat) / n
                    cl["centroid_lon"] = (cl["centroid_lon"] * (n - 1) + lon) / n
                    placed = True
                    break
            if not placed:
                clusters.append({
                    "event_type": etype,
                    "centroid_lat": lat,
                    "centroid_lon": lon,
                    "start": t,
                    "end": t,
                    "members": [sig],
                })

        return [c["members"] for c in clusters if len(c["members"]) >= self.min_signals]
