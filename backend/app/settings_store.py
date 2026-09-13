"""Runtime-tunable settings (trust weights, thresholds, source modes).

Stored in the app_settings table via the repository boundary; admin UI can
modify trust weights / thresholds / simulation speed at runtime.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from app.repositories.registry import RepositoryRegistry


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)

TRUST_WEIGHT_DEFAULTS: dict[str, float] = {
    "source_reliability": 0.20,
    "text_evidence": 0.15,
    "media_evidence": 0.10,
    "location_consistency": 0.15,
    "time_consistency": 0.10,
    "weather_evidence": 0.15,
    "cross_source_agreement": 0.10,
    "duplicate_penalty": 0.05,
}

RISK_THRESHOLD_DEFAULTS: dict[str, float] = {
    "duplicate_threshold": 0.72,
    "partial_duplicate": 0.50,
    "suspicious_trust_below": 55.0,
    "high_confidence": 80.0,
    "moderate_confidence": 60.0,
}

RISK_THRESHOLD_KEYS = set(RISK_THRESHOLD_DEFAULTS.keys())


class SettingsStore:
    def __init__(self, registry: RepositoryRegistry) -> None:
        self._reg = registry

    # -- generic ----------------------------------------------------------
    def get(self, key: str, default: Any) -> Any:
        try:
            from sqlalchemy import select

            from app.models.entities import KeyValueModel

            row = self._reg.session.execute(select(KeyValueModel).where(KeyValueModel.key == key)).scalar_one_or_none()
            return row.value if row else default
        except Exception:
            return default

    def set(self, key: str, value: Any) -> None:
        from sqlalchemy import select

        from app.models.entities import KeyValueModel

        row = self._reg.session.execute(select(KeyValueModel).where(KeyValueModel.key == key)).scalar_one_or_none()
        if row:
            row.value = value
            row.updated_at = utcnow()
        else:
            self._reg.session.add(KeyValueModel(key=key, value=value))
        self._reg.session.flush()

    # -- typed helpers ------------------------------------------------------
    def trust_weights(self) -> dict[str, float]:
        stored = self.get("trust_weights", {}) or {}
        merged = dict(TRUST_WEIGHT_DEFAULTS)
        merged.update({k: float(v) for k, v in stored.items() if k in TRUST_WEIGHT_DEFAULTS})
        return merged

    def risk_thresholds(self) -> dict[str, float]:
        stored = self.get("risk_thresholds", {}) or {}
        merged = dict(RISK_THRESHOLD_DEFAULTS)
        merged.update({k: float(v) for k, v in stored.items() if k in RISK_THRESHOLD_KEYS})
        return merged

    def all_settings(self) -> dict[str, Any]:
        return {
            "trust_weights": self.trust_weights(),
            "risk_thresholds": self.risk_thresholds(),
            "simulation_speed": float(self.get("simulation_speed", 1.0)),
            "source_modes": self.get("source_modes", {}),
        }
