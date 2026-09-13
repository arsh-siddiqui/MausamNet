"""DemoTrustEngine — explainable trust scoring.

Combines source reliability, text/media evidence, location & time
consistency, weather evidence, cross-source agreement and duplicate
probability into a 0-100 trust score with a full breakdown.

Prototype weights live in app/settings_store.py and are admin-tunable.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

SOURCE_BASE_RELIABILITY: dict[str, float] = {
    "GOVERNMENT": 0.98,
    "WEATHER_API": 0.93,
    "PUBLIC_DATASET": 0.90,
    "NEWS": 0.87,
    "SOCIAL": 0.74,
    "CITIZEN": 0.62,
}

BANDS = [(80, "HIGH"), (60, "MODERATE"), (0, "LOW")]


def band_for(score: float) -> str:
    for threshold, band in BANDS:
        if score >= threshold:
            return band
    return "LOW"


class TrustEngine:
    """Interface."""

    def score(self, payload: dict[str, Any]) -> dict:
        raise NotImplementedError


class DemoTrustEngine(TrustEngine):
    def score(self, payload: dict[str, Any]) -> dict:
        weights = payload.get("weights") or {}
        w_source = weights.get("source_reliability", 0.20)
        w_text = weights.get("text_evidence", 0.15)
        w_media = weights.get("media_evidence", 0.10)
        w_location = weights.get("location_consistency", 0.15)
        w_time = weights.get("time_consistency", 0.10)
        w_weather = weights.get("weather_evidence", 0.15)
        w_cross = weights.get("cross_source_agreement", 0.10)
        w_dup = weights.get("duplicate_penalty", 0.05)

        src_cat: str = payload.get("source_category", "SOCIAL")
        base = SOURCE_BASE_RELIABILITY.get(src_cat, 0.6)

        # --- component scores in [0,1] -----------------------------------
        source_component = base

        text: str = f"{payload.get('headline','')} {payload.get('content','')}".lower()
        specificity = 0.0
        if any(w in text for w in ("mm", "kph", "°", "degree", "%")):
            specificity += 0.4
        if any(w in text for w in ("alert", "warning", "advisory", "issued")):
            specificity += 0.3
        if len(text) > 80:
            specificity += 0.3
        text_component = min(1.0, specificity)

        has_media = bool(payload.get("media_url"))
        media_component = 0.85 if has_media else 0.45

        weather = payload.get("weather_evidence") or {}
        weather_component = float(weather.get("score", 0.5))

        cross = payload.get("cross_source_agreement", 0.0)
        cross_component = max(0.0, min(1.0, float(cross)))

        # duplicate penalty: higher duplicate probability reduces trust
        dup_prob = float(payload.get("duplicate_score", 0.0))
        dup_component = 1.0 - min(1.0, dup_prob)

        total = (
            source_component * w_source
            + text_component * w_text
            + media_component * w_media
            + float(payload.get("location_component", 0.8)) * w_location
            + float(payload.get("time_component", 0.85)) * w_time
            + weather_component * w_weather
            + cross_component * w_cross
            + dup_component * w_dup
        )
        trust = int(round(max(0.0, min(1.0, total)) * 100))

        explanation: list[str] = []
        if source_component >= 0.9:
            explanation.append(f"✓ {src_cat.title()} source is highly reliable ({base:.0%} baseline).")
        elif source_component >= 0.7:
            explanation.append(f"• {src_cat.title()} source is generally reliable ({base:.0%} baseline).")
        else:
            explanation.append(f"⚠ {src_cat.title()} source reliability is limited ({base:.0%} baseline); corroborate before acting.")

        if text_component >= 0.7:
            explanation.append("✓ Report contains specific measurable values (quantities, alerts).")
        elif text_component >= 0.4:
            explanation.append("• Report has some specifics but limited detail.")
        else:
            explanation.append("⚠ Report lacks measurable specifics.")

        if has_media:
            explanation.append("✓ Image evidence attached — run media forensics for authenticity.")
        else:
            explanation.append("• No image evidence attached.")

        if weather_component >= 0.75:
            explanation.append("✓ Weather observations strongly corroborate the claim.")
        elif weather_component >= 0.5:
            explanation.append("• Weather observations partially corroborate the claim.")
        else:
            explanation.append("⚠ Weather observations do not clearly support the claim.")

        if cross_component >= 0.6:
            explanation.append(f"✓ Cross-source agreement strong ({cross_component:.0%}).")
        elif cross_component >= 0.3:
            explanation.append(f"• Cross-source agreement moderate ({cross_component:.0%}).")
        else:
            explanation.append(f"⚠ Little cross-source agreement ({cross_component:.0%}).")

        if dup_prob >= 0.8:
            explanation.append("⚠ Very similar content already seen — probable duplicate/recycled.")
        elif dup_prob >= 0.5:
            explanation.append("• Partially similar content exists elsewhere.")

        verdict = "LIKELY GENUINE" if trust >= 80 else ("NEEDS VERIFICATION" if trust >= 55 else "POTENTIALLY MISLEADING")

        return {
            "trust_score": trust,
            "confidence_band": band_for(trust),
            "verdict": verdict,
            "breakdown": {
                "source_reliability": round(source_component * 100),
                "text_evidence": round(text_component * 100),
                "media_evidence": round(media_component * 100),
                "location_consistency": round(float(payload.get("location_component", 0.8)) * 100),
                "time_consistency": round(float(payload.get("time_component", 0.85)) * 100),
                "weather_evidence": round(weather_component * 100),
                "cross_source_agreement": round(cross_component * 100),
                "duplicate_freedom": round(dup_component * 100),
            },
            "explanation": explanation,
        }
