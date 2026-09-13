"""External data connector abstraction.

Every integration point (IMD, weather APIs, news, social, datasets) is a
pluggable connector exposing connect/fetch/normalize/health_check. Demo
connectors generate deterministic simulated data; adding a real connector
means implementing the same interface and registering it in FACTORY.
"""
from __future__ import annotations

import datetime as dt
import random
from typing import Any, Protocol

from app.domain import EVENT_TYPES, SEVERITIES

# ---------------------------------------------------------------- catalogue
# Real Indian city catalogue used by connectors + seed. (lat, lon) approx.
CITIES: list[dict[str, Any]] = [
    {"city": "Mumbai", "district": "Mumbai Suburban", "state": "Maharashtra", "lat": 19.076, "lon": 72.8777, "tier": 1},
    {"city": "Pune", "district": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "tier": 1},
    {"city": "Nagpur", "district": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "tier": 2},
    {"city": "Nashik", "district": "Nashik", "state": "Maharashtra", "lat": 19.9975, "lon": 73.7898, "tier": 2},
    {"city": "Delhi", "district": "New Delhi", "state": "Delhi", "lat": 28.6139, "lon": 77.209, "tier": 1},
    {"city": "Gurugram", "district": "Gurugram", "state": "Haryana", "lat": 28.4595, "lon": 77.0266, "tier": 2},
    {"city": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714, "tier": 1},
    {"city": "Surat", "district": "Surat", "state": "Gujarat", "lat": 21.1702, "lon": 72.8311, "tier": 2},
    {"city": "Jaipur", "district": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "tier": 2},
    {"city": "Bengaluru", "district": "Bengaluru Urban", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946, "tier": 1},
    {"city": "Hubballi", "district": "Dharwad", "state": "Karnataka", "lat": 15.3647, "lon": 75.124, "tier": 3},
    {"city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "lat": 17.385, "lon": 78.4867, "tier": 1},
    {"city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "tier": 1},
    {"city": "Coimbatore", "district": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lon": 76.9558, "tier": 3},
    {"city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639, "tier": 1},
    {"city": "Siliguri", "district": "Darjeeling", "state": "West Bengal", "lat": 26.7271, "lon": 88.3953, "tier": 3},
    {"city": "Kochi", "district": "Ernakulam", "state": "Kerala", "lat": 9.9312, "lon": 76.2673, "tier": 2},
    {"city": "Thiruvananthapuram", "district": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366, "tier": 3},
    {"city": "Bhubaneswar", "district": "Khordha", "state": "Odisha", "lat": 20.2961, "lon": 85.8245, "tier": 2},
    {"city": "Guwahati", "district": "Kamrup Metropolitan", "state": "Assam", "lat": 26.1445, "lon": 91.7362, "tier": 2},
    {"city": "Lucknow", "district": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462, "tier": 2},
    {"city": "Varanasi", "district": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739, "tier": 3},
    {"city": "Patna", "district": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376, "tier": 2},
    {"city": "Srinagar", "district": "Srinagar", "state": "Jammu & Kashmir", "lat": 34.0837, "lon": 74.7973, "tier": 3},
    {"city": "Chandigarh", "district": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "tier": 2},
    {"city": "Indore", "district": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lon": 75.8577, "tier": 2},
    {"city": "Bhopal", "district": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126, "tier": 2},
    {"city": "Vijayawada", "district": "NTR", "state": "Andhra Pradesh", "lat": 16.5062, "lon": 80.648, "tier": 3},
    {"city": "Visakhapatnam", "district": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.6868, "lon": 83.2185, "tier": 2},
    {"city": "Dehradun", "district": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lon": 78.0322, "tier": 3},
    {"city": "Ranchi", "district": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lon": 85.3096, "tier": 3},
    {"city": "Raipur", "district": "Raipur", "state": "Chhattisgarh", "lat": 21.2514, "lon": 81.6296, "tier": 3},
    {"city": "Shimla", "district": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lon": 77.1734, "tier": 3},
    {"city": "Jodhpur", "district": "Jodhpur", "state": "Rajasthan", "lat": 26.2389, "lon": 73.0243, "tier": 3},
    {"city": "Amritsar", "district": "Amritsar", "state": "Punjab", "lat": 31.634, "lon": 74.8723, "tier": 3},
    {"city": "Ludhiana", "district": "Ludhiana", "state": "Punjab", "lat": 30.901, "lon": 75.8573, "tier": 3},
]

STATES = sorted({c["state"] for c in CITIES})


# ---------------------------------------------------------------- protocol
class WeatherConnector(Protocol):
    """All external integrations implement this surface."""

    id: str
    name: str
    category: str

    def connect(self) -> bool: ...
    def fetch(self, now: dt.datetime, rng: random.Random) -> list[dict[str, Any]]: ...
    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]: ...
    def health_check(self) -> dict[str, Any]: ...


class BaseDemoConnector:
    """Shared plumbing for demo connectors."""

    category = "DEMO"
    reliability = 0.8

    def connect(self) -> bool:
        return True  # demo connectors are always "connected"

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def health_check(self) -> dict[str, Any]:
        return {"status": "OPERATIONAL", "mode": "DEMO", "latency_ms": 40}

    @staticmethod
    def _pick(rng: random.Random, seq: list) -> Any:
        return rng.choice(seq)


def make_event_for_city(rng: random.Random, city: dict[str, Any], now: dt.datetime) -> dict[str, Any] | None:
    """Random realistic event for a city, honouring seasonal plausibility."""
    month = now.month
    west_coast = city["state"] in ("Maharashtra", "Kerala", "Karnataka", "Goa")
    north = city["state"] in ("Delhi", "Punjab", "Haryana", "Uttar Pradesh", "Bihar", "Uttarakhand", "Chandigarh", "Jammu & Kashmir")
    desert = city["state"] in ("Rajasthan", "Gujarat")

    roll = rng.random()
    etype: str | None = None
    metrics: dict[str, Any] = {}

    if west_coast and month in (6, 7, 8, 9) and roll < 0.5:
        etype = rng.choice(["RAINFALL", "FLOOD", "THUNDERSTORM"])
    elif north and month in (12, 1, 2) and roll < 0.45:
        etype = rng.choice(["FOG", "FOG", "RAINFALL"])
    elif desert and month in (4, 5, 6) and roll < 0.4:
        etype = rng.choice(["HEATWAVE", "DUST_STORM", "STRONG_WIND"])
    elif north and month in (4, 5, 6) and roll < 0.35:
        etype = rng.choice(["HEATWAVE", "DUST_STORM"])
    elif roll < 0.3:
        etype = rng.choice(EVENT_TYPES[:-1])

    if etype is None:
        return None

    severity = rng.choices(SEVERITIES, weights=[0.25, 0.4, 0.25, 0.1])[0]
    if etype == "RAINFALL":
        base = {"LOW": 8, "MEDIUM": 28, "HIGH": 70, "CRITICAL": 130}[severity]
        metrics["rainfall_mm"] = round(base * (0.7 + 0.6 * rng.random()), 1)
    elif etype == "FLOOD":
        base = {"LOW": 30, "MEDIUM": 60, "HIGH": 90, "CRITICAL": 140}[severity]
        metrics["rainfall_mm"] = round(base * (0.8 + 0.5 * rng.random()), 1)
        metrics["water_level_cm"] = round(severity_weight(severity) * 30 * (0.8 + 0.4 * rng.random()), 0)
    elif etype == "THUNDERSTORM":
        metrics["wind_kph"] = round({"LOW": 30, "MEDIUM": 45, "HIGH": 65, "CRITICAL": 85}[severity] * (0.85 + 0.3 * rng.random()), 0)
    elif etype == "HEATWAVE":
        metrics["temp_c"] = round({"LOW": 39, "MEDIUM": 41, "HIGH": 43.5, "CRITICAL": 46}[severity] * (0.99 + 0.02 * rng.random()), 1)
    elif etype == "FOG":
        metrics["visibility_km"] = round({"LOW": 0.8, "MEDIUM": 0.4, "HIGH": 0.15, "CRITICAL": 0.05}[severity] * (0.8 + 0.4 * rng.random()), 2)
    elif etype == "DUST_STORM":
        metrics["wind_kph"] = round({"LOW": 35, "MEDIUM": 50, "HIGH": 70, "CRITICAL": 90}[severity] * (0.85 + 0.3 * rng.random()), 0)
        metrics["visibility_km"] = round(max(0.05, {"LOW": 1.2, "MEDIUM": 0.7, "HIGH": 0.4, "CRITICAL": 0.2}[severity] * (0.8 + 0.4 * rng.random())), 2)
    elif etype == "STRONG_WIND":
        metrics["wind_kph"] = round({"LOW": 40, "MEDIUM": 55, "HIGH": 75, "CRITICAL": 95}[severity] * (0.85 + 0.3 * rng.random()), 0)

    return {"event_type": etype, "severity": severity, "metrics": metrics}


def severity_weight(severity: str) -> float:
    return {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0, "CRITICAL": 4.0}[severity]
