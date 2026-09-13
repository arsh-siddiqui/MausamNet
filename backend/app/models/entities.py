"""ORM models (SQLite prototype).

The repository layer maps these rows to domain dataclasses, so the rest of
the application never touches ORM objects directly.
"""
from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------- enums
class UserRole(str, enum.Enum):
    ANALYST = "ANALYST"
    VERIFIER = "VERIFIER"
    ADMIN = "ADMIN"


class SignalSource(str, enum.Enum):
    GOVERNMENT = "GOVERNMENT"
    WEATHER_API = "WEATHER_API"
    NEWS = "NEWS"
    SOCIAL = "SOCIAL"
    PUBLIC_DATASET = "PUBLIC_DATASET"
    CITIZEN = "CITIZEN"


class EventType(str, enum.Enum):
    RAINFALL = "RAINFALL"
    FLOOD = "FLOOD"
    THUNDERSTORM = "THUNDERSTORM"
    HEATWAVE = "HEATWAVE"
    FOG = "FOG"
    DUST_STORM = "DUST_STORM"
    STRONG_WIND = "STRONG_WIND"
    OTHER = "OTHER"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SignalStatus(str, enum.Enum):
    NEW = "NEW"
    CLASSIFIED = "CLASSIFIED"
    DUPLICATE = "DUPLICATE"
    SUSPICIOUS = "SUSPICIOUS"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class EventStatus(str, enum.Enum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"


# ---------------------------------------------------------------- tables
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    organization: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.ANALYST.value, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)


class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(30), index=True)  # SignalSource value
    mode: Mapped[str] = mapped_column(String(20), default="DEMO")  # DEMO | LIVE
    status: Mapped[str] = mapped_column(String(20), default="OPERATIONAL")
    reliability: Mapped[float] = mapped_column(Float, default=0.8)
    signals_per_day: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    last_sync_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)


class WeatherSignalModel(Base):
    __tablename__ = "weather_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(60), ForeignKey("sources.id"), index=True)
    source_category: Mapped[str] = mapped_column(String(30), index=True)
    headline: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text, default="")
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    event_type: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(10), index=True)
    status: Mapped[str] = mapped_column(String(20), default="NEW", index=True)
    latitude: Mapped[float] = mapped_column(Float, index=True)
    longitude: Mapped[float] = mapped_column(Float, index=True)
    city: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str] = mapped_column(String(80), index=True)
    state: Mapped[str] = mapped_column(String(80), index=True)
    occurred_at: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
    ingested_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, index=True)
    ai_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    ai_label: Mapped[str] = mapped_column(String(40), default="")
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    duplicate_of: Mapped[str | None] = mapped_column(String(36), nullable=True)
    duplicate_score: Mapped[float] = mapped_column(Float, default=0.0)
    suspicious: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    suspicious_reasons: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)  # rainfall_mm, wind_kph, temp_c...
    event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("weather_events.id"), nullable=True, index=True)
    explanation: Mapped[list] = mapped_column(JSON, default=list)

    event = relationship("WeatherEventModel", back_populates="signals", foreign_keys=[event_id])


class WeatherEventModel(Base):
    __tablename__ = "weather_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    event_type: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(10), index=True)
    status: Mapped[str] = mapped_column(String(20), default="CANDIDATE", index=True)
    latitude: Mapped[float] = mapped_column(Float, index=True)
    longitude: Mapped[float] = mapped_column(Float)
    city: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80), index=True)
    radius_km: Mapped[float] = mapped_column(Float, default=25.0)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
    latest_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[str] = mapped_column(Text, default="")
    fusion: Mapped[dict] = mapped_column(JSON, default=dict)       # EvidenceFusion dict
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)     # per-category matrix
    timeline: Mapped[list] = mapped_column(JSON, default=list)     # [{at, label, detail}]
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)      # growth_rate, peak values
    related_event_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    signals = relationship("WeatherSignalModel", back_populates="event", foreign_keys="WeatherSignalModel.event_id")


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("weather_events.id"), index=True)
    category: Mapped[str] = mapped_column(String(30), index=True)  # GOVERNMENT / NEWS / ...
    strength: Mapped[str] = mapped_column(String(20))              # STRONG / SUPPORTING / WEAK / CONTRADICTING
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    signal_ids: Mapped[list] = mapped_column(JSON, default=list)
    note: Mapped[str] = mapped_column(Text, default="")


class EventGraphEdgeModel(Base):
    __tablename__ = "event_graph_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("weather_events.id"), index=True)
    source_node: Mapped[str] = mapped_column(String(40))
    target_node: Mapped[str] = mapped_column(String(40))
    relation: Mapped[str] = mapped_column(String(30))  # SUPPORTS / CONTRADICTS / DUPLICATE_OF / LOCATED_NEAR / SAME_EVENT
    weight: Mapped[float] = mapped_column(Float, default=0.0)


class WeatherObservationModel(Base):
    __tablename__ = "weather_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    city: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
    rainfall_mm: Mapped[float] = mapped_column(Float, default=0.0)
    temp_c: Mapped[float] = mapped_column(Float, default=0.0)
    wind_kph: Mapped[float] = mapped_column(Float, default=0.0)
    humidity: Mapped[float] = mapped_column(Float, default=0.0)
    visibility_km: Mapped[float] = mapped_column(Float, default=10.0)

    __table_args__ = (Index("ix_obs_city_time", "city", "observed_at"),)


class VerificationActionModel(Base):
    __tablename__ = "verification_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("weather_events.id"), nullable=True, index=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("weather_signals.id"), nullable=True, index=True)
    verifier_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(20))  # VERIFY / REJECT / INVESTIGATE / ESCALATE
    rationale: Mapped[str] = mapped_column(Text, default="")
    ai_recommendation: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, index=True)


class AlertModel(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(40), index=True)  # HIGH_RISK_EVENT / SUSPICIOUS_SIGNAL / ...
    severity: Mapped[str] = mapped_column(String(10), default="MEDIUM")
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text, default="")
    event_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, index=True)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(40), default="")
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    ip: Mapped[str] = mapped_column(String(60), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, index=True)


class AnomalyModel(Base):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    metric: Mapped[str] = mapped_column(String(40), index=True)  # RAINFALL / TEMP / WIND / VISIBILITY
    city: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime, index=True)
    expected_low: Mapped[float] = mapped_column(Float)
    expected_high: Mapped[float] = mapped_column(Float)
    observed_value: Mapped[float] = mapped_column(Float)
    deviation_pct: Mapped[float] = mapped_column(Float)
    zscore: Mapped[float] = mapped_column(Float, default=0.0)
    risk: Mapped[str] = mapped_column(String(10), default="MEDIUM", index=True)
    event_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    explanation: Mapped[list] = mapped_column(JSON, default=list)


class MediaAnalysisModel(Base):
    __tablename__ = "media_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    phash: Mapped[str] = mapped_column(String(80), default="", index=True)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    filesize: Mapped[int] = mapped_column(Integer, default=0)
    format: Mapped[str] = mapped_column(String(20), default="")
    captured_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    exif_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    match_signal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    previous_seen_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    previous_location: Mapped[str] = mapped_column(String(120), default="")
    finding: Mapped[str] = mapped_column(String(40), default="")  # AUTHENTIC_LIKELY / POTENTIAL_RECYCLED / NO_MATCH / NEEDS_REVIEW
    checks: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)


class KeyValueModel(Base):
    """Generic app-level settings (trust weights, thresholds, ...)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class SimulationStateModel(Base):
    __tablename__ = "simulation_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    running: Mapped[bool] = mapped_column(Boolean, default=False)
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    scenario: Mapped[str] = mapped_column(String(60), default="general")
    stage: Mapped[int] = mapped_column(Integer, default=0)
    ticks: Mapped[int] = mapped_column(Integer, default=0)
    signals_generated: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)


class GroundReportModel(Base):
    __tablename__ = "ground_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tracking_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    reporter_name: Mapped[str] = mapped_column(String(120), default="Anonymous Citizen")
    event_type: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text, default="")
    city: Mapped[str] = mapped_column(String(80))
    district: Mapped[str] = mapped_column(String(80), default="")
    state: Mapped[str] = mapped_column(String(80))
    latitude: Mapped[float] = mapped_column(Float, default=0.0)
    longitude: Mapped[float] = mapped_column(Float, default=0.0)
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="RECEIVED", index=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, index=True)
