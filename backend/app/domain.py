"""Domain vocabulary shared across backend and referenced by the frontend."""
from __future__ import annotations

SOURCE_CATEGORIES = ["GOVERNMENT", "WEATHER_API", "NEWS", "SOCIAL", "PUBLIC_DATASET", "CITIZEN"]
EVENT_TYPES = ["RAINFALL", "FLOOD", "THUNDERSTORM", "HEATWAVE", "FOG", "DUST_STORM", "STRONG_WIND", "OTHER"]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
EVENT_STATUSES = ["CANDIDATE", "ACTIVE", "VERIFIED", "REJECTED", "RESOLVED"]
SIGNAL_STATUSES = ["NEW", "CLASSIFIED", "DUPLICATE", "SUSPICIOUS", "VERIFIED", "REJECTED"]
USER_ROLES = ["ANALYST", "VERIFIER", "ADMIN"]
VERIFICATION_ACTIONS = ["VERIFY", "REJECT", "INVESTIGATE", "ESCALATE"]
ALERT_TYPES = [
    "HIGH_RISK_EVENT",
    "SUSPICIOUS_SIGNAL",
    "DUPLICATE_FOUND",
    "VERIFICATION_TASK",
    "EVENT_VERIFIED",
    "EVENT_REJECTED",
    "SOURCE_DEGRADED",
]

EVENT_TYPE_LABELS: dict[str, str] = {
    "RAINFALL": "Rainfall",
    "FLOOD": "Flood",
    "THUNDERSTORM": "Thunderstorm",
    "HEATWAVE": "Heatwave",
    "FOG": "Fog",
    "DUST_STORM": "Dust Storm",
    "STRONG_WIND": "Strong Wind",
    "OTHER": "Other",
}

SEVERITY_LABELS: dict[str, str] = {
    "LOW": "Low",
    "MEDIUM": "Medium",
    "HIGH": "High",
    "CRITICAL": "Critical",
}

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

SOURCE_LABELS: dict[str, str] = {
    "GOVERNMENT": "Government Weather",
    "WEATHER_API": "Weather APIs",
    "PUBLIC_DATASET": "Public Datasets",
    "NEWS": "News",
    "SOCIAL": "Social Signals",
    "CITIZEN": "Ground Evidence",
}

# Analyst-facing priority order of source categories (highest first)
SOURCE_PRIORITY = ["GOVERNMENT", "WEATHER_API", "PUBLIC_DATASET", "NEWS", "SOCIAL", "CITIZEN"]
