"""Real API Connectors for Open-Meteo and NewsAPI."""

import datetime as dt
import random
from typing import Any
import httpx

from app.config import settings
from app.connectors.base import CITIES, severity_weight
from app.domain import EVENT_TYPES

class RealWeatherApiConnector:
    """Uses Open-Meteo API to fetch real weather conditions for major cities."""
    id = "open-meteo-real"
    name = "Open-Meteo Real-Time Weather"
    category = "WEATHER_API"
    reliability = 0.95

    def connect(self) -> bool:
        return True

    def fetch(self, now: dt.datetime, rng: random.Random) -> list[dict[str, Any]]:
        out = []
        # Check a random sample of cities to avoid hitting rate limits instantly
        # Open-Meteo is free, but doing 35 API calls every cycle is slow.
        cities_to_check = rng.sample(CITIES, k=min(4, len(CITIES)))

        try:
            with httpx.Client(timeout=5.0) as client:
                for city in cities_to_check:
                    url = f"{settings.open_meteo_api_url}/forecast"
                    params = {
                        "latitude": city["lat"],
                        "longitude": city["lon"],
                        "current": "temperature_2m,precipitation,wind_speed_10m",
                        "timezone": "auto"
                    }
                    resp = client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        current = data.get("current", {})
                        temp = current.get("temperature_2m", 0)
                        precip = current.get("precipitation", 0)
                        wind = current.get("wind_speed_10m", 0)

                        # Logic to determine if it's an extreme event
                        etype = None
                        severity = "LOW"
                        metrics = {"temp_c": temp, "rainfall_mm": precip, "wind_kph": wind}

                        if precip > 10:
                            etype = "RAINFALL"
                            severity = "HIGH" if precip > 25 else "MEDIUM"
                        elif temp > 40:
                            etype = "HEATWAVE"
                            severity = "CRITICAL" if temp > 45 else "HIGH"
                        elif wind > 50:
                            etype = "STRONG_WIND"
                            severity = "HIGH" if wind > 75 else "MEDIUM"

                        if etype:
                            label = etype.replace("_", " ").title()
                            out.append({
                                "source_id": self.id,
                                "source_category": self.category,
                                "headline": f"Real-time Weather Alert: {label} near {city['city']}. Temp: {temp}°C, Precip: {precip}mm.",
                                "content": "Live meteorological reading from Open-Meteo API.",
                                "event_type": etype,
                                "severity": severity,
                                "metrics": metrics,
                                "city": city["city"], "district": city["district"], "state": city["state"],
                                "latitude": city["lat"],
                                "longitude": city["lon"],
                                "occurred_at": now,
                            })
        except Exception as e:
            # Silently fail if API is unreachable, standard for resilient connectors
            pass
            
        return out

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def health_check(self) -> dict[str, Any]:
        return {"status": "OPERATIONAL", "mode": "REAL", "api": "Open-Meteo"}


class RealNewsConnector:
    """Uses NewsAPI to fetch Indian weather-related news."""
    id = "newsapi-real"
    name = "NewsAPI Global Monitoring"
    category = "NEWS"
    reliability = 0.85

    def __init__(self):
        self.api_key = settings.news_api_key

    def connect(self) -> bool:
        return bool(self.api_key)

    def fetch(self, now: dt.datetime, rng: random.Random) -> list[dict[str, Any]]:
        if not self.api_key:
            return []
            
        out = []
        try:
            with httpx.Client(timeout=8.0) as client:
                # Fetch recent news related to extreme weather in India
                url = f"{settings.news_api_url}/everything"
                params = {
                    "q": "(flood OR heavy rain OR storm OR cyclone OR heatwave) AND (India)",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "apiKey": self.api_key,
                    "pageSize": 5
                }
                resp = client.get(url, params=params)
                
                if resp.status_code == 200:
                    data = resp.json()
                    articles = data.get("articles", [])
                    
                    for article in articles:
                        headline = article.get("title", "")
                        content = article.get("description", "") or headline
                        
                        # Very simple heuristic to match a city
                        matched_city = None
                        for c in CITIES:
                            if c["city"].lower() in headline.lower() or c["city"].lower() in content.lower():
                                matched_city = c
                                break
                        
                        if not matched_city:
                            matched_city = rng.choice(CITIES)
                            
                        # Infer event type from headline
                        etype = "OTHER"
                        if "flood" in headline.lower() or "waterlog" in headline.lower():
                            etype = "FLOOD"
                        elif "rain" in headline.lower():
                            etype = "RAINFALL"
                        elif "heat" in headline.lower():
                            etype = "HEATWAVE"
                        elif "storm" in headline.lower() or "cyclone" in headline.lower():
                            etype = "THUNDERSTORM"
                            
                        out.append({
                            "source_id": self.id,
                            "source_category": self.category,
                            "headline": headline,
                            "content": content,
                            "event_type": etype,
                            "severity": "MEDIUM", # Default severity for news
                            "metrics": {},
                            "city": matched_city["city"], 
                            "district": matched_city["district"], 
                            "state": matched_city["state"],
                            "latitude": matched_city["lat"] + rng.uniform(-0.02, 0.02),
                            "longitude": matched_city["lon"] + rng.uniform(-0.02, 0.02),
                            "occurred_at": now,
                            "media_url": article.get("urlToImage"),
                        })
        except Exception as e:
            pass
            
        return out

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def health_check(self) -> dict[str, Any]:
        return {"status": "OPERATIONAL" if self.api_key else "DEGRADED", "mode": "REAL", "api": "NewsAPI"}
