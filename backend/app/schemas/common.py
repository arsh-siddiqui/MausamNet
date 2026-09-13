"""Pydantic schemas shared across API + services.

Kept intentionally close to the future MongoDB document shape so the
repository swap stays painless.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ------------------------------------------------------------- vocabularies
SIGNAL_SOURCES = ["GOVERNMENT", "WEATHER_API", "NEWS", "SOCIAL", "PUBLIC_DATASET", "CITIZEN"]
EVENT_TYPES = ["RAINFALL", "FLOOD", "THUNDERSTORM", "HEATWAVE", "FOG", "DUST_STORM", "STRONG_WIND", "OTHER"]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
EVENT_STATUSES = ["CANDIDATE", "ACTIVE", "VERIFIED", "REJECTED", "RESOLVED"]
SIGNAL_STATUSES = ["NEW", "CLASSIFIED", "DUPLICATE", "SUSPICIOUS", "VERIFIED", "REJECTED"]
USER_ROLES = ["ANALYST", "VERIFIER", "ADMIN"]
ACTIONS = ["VERIFY", "REJECT", "INVESTIGATE", "ESCALATE"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------- auth
class UserOut(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    organization: str = ""
    role: str
    is_active: bool = True
    created_at: dt.datetime | None = None


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    organization: str = Field(default="", max_length=120)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    role: str = "ANALYST"


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshIn(BaseModel):
    refresh_token: str


class DemoAccountsOut(BaseModel):
    email: str
    password: str
    role: str
    label: str


# ------------------------------------------------------------- sources
class SourceOut(ORMModel):
    id: str
    name: str
    category: str
    mode: str
    status: str
    reliability: float
    signals_per_day: int
    latency_ms: int
    last_sync_at: dt.datetime | None = None
    config: dict[str, Any] = {}


# ------------------------------------------------------------- signals
class SignalFilters(BaseModel):
    q: str = ""
    source: str = ""
    event_type: str = ""
    severity: str = ""
    status: str = ""
    state: str = ""
    city: str = ""
    suspicious_only: bool = False
    duplicate_only: bool = False


class SignalOut(ORMModel):
    id: str
    source_id: str
    source_category: str
    headline: str
    content: str = ""
    media_url: str | None = None
    event_type: str
    severity: str
    status: str
    latitude: float
    longitude: float
    city: str
    district: str = ""
    state: str
    occurred_at: dt.datetime
    ingested_at: dt.datetime
    ai_confidence: float
    ai_label: str = ""
    trust_score: float
    duplicate_of: str | None = None
    duplicate_score: float = 0.0
    suspicious: bool = False
    suspicious_reasons: list[str] = []
    metrics: dict[str, Any] = {}
    event_id: str | None = None
    explanation: list[str] = []


class SignalCreateIn(BaseModel):
    source_category: str
    headline: str = Field(min_length=3, max_length=300)
    content: str = Field(default="", max_length=4000)
    event_type: str
    severity: str = "MEDIUM"
    latitude: float
    longitude: float
    city: str
    district: str = ""
    state: str
    occurred_at: dt.datetime | None = None
    metrics: dict[str, Any] = {}
    media_url: str | None = None


# ------------------------------------------------------------- events
class EventFilters(BaseModel):
    q: str = ""
    event_type: str = ""
    severity: str = ""
    status: str = ""
    state: str = ""
    min_confidence: float = 0.0


class EventOut(ORMModel):
    id: str
    title: str
    event_type: str
    severity: str
    status: str
    latitude: float
    longitude: float
    city: str
    district: str = ""
    state: str
    radius_km: float = 25.0
    started_at: dt.datetime
    latest_at: dt.datetime
    signal_count: int
    confidence: float
    trust_score: float
    description: str = ""
    fusion: dict[str, Any] = {}
    evidence: dict[str, Any] = {}
    timeline: list[Any] = []
    metrics: dict[str, Any] = {}
    related_event_ids: list[str] = []


class EventDetail(EventOut):
    signals: list[SignalOut] = []
    graph: dict[str, Any] | None = None
    anomalies: list[AnomalyOut] = []
    verification_history: list[dict[str, Any]] = []
    related_events: list[EventOut] = []


class AnomalyOut(ORMModel):
    id: str
    metric: str
    city: str
    district: str = ""
    state: str
    latitude: float
    longitude: float
    observed_at: dt.datetime
    expected_low: float
    expected_high: float
    observed_value: float
    deviation_pct: float
    zscore: float = 0.0
    risk: str
    event_id: str | None = None
    explanation: list[str] = []


class SignalDetail(SignalOut):
    verification_history: list[dict[str, Any]] = []
    media_analysis: dict[str, Any] | None = None
    related_signals: list[dict[str, Any]] = []
    location_consistency: dict[str, Any] = {}
    time_consistency: dict[str, Any] = {}
    weather_evidence: dict[str, Any] = {}


# ------------------------------------------------------------- pagination
class SignalsPage(BaseModel):
    items: list[SignalOut]
    total: int
    page: int
    pages: int


class EventsPage(BaseModel):
    items: list[EventOut]
    total: int
    page: int
    pages: int


class AlertsPage(BaseModel):
    items: list[AlertOut]
    total: int
    page: int
    pages: int


# ------------------------------------------------------------- verification
class VerificationItem(BaseModel):
    event: EventOut
    source_breakdown: dict[str, int] = {}
    trust_score: float = 0.0
    ai_recommendation: str = "VERIFY"
    evidence_summary: list[str] = []


class VerificationActionIn(BaseModel):
    action: str = ""  # action is taken from the path; body field optional
    rationale: str = Field(default="", max_length=2000)


class VerificationActionOut(BaseModel):
    ok: bool
    event: EventOut
    audit_id: str


# ------------------------------------------------------------- ground reports
class GroundReportIn(BaseModel):
    event_type: str
    description: str = Field(min_length=10, max_length=4000)
    city: str
    district: str = ""
    state: str
    latitude: float | None = None
    longitude: float | None = None
    reporter_name: str = Field(default="Anonymous Citizen", max_length=120)
    media_url: str | None = None


class GroundReportOut(ORMModel):
    id: str
    tracking_id: str
    reporter_name: str
    event_type: str
    description: str
    city: str
    district: str = ""
    state: str
    latitude: float = 0.0
    longitude: float = 0.0
    media_url: str | None = None
    status: str
    signal_id: str | None = None
    created_at: dt.datetime | None = None


# ------------------------------------------------------------- AI
class ClassifyIn(BaseModel):
    headline: str = Field(min_length=3, max_length=300)
    content: str = Field(default="", max_length=4000)
    metrics: dict[str, Any] = {}


class ClassifyOut(BaseModel):
    event_type: str
    severity: str
    confidence: float
    explanation: list[str]


class TrustScoreIn(BaseModel):
    source_category: str
    headline: str
    content: str = ""
    latitude: float
    longitude: float
    city: str
    state: str
    occurred_at: dt.datetime | None = None
    metrics: dict[str, Any] = {}
    media_url: str | None = None
    duplicate_score: float = 0.0
    cross_source_agreement: float = 0.0


class TrustScoreOut(BaseModel):
    trust_score: int
    confidence_band: str
    verdict: str
    breakdown: dict[str, float]
    explanation: list[str]


class DuplicateCheckIn(BaseModel):
    headline: str
    content: str = ""
    latitude: float
    longitude: float
    occurred_at: dt.datetime
    source_category: str = ""
    media_phash: str = ""


class DuplicateCheckOut(BaseModel):
    is_duplicate: bool
    score: float
    match_signal_id: str | None
    reason: str


class MediaAnalyzeOut(ORMModel):
    id: str
    signal_id: str | None = None
    filename: str
    phash: str
    width: int
    height: int
    filesize: int
    format: str
    captured_at: dt.datetime | None = None
    exif_ok: bool
    similarity: float
    match_signal_id: str | None = None
    previous_seen_at: dt.datetime | None = None
    previous_location: str = ""
    finding: str
    checks: dict[str, Any] = {}
    explanation: list[str] = []
    created_at: dt.datetime | None = None


# ------------------------------------------------------------- simulation
class SimulationControlIn(BaseModel):
    speed: float = Field(default=1.0, ge=0.5, le=5.0)
    scenario: str = "general"


class SimulationStatusOut(BaseModel):
    running: bool
    speed: float
    scenario: str
    stage: int
    ticks: int
    signals_generated: int
    scenario_stages: list[str] = []


# ------------------------------------------------------------- analytics / dashboard
class DashboardOverview(BaseModel):
    signals_processed: int
    active_events: int
    critical_events: int
    suspicious_signals: int
    verified_events: int
    pending_reviews: int
    generated_at: dt.datetime


class EventTrendPoint(BaseModel):
    bucket: str
    events: int
    signals: int


class SourceReliabilityRow(BaseModel):
    category: str
    signals: int
    verified_pct: float
    suspicious_pct: float
    avg_trust: float
    reliability: float


class StateRow(BaseModel):
    state: str
    signals: int
    events: int
    verified_pct: float
    suspicious_pct: float
    critical: int
    avg_confidence: float


class AnomalyCorrelationRow(BaseModel):
    anomaly_id: str
    city: str
    metric: str
    linked_event_id: str | None
    linked_event_title: str | None


class AnalyticsOverview(BaseModel):
    event_trend: list[EventTrendPoint]
    state_ranking: list[StateRow]
    event_categories: list[dict[str, Any]]
    verification_rate: list[EventTrendPoint]
    suspicious_trend: list[EventTrendPoint]
    source_reliability: list[SourceReliabilityRow]
    hourly_distribution: list[dict[str, Any]]
    severity_distribution: list[dict[str, Any]]
    states: list[StateRow]
    filters_applied: dict[str, Any] = {}


class SearchResults(BaseModel):
    events: list[EventOut]
    signals: list[SignalOut]
    sources: list[SourceOut]
    locations: list[dict[str, Any]]


# ------------------------------------------------------------- map
class MapPointOut(BaseModel):
    id: str
    kind: str  # event | signal | anomaly
    latitude: float
    longitude: float
    title: str
    event_type: str
    severity: str
    status: str | None = None
    source_category: str | None = None
    confidence: float | None = None
    trust_score: float | None = None
    signal_count: int | None = None
    suspicious: bool = False
    deviation_pct: float | None = None
    metric: str | None = None
    occurred_at: dt.datetime | None = None
    state: str | None = None
    district: str | None = None
    city: str | None = None


# ------------------------------------------------------------- notifications
class AlertOut(ORMModel):
    id: str
    type: str
    severity: str
    title: str
    message: str = ""
    event_id: str | None = None
    signal_id: str | None = None
    read_at: dt.datetime | None = None
    created_at: dt.datetime


# ------------------------------------------------------------- system
class SystemComponent(BaseModel):
    name: str
    status: str
    latency_ms: int
    last_heartbeat: dt.datetime
    detail: str = ""


class SystemHealthOut(BaseModel):
    overall: str
    components: list[SystemComponent]
    version: str
    environment: str


class SettingsOut(BaseModel):
    trust_weights: dict[str, float]
    risk_thresholds: dict[str, float]
    simulation_speed: float
    source_modes: dict[str, str]
