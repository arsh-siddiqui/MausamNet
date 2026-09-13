"""Demo connectors — simulated data sources for the prototype.

Each connector produces realistic, clearly-labeled DEMO signals. Real
implementations (IMD, OpenWeather, news APIs, social firehoses) implement
the same WeatherConnector protocol and register in CONNECTOR_FACTORY.
"""
from __future__ import annotations

import datetime as dt
import random
from typing import Any

from app.connectors.base import CITIES, BaseDemoConnector, make_event_for_city
from app.domain import EVENT_TYPES

TEMPLATES: dict[str, list[str]] = {
    "GOVERNMENT": [
        "IMD {color} alert: {etype_label} expected over {city}, {state}. {metric_phrase}",
        "Regional Met Centre issues {color} warning for {district} district — {etype_label}. {metric_phrase}",
        "IMD bulletin: {etype_label} conditions likely in {city} during next 6 hours. {metric_phrase}",
    ],
    "WEATHER_API": [
        "Model run indicates {etype_label} near {city}: {metric_phrase}. Confidence moderate.",
        "High-resolution nowcast for {city}: {metric_phrase}. Trend increasing.",
        "NWP update {city} {state}: {metric_phrase}.",
    ],
    "PUBLIC_DATASET": [
        "Station feed {city}: {metric_phrase}. Quality flag OK.",
        "Open dataset sensor reading {city}, {district}: {metric_phrase}.",
    ],
    "NEWS": [
        "{city}: {etype_label} disrupts normal life — reports of {impact}. {metric_phrase}",
        "Local media: {etype_label} hits {city}, {state}; authorities respond. {metric_phrase}",
        "Reports emerging from {district} district about {etype_label} impacts. {metric_phrase}",
    ],
    "SOCIAL": [
        "Multiple posts from {city} show {etype_label} conditions — videos circulating. {metric_phrase}",
        "Citizens report {impact} in {city} area. Unverified images attached.",
        "Trending: #{tag} — users share {etype_label} visuals from {city}. {metric_phrase}",
    ],
    "CITIZEN": [
        "Ground observation from {city}: {impact}. Reported via public form.",
        "Resident of {district} describes {etype_label} impacts near landmark. {metric_phrase}",
    ],
}

IMPACTS = [
    "waterlogged roads", "traffic disruption", "train delays", "flight diversions",
    "school closures", "power outages", "fallen trees", "roof damage", "low visibility on highways",
]
TAGS = ["MumbaiRains", "DelhiFog", "HeatwaveAlert", "MonsoonAlert", "DustStorm", "CycloneWatch"]


def _metric_phrase(metrics: dict[str, Any]) -> str:
    parts: list[str] = []
    if "rainfall_mm" in metrics:
        parts.append(f"{metrics['rainfall_mm']:.0f} mm rainfall")
    if "wind_kph" in metrics:
        parts.append(f"winds {metrics['wind_kph']:.0f} kph")
    if "temp_c" in metrics:
        parts.append(f"temp {metrics['temp_c']:.1f} °C")
    if "visibility_km" in metrics:
        parts.append(f"visibility {metrics['visibility_km']:.2f} km")
    return "; ".join(parts) if parts else "conditions developing"


class DemoGovernmentConnector(BaseDemoConnector):
    id = "imd-demo"
    name = "Government Weather (IMD Demo)"
    category = "GOVERNMENT"
    reliability = 0.98

    def fetch(self, now: dt.datetime, rng: random.Random) -> list[dict[str, Any]]:
        out = []
        for city in rng.sample(CITIES, k=min(3, len(CITIES))):
            ev = make_event_for_city(rng, city, now)
            if not ev:
                continue
            color = {"LOW": "yellow", "MEDIUM": "yellow", "HIGH": "orange", "CRITICAL": "red"}[ev["severity"]]
            label = ev["event_type"].replace("_", " ").title()
            out.append({
                "source_id": self.id,
                "source_category": self.category,
                "headline": TEMPLATES["GOVERNMENT"][rng.randrange(3)].format(
                    color=color, etype_label=label, city=city["city"], state=city["state"],
                    district=city["district"], metric_phrase=_metric_phrase(ev["metrics"]), impact="", tag=""),
                "content": f"Simulated government meteorological bulletin for {city['city']}. DEMO DATA.",
                "event_type": ev["event_type"],
                "severity": ev["severity"],
                "metrics": ev["metrics"],
                "city": city["city"], "district": city["district"], "state": city["state"],
                "latitude": city["lat"] + rng.uniform(-0.05, 0.05),
                "longitude": city["lon"] + rng.uniform(-0.05, 0.05),
                "occurred_at": now,
            })
        return out


class DemoWeatherApiConnector(BaseDemoConnector):
    id = "wxapi-demo"
    name = "Weather APIs (Demo)"
    category = "WEATHER_API"
    reliability = 0.93

    def fetch(self, now: dt.datetime, rng: random.Random) -> list[dict[str, Any]]:
        out = []
        for city in rng.sample(CITIES, k=min(4, len(CITIES))):
            ev = make_event_for_city(rng, city, now)
            if not ev:
                continue
            label = ev["event_type"].replace("_", " ").title()
            out.append({
                "source_id": self.id,
                "source_category": self.category,
                "headline": TEMPLATES["WEATHER_API"][rng.randrange(3)].format(
                    etype_label=label, city=city["city"], state=city["state"],
                    district=city["district"], metric_phrase=_metric_phrase(ev["metrics"]), impact="", tag="", color=""),
                "content": f"Simulated weather-API model output. DEMO DATA.",
                "event_type": ev["event_type"],
                "severity": ev["severity"],
                "metrics": ev["metrics"],
                "city": city["city"], "district": city["district"], "state": city["state"],
                "latitude": city["lat"] + rng.uniform(-0.04, 0.04),
                "longitude": city["lon"] + rng.uniform(-0.04, 0.04),
                "occurred_at": now,
            })
        return out


class DemoDatasetConnector(BaseDemoConnector):
    id = "dataset-demo"
    name = "Public Datasets (Demo)"
    category = "PUBLIC_DATASET"
    reliability = 0.90

    def fetch(self, now: dt.datetime, rng: random.Random) -> list[dict[str, Any]]:
        out = []
        for city in rng.sample(CITIES, k=min(2, len(CITIES))):
            ev = make_event_for_city(rng, city, now)
            if not ev:
                continue
            label = ev["event_type"].replace("_", " ").title()
            out.append({
                "source_id": self.id,
                "source_category": self.category,
                "headline": TEMPLATES["PUBLIC_DATASET"][rng.randrange(2)].format(
                    etype_label=label, city=city["city"], state=city["state"],
                    district=city["district"], metric_phrase=_metric_phrase(ev["metrics"]), impact="", tag="", color=""),
                "content": "Simulated public dataset observation. DEMO DATA.",
                "event_type": ev["event_type"],
                "severity": ev["severity"],
                "metrics": ev["metrics"],
                "city": city["city"], "district": city["district"], "state": city["state"],
                "latitude": city["lat"] + rng.uniform(-0.03, 0.03),
                "longitude": city["lon"] + rng.uniform(-0.03, 0.03),
                "occurred_at": now,
            })
        return out


class DemoNewsConnector(BaseDemoConnector):
    id = "news-demo"
    name = "News Intelligence (Demo)"
    category = "NEWS"
    reliability = 0.87

    def fetch(self, now: dt.datetime, rng: random.Random) -> list[dict[str, Any]]:
        out = []
        for city in rng.sample(CITIES, k=min(2, len(CITIES))):
            ev = make_event_for_city(rng, city, now)
            if not ev:
                continue
            label = ev["event_type"].replace("_", " ").title()
            out.append({
                "source_id": self.id,
                "source_category": self.category,
                "headline": TEMPLATES["NEWS"][rng.randrange(3)].format(
                    etype_label=label, city=city["city"], state=city["state"],
                    district=city["district"], metric_phrase=_metric_phrase(ev["metrics"]),
                    impact=rng.choice(IMPACTS), tag="", color=""),
                "content": "Simulated news monitoring signal. DEMO DATA.",
                "event_type": ev["event_type"],
                "severity": ev["severity"],
                "metrics": ev["metrics"],
                "city": city["city"], "district": city["district"], "state": city["state"],
                "latitude": city["lat"] + rng.uniform(-0.06, 0.06),
                "longitude": city["lon"] + rng.uniform(-0.06, 0.06),
                "occurred_at": now,
            })
        return out


class DemoSocialConnector(BaseDemoConnector):
    id = "social-demo"
    name = "Social Intelligence (Demo)"
    category = "SOCIAL"
    reliability = 0.74

    def fetch(self, now: dt.datetime, rng: random.Random) -> list[dict[str, Any]]:
        out = []
        for city in rng.sample(CITIES, k=min(3, len(CITIES))):
            ev = make_event_for_city(rng, city, now)
            if not ev:
                continue
            label = ev["event_type"].replace("_", " ").title()
            out.append({
                "source_id": self.id,
                "source_category": self.category,
                "headline": TEMPLATES["SOCIAL"][rng.randrange(3)].format(
                    etype_label=label, city=city["city"], state=city["state"],
                    district=city["district"], metric_phrase=_metric_phrase(ev["metrics"]),
                    impact=rng.choice(IMPACTS), tag=rng.choice(TAGS), color=""),
                "content": "Simulated social media cluster. DEMO DATA.",
                "event_type": ev["event_type"],
                "severity": ev["severity"],
                "metrics": ev["metrics"],
                "city": city["city"], "district": city["district"], "state": city["state"],
                "latitude": city["lat"] + rng.uniform(-0.09, 0.09),
                "longitude": city["lon"] + rng.uniform(-0.09, 0.09),
                "occurred_at": now,
                "media_url": ("https://demo.mausamnet.in/media/social_%03d.jpg" % rng.randrange(1, 60)) if rng.random() < 0.5 else None,
            })
        return out


from app.connectors.real_connectors import RealWeatherApiConnector, RealNewsConnector

CONNECTOR_FACTORY: dict[str, Any] = {
    "GOVERNMENT": DemoGovernmentConnector,
    "WEATHER_API": RealWeatherApiConnector,
    "PUBLIC_DATASET": DemoDatasetConnector,
    "NEWS": RealNewsConnector,
    "SOCIAL": DemoSocialConnector,
}
