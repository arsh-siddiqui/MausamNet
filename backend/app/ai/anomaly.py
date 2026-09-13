"""StatisticalAnomalyDetector — z-score based weather anomaly detection.

For each city and metric, builds expectation from the observation history
(mean ± 2σ as the "expected band") and flags observations beyond it.
Deterministic and explainable.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

METRIC_LABELS = {
    "RAINFALL": ("rainfall_mm", "Rainfall", "mm"),
    "TEMP": ("temp_c", "Temperature", "°C"),
    "WIND": ("wind_kph", "Wind", "kph"),
    "VISIBILITY": ("visibility_km", "Visibility", "km"),
    "HUMIDITY": ("humidity", "Humidity", "%"),
}

RISK_BANDS = [(3.5, "CRITICAL"), (2.5, "HIGH"), (1.5, "MEDIUM")]


def risk_for_zscore(z: float) -> str:
    for threshold, risk in RISK_BANDS:
        if abs(z) >= threshold:
            return risk
    return "LOW"


class AnomalyDetector:
    def detect(self, city_stats: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raise NotImplementedError


class StatisticalAnomalyDetector(AnomalyDetector):
    """Consumes ObservationRepository.stats_by_city() rows."""

    def detect(self, city_stats: list[dict[str, Any]]) -> list[dict[str, Any]]:
        anomalies: list[dict[str, Any]] = []
        for row in city_stats:
            if row.get("n", 0) < 6:
                continue  # not enough history
            rainfall = row.get("rain_max", 0.0)
            mean, std = row.get("rain_mean", 0.0), row.get("rain_std", 0.0)
            if std <= 0.5:
                std = 0.5  # avoid div-by-zero; flat series
            z = (rainfall - mean) / std
            if abs(z) >= 1.5 and rainfall > mean + 0.5:
                expected_low = max(0.0, mean - 2 * std)
                expected_high = mean + 2 * std
                deviation = ((rainfall - expected_high) / max(expected_high, 1.0)) * 100 if rainfall > expected_high else 0
                anomalies.append({
                    "metric": "RAINFALL",
                    "city": row["city"],
                    "district": row.get("district", ""),
                    "state": row.get("state", ""),
                    "latitude": row.get("latitude", 0.0),
                    "longitude": row.get("longitude", 0.0),
                    "observed_at": row.get("last_observed_at") or utcnow(),
                    "expected_low": round(expected_low, 2),
                    "expected_high": round(expected_high, 2),
                    "observed_value": round(rainfall, 2),
                    "deviation_pct": round(deviation, 1),
                    "zscore": round(z, 2),
                    "risk": risk_for_zscore(z),
                    "explanation": [
                        f"City baseline: mean {mean:.1f} mm, σ {std:.1f} mm over {row.get('n')} observations.",
                        f"Observed peak {rainfall:.1f} mm is {z:.1f}σ above the mean.",
                        f"Expected band (mean ± 2σ): {expected_low:.0f}–{expected_high:.0f} mm.",
                        f"Deviation above expected band: +{deviation:.0f}%.",
                    ],
                })
        anomalies.sort(key=lambda a: a["zscore"], reverse=True)
        return anomalies


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
