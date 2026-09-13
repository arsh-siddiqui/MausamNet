"""DemoEventClassifier — deterministic, explainable text+metric classification.

Swap-in plan (docs): IndicBERT / fine-tuned transformer returning the same
ClassifyOut shape; no service or API change required.
"""
from __future__ import annotations

import re
from typing import Any

from app.domain import EVENT_TYPES, SEVERITIES

# --- lexicons -----------------------------------------------------------
LEXICONS: dict[str, list[str]] = {
    "RAINFALL": ["rain", "rainfall", "downpour", "drizzle", "showers", "precipitation", "mm rain", "rainfall_mm"],
    "FLOOD": ["flood", "waterlogging", "water-logging", "inundation", "inundated", "overflow", "submerged", "breach"],
    "THUNDERSTORM": ["thunder", "lightning", "thunderstorm", "squall", "storm cell", "hail"],
    "HEATWAVE": ["heat", "heatwave", "heat wave", "heatwave", "hot", "temperature", "temp_c", "heat_index"],
    "FOG": ["fog", "mist", "haze", "visibility", "visibility_km", "smog"],
    "DUST_STORM": ["dust", "sandstorm", "dust storm", "haze", "dust storm", "aqi"],
    "STRONG_WIND": ["wind", "gusty", "gale", "wind_kph", "gust", "cyclone", "squall"],
}

SEVERITY_LEXICONS: dict[str, list[str]] = {
    "CRITICAL": ["death", "killed", "casualt", "evacuat", "collapsed", "severe", "extreme", "disaster", "rescue", "imdalarm", "red alert"],
    "HIGH": ["damage", "disrupted", "cancelled", "diverted", "waterlogged", "traffic", "school closed", "orange alert", "high"],
    "MEDIUM": ["moderate", "advisory", "warning", "yellow alert", "likely", "expected"],
    "LOW": ["light", "trace", "minor", "drizzle", "possibility"],
}


class EventClassifier:
    """Interface for event classification."""

    def classify(self, headline: str, content: str = "", metrics: dict[str, Any] | None = None) -> dict:
        raise NotImplementedError


class DemoEventClassifier(EventClassifier):
    """Lexicon + rule based classifier with numeric-metric overrides."""

    def classify(self, headline: str, content: str = "", metrics: dict[str, Any] | None = None) -> dict:
        metrics = metrics or {}
        text = f"{headline} {content}".lower()

        # --- type scoring ------------------------------------------------
        scores: dict[str, float] = {}
        for etype, words in LEXICONS.items():
            s = 0.0
            for w in words:
                if w in text:
                    # metric-key hits (e.g. "rainfall_mm") count more
                    s += 1.5 if ("_" in w) else 1.0
            scores[etype] = s

        # numeric metric evidence strongly implies type
        if "rainfall_mm" in metrics and metrics["rainfall_mm"] is not None and metrics["rainfall_mm"] > 15:
            scores["RAINFALL"] = scores.get("RAINFALL", 0) + 3
            scores["FLOOD"] = scores.get("FLOOD", 0) + (1.5 if metrics["rainfall_mm"] > 65 else 0)
        if "wind_kph" in metrics and metrics["wind_kph"] and metrics["wind_kph"] > 40:
            scores["STRONG_WIND"] = scores.get("STRONG_WIND", 0) + 3
        if "temp_c" in metrics and metrics["temp_c"] and metrics["temp_c"] >= 40:
            scores["HEATWAVE"] = scores.get("HEATWAVE", 0) + 3
        if "visibility_km" in metrics and metrics["visibility_km"] and metrics["visibility_km"] < 1.0:
            scores["FOG"] = scores.get("FOG", 0) + 3

        best = max(scores, key=lambda k: scores[k])
        total = sum(scores.values())
        if total == 0 or scores[best] == 0:
            etype = "OTHER"
            confidence = 0.35
            explanation = ["No strong keyword or metric evidence; classified as OTHER."]
        else:
            etype = best
            # margin over runner-up drives confidence
            ranked = sorted(scores.values(), reverse=True)
            margin = (ranked[0] - (ranked[1] if len(ranked) > 1 else 0)) / (ranked[0] + 1e-6)
            confidence = min(0.97, 0.45 + 0.4 * margin + min(0.15, ranked[0] / 40))
            explanation = [
                f"Keyword evidence for {etype}: {int(scores[best])} matched terms.",
                f"Margin over next type: {margin:.0%}.",
            ]

        if etype not in EVENT_TYPES:
            etype = "OTHER"

        # --- severity ------------------------------------------------------
        sev_score = {s: 0.0 for s in SEVERITIES}
        for band, words in SEVERITY_LEXICONS.items():
            for w in words:
                if w in text:
                    sev_score[band] += 1.0

        rainfall = metrics.get("rainfall_mm")
        if isinstance(rainfall, (int, float)):
            if rainfall >= 120:
                sev_score["CRITICAL"] += 3
            elif rainfall >= 65:
                sev_score["HIGH"] += 3
            elif rainfall >= 35:
                sev_score["MEDIUM"] += 2
            else:
                sev_score["LOW"] += 1
        wind = metrics.get("wind_kph")
        if isinstance(wind, (int, float)) and wind:
            if wind >= 90:
                sev_score["CRITICAL"] += 3
            elif wind >= 60:
                sev_score["HIGH"] += 2
            elif wind >= 40:
                sev_score["MEDIUM"] += 1
        temp = metrics.get("temp_c")
        if isinstance(temp, (int, float)) and temp:
            if temp >= 45:
                sev_score["CRITICAL"] += 3
            elif temp >= 42:
                sev_score["HIGH"] += 2
            elif temp >= 40:
                sev_score["MEDIUM"] += 1
        vis = metrics.get("visibility_km")
        if isinstance(vis, (int, float)) and vis is not None:
            if vis <= 0.05:
                sev_score["CRITICAL"] += 2
            elif vis <= 0.2:
                sev_score["HIGH"] += 2
            elif vis <= 0.5:
                sev_score["MEDIUM"] += 1

        severity = max(sev_score, key=lambda k: sev_score[k])
        if sev_score[severity] == 0:
            severity = "MEDIUM"
        explanation.append(f"Severity '{severity}' from text + metric thresholds.")

        return {
            "event_type": etype,
            "severity": severity,
            "confidence": round(min(0.98, confidence), 3),
            "explanation": explanation,
        }
