"""SQLite implementations of the repository interfaces.

Every class maps between ORM rows and the schema models (Pydantic) that the
rest of the application uses. Swapping to MongoDB = write Mongo*Repository
classes + register them in `registry.py`. Nothing else changes.
"""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Iterable

from sqlalchemy import String, and_, cast, func, or_, select, Integer, case
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.entities import (
    AlertModel,
    AnomalyModel,
    AuditLogModel,
    EventGraphEdgeModel,
    EvidenceModel,
    GroundReportModel,
    MediaAnalysisModel,
    SimulationStateModel,
    SourceModel,
    UserModel,
    VerificationActionModel,
    WeatherEventModel,
    WeatherObservationModel,
    WeatherSignalModel,
)
from app.schemas.common import (
    AlertOut,
    AnomalyOut,
    EventOut,
    GroundReportOut,
    MediaAnalyzeOut,
    SignalOut,
    SourceOut,
    UserOut,
)


def new_id() -> str:
    return str(uuid.uuid4())


def _norm(dt_or_none: dt.datetime | None) -> dt.datetime | None:
    if dt_or_none is None:
        return None
    if dt_or_none.tzinfo is not None:
        return dt_or_none.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return dt_or_none


# ------------------------------------------------------------------ users
class SQLiteUserRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, *, email: str, full_name: str, organization: str, hashed_password: str, role: str) -> UserOut:
        row = UserModel(
            id=new_id(),
            email=email.lower().strip(),
            full_name=full_name.strip(),
            organization=(organization or "").strip(),
            hashed_password=hashed_password,
            role=role,
        )
        self._s.add(row)
        self._s.flush()
        return UserOut.model_validate(row)

    def get_by_email(self, email: str) -> UserOut | None:
        row = self._s.execute(select(UserModel).where(UserModel.email == email.lower().strip())).scalar_one_or_none()
        return UserOut.model_validate(row) if row else None

    def get_by_id(self, user_id: str) -> UserOut | None:
        row = self._s.get(UserModel, user_id)
        return UserOut.model_validate(row) if row else None

    def count(self) -> int:
        return int(self._s.execute(select(func.count(UserModel.id))).scalar() or 0)


# ------------------------------------------------------------------ sources
class SQLiteSourceRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def list_all(self) -> list[SourceOut]:
        rows = self._s.execute(select(SourceModel).order_by(SourceModel.id)).scalars().all()
        return [SourceOut.model_validate(r) for r in rows]

    def get(self, source_id: str) -> SourceOut | None:
        row = self._s.get(SourceModel, source_id)
        return SourceOut.model_validate(row) if row else None

    def upsert_defaults(self, defaults: Iterable[dict[str, Any]]) -> None:
        for d in defaults:
            row = self._s.get(SourceModel, d["id"])
            if row is None:
                self._s.add(SourceModel(id=d["id"], **{k: v for k, v in d.items() if k != "id"}))
            else:
                for k, v in d.items():
                    if k != "id":
                        setattr(row, k, v)
        self._s.flush()

    def touch_sync(self, source_id: str, *, latency_ms: int, status: str = "OPERATIONAL") -> None:
        row = self._s.get(SourceModel, source_id)
        if row:
            row.last_sync_at = utcnow()
            row.latency_ms = latency_ms
            row.status = status
            self._s.flush()

    def set_mode(self, source_id: str, mode: str) -> None:
        row = self._s.get(SourceModel, source_id)
        if row:
            row.mode = mode
            self._s.flush()

    def search(self, q: str, limit: int = 8) -> list[SourceOut]:
        like = f"%{q}%"
        rows = (
            self._s.execute(
                select(SourceModel).where(or_(SourceModel.name.ilike(like), SourceModel.id.ilike(like))).limit(limit)
            )
            .scalars()
            .all()
        )
        return [SourceOut.model_validate(r) for r in rows]


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


# ------------------------------------------------------------------ signals
class SQLiteSignalRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    # -- helpers -------------------------------------------------------
    @staticmethod
    def _apply_filters(stmt, f: dict[str, Any]):
        if f.get("q"):
            like = f"%{f['q']}%"
            stmt = stmt.where(
                or_(
                    WeatherSignalModel.headline.ilike(like),
                    WeatherSignalModel.content.ilike(like),
                    WeatherSignalModel.city.ilike(like),
                    WeatherSignalModel.state.ilike(like),
                    WeatherSignalModel.id.ilike(like),
                    cast(WeatherSignalModel.metrics, String).ilike(like),
                )
            )
        if f.get("source"):
            stmt = stmt.where(WeatherSignalModel.source_category == f["source"])
        if f.get("event_type"):
            stmt = stmt.where(WeatherSignalModel.event_type == f["event_type"])
        if f.get("severity"):
            stmt = stmt.where(WeatherSignalModel.severity == f["severity"])
        if f.get("status"):
            stmt = stmt.where(WeatherSignalModel.status == f["status"])
        if f.get("state"):
            stmt = stmt.where(WeatherSignalModel.state == f["state"])
        if f.get("city"):
            stmt = stmt.where(WeatherSignalModel.city == f["city"])
        if f.get("suspicious_only"):
            stmt = stmt.where(WeatherSignalModel.suspicious.is_(True))
        if f.get("duplicate_only"):
            stmt = stmt.where(WeatherSignalModel.duplicate_of.isnot(None))
        if f.get("since"):
            stmt = stmt.where(WeatherSignalModel.occurred_at >= _norm(f["since"]))
        if f.get("until"):
            stmt = stmt.where(WeatherSignalModel.occurred_at <= _norm(f["until"]))
        return stmt

    _SORTABLE = {
        "occurred_at": WeatherSignalModel.occurred_at,
        "ingested_at": WeatherSignalModel.ingested_at,
        "trust_score": WeatherSignalModel.trust_score,
        "ai_confidence": WeatherSignalModel.ai_confidence,
        "severity": WeatherSignalModel.severity,
        "source_category": WeatherSignalModel.source_category,
        "city": WeatherSignalModel.city,
    }

    # -- API ------------------------------------------------------------
    def create(self, data: dict[str, Any]) -> SignalOut:
        data = dict(data)
        data.setdefault("id", new_id())
        data["occurred_at"] = _norm(data.get("occurred_at") or utcnow())
        data["ingested_at"] = _norm(data.get("ingested_at") or utcnow())
        row = WeatherSignalModel(**data)
        self._s.add(row)
        self._s.flush()
        return SignalOut.model_validate(row)

    def get(self, signal_id: str) -> SignalOut | None:
        row = self._s.get(WeatherSignalModel, signal_id)
        return SignalOut.model_validate(row) if row else None

    def list_page(self, *, filters: dict[str, Any], page: int, page_size: int, sort: str, direction: str) -> tuple[list[SignalOut], int]:
        base = self._apply_filters(select(WeatherSignalModel), filters)
        total = int(self._s.execute(select(func.count()).select_from(base.subquery())).scalar() or 0)
        col = self._SORTABLE.get(sort, WeatherSignalModel.occurred_at)
        order = col.desc() if direction == "desc" else col.asc()
        rows = (
            self._s.execute(base.order_by(order).offset((page - 1) * page_size).limit(page_size))
            .scalars()
            .all()
        )
        return [SignalOut.model_validate(r) for r in rows], total

    def update(self, signal_id: str, data: dict[str, Any]) -> None:
        row = self._s.get(WeatherSignalModel, signal_id)
        if row:
            for k, v in data.items():
                setattr(row, k, v)
            self._s.flush()

    def count(self, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count(WeatherSignalModel.id))
        if filters:
            stmt = self._apply_filters(select(WeatherSignalModel), filters).with_only_columns(func.count(WeatherSignalModel.id))
        return int(self._s.execute(stmt).scalar() or 0)

    def recent(self, limit: int = 12, filters: dict[str, Any] | None = None) -> list[SignalOut]:
        stmt = self._apply_filters(select(WeatherSignalModel), filters or {})
        rows = self._s.execute(stmt.order_by(WeatherSignalModel.ingested_at.desc()).limit(limit)).scalars().all()
        return [SignalOut.model_validate(r) for r in rows]

    def candidates_for_duplicate_check(self, *, since: dt.datetime, limit: int = 500) -> list[SignalOut]:
        rows = (
            self._s.execute(
                select(WeatherSignalModel)
                .where(WeatherSignalModel.occurred_at >= _norm(since))
                .order_by(WeatherSignalModel.occurred_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [SignalOut.model_validate(r) for r in rows]

    def set_event(self, signal_ids: list[str], event_id: str | None) -> None:
        if not signal_ids:
            return
        self._s.execute(
            WeatherSignalModel.__table__.update()
            .where(WeatherSignalModel.id.in_(signal_ids))
            .values(event_id=event_id)
        )
        self._s.flush()

    def ids_for_event(self, event_id: str, limit: int = 400) -> list[SignalOut]:
        rows = (
            self._s.execute(
                select(WeatherSignalModel)
                .where(WeatherSignalModel.event_id == event_id)
                .order_by(WeatherSignalModel.occurred_at.asc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [SignalOut.model_validate(r) for r in rows]

    def search(self, q: str, limit: int = 8) -> list[SignalOut]:
        like = f"%{q}%"
        rows = (
            self._s.execute(
                select(WeatherSignalModel)
                .where(or_(WeatherSignalModel.headline.ilike(like), WeatherSignalModel.city.ilike(like), WeatherSignalModel.id.ilike(like)))
                .order_by(WeatherSignalModel.ingested_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [SignalOut.model_validate(r) for r in rows]

    def count_by_day(self, *, days: int, filters: dict[str, Any] | None = None) -> dict[str, int]:
        """Signal counts grouped by ingestion day (ISO date -> count)."""
        base = self._apply_filters(select(WeatherSignalModel), filters or {})
        day_expr = func.date(WeatherSignalModel.ingested_at).label("day")
        stmt = base.with_only_columns(day_expr, func.count(WeatherSignalModel.id).label("n")).group_by(day_expr)
        rows = self._s.execute(stmt).all()
        return {str(r.day): int(r.n) for r in rows}

    def analytics_aggregates(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        """SQL GROUP BY aggregates used by the analytics service.

        Returns by_state / by_day_suspicious / by_source maps — computed in the
        database instead of dragging thousands of rows into Python.
        """
        base_filters = filters or {}

        def _grouped(dimension_cols, agg_cols):
            base = self._apply_filters(select(WeatherSignalModel), base_filters)
            stmt = base.with_only_columns(*dimension_cols, *agg_cols).group_by(*[c.key for c in dimension_cols])
            return self._s.execute(stmt).all()

        state_col = WeatherSignalModel.state.label("state")
        by_state = {
            r.state: {"signals": int(r.n), "suspicious": int(r.susp)}
            for r in _grouped(
                [state_col],
                [
                    func.count(WeatherSignalModel.id).label("n"),
                    func.sum(cast(WeatherSignalModel.suspicious, Integer)).label("susp"),
                ],
            )
        }

        day_expr = func.date(WeatherSignalModel.ingested_at).label("day")
        by_day_suspicious = {
            str(r.day): int(r.susp)
            for r in _grouped(
                [day_expr],
                [func.sum(cast(WeatherSignalModel.suspicious, Integer)).label("susp")],
            )
        }

        cat_col = WeatherSignalModel.source_category.label("cat")
        by_source = {
            r.cat: {"n": int(r.n), "verified": int(r.ver), "suspicious": int(r.susp), "trust_sum": float(r.trust or 0)}
            for r in _grouped(
                [cat_col],
                [
                    func.count(WeatherSignalModel.id).label("n"),
                    func.sum(case((WeatherSignalModel.status == "VERIFIED", 1), else_=0)).label("ver"),
                    func.sum(cast(WeatherSignalModel.suspicious, Integer)).label("susp"),
                    func.sum(func.coalesce(WeatherSignalModel.trust_score, 0)).label("trust"),
                ],
            )
        }
        return {"by_state": by_state, "by_day_suspicious": by_day_suspicious, "by_source": by_source}

    def assign_sequence(self, signal_id: str) -> int:
        """Human-friendly sequential reference (SIH-xxxxx)."""
        seq = int(self._s.execute(select(func.count(WeatherSignalModel.id))).scalar() or 0) + 1
        self._s.execute(
            WeatherSignalModel.__table__.update()
            .where(WeatherSignalModel.id == signal_id)
            .values(ai_label=WeatherSignalModel.ai_label)  # no-op keeps ORM honest
        )
        return seq

    def get_by_sequence(self, seq: int) -> SignalOut | None:
        return None


# ------------------------------------------------------------------ events
class SQLiteEventRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    @staticmethod
    def _apply_filters(stmt, f: dict[str, Any]):
        if f.get("q"):
            like = f"%{f['q']}%"
            stmt = stmt.where(or_(WeatherEventModel.title.ilike(like), WeatherEventModel.city.ilike(like), WeatherEventModel.state.ilike(like), WeatherEventModel.id.ilike(like)))
        if f.get("event_type"):
            stmt = stmt.where(WeatherEventModel.event_type == f["event_type"])
        if f.get("severity"):
            stmt = stmt.where(WeatherEventModel.severity == f["severity"])
        if f.get("status"):
            stmt = stmt.where(WeatherEventModel.status == f["status"])
        if f.get("state"):
            stmt = stmt.where(WeatherEventModel.state == f["state"])
        if f.get("min_confidence"):
            stmt = stmt.where(WeatherEventModel.confidence >= f["min_confidence"])
        return stmt

    _SORTABLE = {
        "started_at": WeatherEventModel.started_at,
        "latest_at": WeatherEventModel.latest_at,
        "confidence": WeatherEventModel.confidence,
        "signal_count": WeatherEventModel.signal_count,
        "severity": WeatherEventModel.severity,
        "title": WeatherEventModel.title,
    }

    def create(self, data: dict[str, Any]) -> EventOut:
        data = dict(data)
        data.setdefault("id", new_id())
        data["started_at"] = _norm(data.get("started_at") or utcnow())
        data["latest_at"] = _norm(data.get("latest_at") or data["started_at"])
        row = WeatherEventModel(**data)
        self._s.add(row)
        self._s.flush()
        return EventOut.model_validate(row)

    def get(self, event_id: str) -> EventOut | None:
        row = self._s.get(WeatherEventModel, event_id)
        return EventOut.model_validate(row) if row else None

    def update(self, event_id: str, data: dict[str, Any]) -> None:
        row = self._s.get(WeatherEventModel, event_id)
        if row:
            for k, v in data.items():
                setattr(row, k, v)
            row.updated_at = utcnow()
            self._s.flush()

    def list_page(self, *, filters: dict[str, Any], page: int, page_size: int, sort: str, direction: str) -> tuple[list[EventOut], int]:
        base = self._apply_filters(select(WeatherEventModel), filters)
        total = int(self._s.execute(select(func.count()).select_from(base.subquery())).scalar() or 0)
        col = self._SORTABLE.get(sort, WeatherEventModel.latest_at)
        order = col.desc() if direction == "desc" else col.asc()
        rows = self._s.execute(base.order_by(order).offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return [EventOut.model_validate(r) for r in rows], total

    def list_all(self, filters: dict[str, Any] | None = None, limit: int = 500) -> list[EventOut]:
        stmt = self._apply_filters(select(WeatherEventModel), filters or {})
        rows = self._s.execute(stmt.order_by(WeatherEventModel.latest_at.desc()).limit(limit)).scalars().all()
        return [EventOut.model_validate(r) for r in rows]

    def count(self, filters: dict[str, Any] | None = None) -> int:
        stmt = self._apply_filters(select(WeatherEventModel), filters or {}).with_only_columns(func.count(WeatherEventModel.id))
        return int(self._s.execute(stmt).scalar() or 0)

    def search(self, q: str, limit: int = 8) -> list[EventOut]:
        like = f"%{q}%"
        rows = (
            self._s.execute(
                select(WeatherEventModel)
                .where(or_(WeatherEventModel.title.ilike(like), WeatherEventModel.city.ilike(like), WeatherEventModel.state.ilike(like)))
                .order_by(WeatherEventModel.latest_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [EventOut.model_validate(r) for r in rows]

    def open_event_near(self, *, event_type: str, latitude: float, longitude: float, radius_km: float, since: dt.datetime) -> EventOut | None:
        """Find an OPEN (candidate/active) event of the same type within radius.

        Uses a bbox pre-filter then haversine refinement — enough for the
        prototype and portable to MongoDB's $geoWithin.
        """
        import math

        dlat = radius_km / 111.0
        dlon = radius_km / (111.0 * max(0.1, math.cos(math.radians(latitude))))
        rows = (
            self._s.execute(
                select(WeatherEventModel)
                .where(
                    WeatherEventModel.event_type == event_type,
                    WeatherEventModel.status.in_(["CANDIDATE", "ACTIVE"]),
                    WeatherEventModel.latest_at >= _norm(since),
                    WeatherEventModel.latitude.between(latitude - dlat, latitude + dlat),
                    WeatherEventModel.longitude.between(longitude - dlon, longitude + dlon),
                )
                .limit(50)
            )
            .scalars()
            .all()
        )

        def hav(a: WeatherEventModel) -> float:
            p1, p2 = math.radians(latitude), math.radians(a.latitude)
            dp = p2 - p1
            dl = math.radians(a.longitude - longitude)
            x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
            return 2 * 6371.0088 * math.asin(math.sqrt(x))

        for row in sorted(rows, key=hav):
            if hav(row) <= radius_km:
                return EventOut.model_validate(row)
        return None

    def set_related(self, event_id: str, related_ids: list[str]) -> None:
        row = self._s.get(WeatherEventModel, event_id)
        if row:
            row.related_event_ids = related_ids
            self._s.flush()


# ------------------------------------------------------------------ evidence + graph
class SQLiteEvidenceRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def replace_for_event(self, event_id: str, rows: list[dict[str, Any]]) -> None:
        self._s.execute(EvidenceModel.__table__.delete().where(EvidenceModel.event_id == event_id))
        for r in rows:
            self._s.add(EvidenceModel(id=new_id(), **r))
        self._s.flush()

    def list_for_event(self, event_id: str) -> list[dict[str, Any]]:
        rows = self._s.execute(select(EvidenceModel).where(EvidenceModel.event_id == event_id)).scalars().all()
        return [
            {"category": r.category, "strength": r.strength, "weight": r.weight, "signal_ids": r.signal_ids, "note": r.note}
            for r in rows
        ]


class SQLiteGraphRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def replace_for_event(self, event_id: str, edges: list[dict[str, Any]]) -> None:
        self._s.execute(EventGraphEdgeModel.__table__.delete().where(EventGraphEdgeModel.event_id == event_id))
        for e in edges:
            e = dict(e)
            e.setdefault("event_id", event_id)
            self._s.add(EventGraphEdgeModel(id=new_id(), **e))
        self._s.flush()

    def list_for_event(self, event_id: str) -> list[dict[str, Any]]:
        rows = self._s.execute(select(EventGraphEdgeModel).where(EventGraphEdgeModel.event_id == event_id)).scalars().all()
        return [
            {"source_node": r.source_node, "target_node": r.target_node, "relation": r.relation, "weight": r.weight}
            for r in rows
        ]


# ------------------------------------------------------------------ observations
class SQLiteObservationRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def bulk_create(self, rows: list[dict[str, Any]]) -> int:
        objs = [WeatherObservationModel(id=new_id(), **r) for r in rows]
        self._s.add_all(objs)
        self._s.flush()
        return len(objs)

    def series_for_city(self, city: str, metric: str, since: dt.datetime) -> list[dict[str, Any]]:
        colmap = {
            "rainfall_mm": WeatherObservationModel.rainfall_mm,
            "temp_c": WeatherObservationModel.temp_c,
            "wind_kph": WeatherObservationModel.wind_kph,
            "humidity": WeatherObservationModel.humidity,
            "visibility_km": WeatherObservationModel.visibility_km,
        }
        col = colmap.get(metric, WeatherObservationModel.rainfall_mm)
        rows = (
            self._s.execute(
                select(WeatherObservationModel)
                .where(WeatherObservationModel.city == city, WeatherObservationModel.observed_at >= _norm(since))
                .order_by(WeatherObservationModel.observed_at.asc())
            )
            .scalars()
            .all()
        )
        return [{"observed_at": r.observed_at, "value": getattr(r, col.key)} for r in rows]

    def stats_by_city(self, since: dt.datetime | None = None) -> list[dict[str, Any]]:
        stmt = select(WeatherObservationModel)
        if since:
            stmt = stmt.where(WeatherObservationModel.observed_at >= _norm(since))
        rows = self._s.execute(stmt).scalars().all()
        agg: dict[tuple[str, str, str], list[WeatherObservationModel]] = {}
        for r in rows:
            agg.setdefault((r.city, r.district, r.state), []).append(r)
        out = []
        for (city, district, state), items in agg.items():
            rainfall = [i.rainfall_mm for i in items]
            out.append(
                {
                    "city": city,
                    "district": district,
                    "state": state,
                    "latitude": items[0].latitude,
                    "longitude": items[0].longitude,
                    "n": len(items),
                    "rain_mean": sum(rainfall) / len(rainfall) if rainfall else 0.0,
                    "rain_std": _std(rainfall),
                    "rain_max": max(rainfall) if rainfall else 0.0,
                    "last_observed_at": max(i.observed_at for i in items),
                }
            )
        return out


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return (sum((v - mean) ** 2 for v in values) / (len(values) - 1)) ** 0.5


# ------------------------------------------------------------------ verification
class SQLiteVerificationRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        row = VerificationActionModel(id=new_id(), **data)
        self._s.add(row)
        self._s.flush()
        return {
            "id": row.id,
            "event_id": row.event_id,
            "signal_id": row.signal_id,
            "verifier_id": row.verifier_id,
            "action": row.action,
            "rationale": row.rationale,
            "ai_recommendation": row.ai_recommendation,
            "created_at": row.created_at,
        }

    def list_for_event(self, event_id: str) -> list[dict[str, Any]]:
        rows = (
            self._s.execute(
                select(VerificationActionModel)
                .where(VerificationActionModel.event_id == event_id)
                .order_by(VerificationActionModel.created_at.asc())
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": r.id,
                "action": r.action,
                "rationale": r.rationale,
                "verifier_id": r.verifier_id,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = (
            self._s.execute(select(VerificationActionModel).order_by(VerificationActionModel.created_at.desc()).limit(limit))
            .scalars()
            .all()
        )
        return [
            {
                "id": r.id,
                "action": r.action,
                "rationale": r.rationale,
                "verifier_id": r.verifier_id,
                "event_id": r.event_id,
                "signal_id": r.signal_id,
                "created_at": r.created_at,
            }
            for r in rows
        ]


# ------------------------------------------------------------------ alerts
class SQLiteAlertRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, data: dict[str, Any]) -> AlertOut:
        row = AlertModel(id=new_id(), **data)
        self._s.add(row)
        self._s.flush()
        return AlertOut.model_validate(row)

    def list_page(self, *, page: int, page_size: int, unread_only: bool = False) -> tuple[list[AlertOut], int]:
        stmt = select(AlertModel)
        if unread_only:
            stmt = stmt.where(AlertModel.read_at.is_(None))
        total = int(self._s.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0)
        rows = (
            self._s.execute(stmt.order_by(AlertModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
            .scalars()
            .all()
        )
        return [AlertOut.model_validate(r) for r in rows], total

    def mark_read(self, alert_id: str) -> None:
        row = self._s.get(AlertModel, alert_id)
        if row and row.read_at is None:
            row.read_at = utcnow()
            self._s.flush()

    def mark_all_read(self) -> None:
        self._s.execute(AlertModel.__table__.update().where(AlertModel.read_at.is_(None)).values(read_at=utcnow()))
        self._s.flush()

    def unread_count(self) -> int:
        return int(self._s.execute(select(func.count(AlertModel.id)).where(AlertModel.read_at.is_(None))).scalar() or 0)


# ------------------------------------------------------------------ audit
class SQLiteAuditRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, data: dict[str, Any]) -> str:
        row = AuditLogModel(id=new_id(), **data)
        self._s.add(row)
        self._s.flush()
        return row.id

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._s.execute(select(AuditLogModel).order_by(AuditLogModel.created_at.desc()).limit(limit)).scalars().all()
        return [
            {"id": r.id, "user_id": r.user_id, "action": r.action, "entity_type": r.entity_type, "entity_id": r.entity_id, "detail": r.detail, "created_at": r.created_at}
            for r in rows
        ]


# ------------------------------------------------------------------ anomalies
class SQLiteAnomalyRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def replace_all(self, rows: list[dict[str, Any]]) -> int:
        for r in rows:
            r = dict(r)
            r["observed_at"] = _norm(r.get("observed_at"))
        self._s.execute(AnomalyModel.__table__.delete())
        self._s.add_all([AnomalyModel(id=new_id(), **r) for r in rows])
        self._s.flush()
        return len(rows)

    def list_all(self, *, limit: int = 200, state: str = "", risk: str = "", metric: str = "") -> list[AnomalyOut]:
        stmt = select(AnomalyModel)
        if state:
            stmt = stmt.where(AnomalyModel.state == state)
        if risk:
            stmt = stmt.where(AnomalyModel.risk == risk)
        if metric:
            stmt = stmt.where(AnomalyModel.metric == metric)
        rows = self._s.execute(stmt.order_by(AnomalyModel.deviation_pct.desc()).limit(limit)).scalars().all()
        return [AnomalyOut.model_validate(r) for r in rows]

    def count(self) -> int:
        return int(self._s.execute(select(func.count(AnomalyModel.id))).scalar() or 0)

    def for_event(self, event_id: str) -> list[AnomalyOut]:
        rows = self._s.execute(select(AnomalyModel).where(AnomalyModel.event_id == event_id)).scalars().all()
        return [AnomalyOut.model_validate(r) for r in rows]

    def link_event(self, anomaly_id: str, event_id: str) -> None:
        row = self._s.get(AnomalyModel, anomaly_id)
        if row:
            row.event_id = event_id
            self._s.flush()

    def recent(self, limit: int = 12) -> list[AnomalyOut]:
        rows = self._s.execute(select(AnomalyModel).order_by(AnomalyModel.observed_at.desc()).limit(limit)).scalars().all()
        return [AnomalyOut.model_validate(r) for r in rows]


# ------------------------------------------------------------------ media
class SQLiteMediaRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, data: dict[str, Any]) -> MediaAnalyzeOut:
        row = MediaAnalysisModel(id=new_id(), **data)
        self._s.add(row)
        self._s.flush()
        return MediaAnalyzeOut.model_validate(row)

    def get(self, analysis_id: str) -> MediaAnalyzeOut | None:
        row = self._s.get(MediaAnalysisModel, analysis_id)
        return MediaAnalyzeOut.model_validate(row) if row else None

    def find_similar(self, phash: str, exclude_id: str | None = None, limit: int = 5) -> list[tuple[MediaAnalyzeOut, float]]:
        from app.ai.media import hamming_similarity

        rows = self._s.execute(select(MediaAnalysisModel).order_by(MediaAnalysisModel.created_at.desc()).limit(400)).scalars().all()
        scored: list[tuple[MediaAnalysisModel, float]] = []
        for r in rows:
            if exclude_id and r.id == exclude_id:
                continue
            if not r.phash or not phash:
                continue
            scored.append((r, hamming_similarity(phash, r.phash)))
        scored.sort(key=lambda t: t[1], reverse=True)
        return [(MediaAnalyzeOut.model_validate(r), s) for r, s in scored[:limit]]

    def list_recent(self, limit: int = 50) -> list[MediaAnalysisModel]:  # type: ignore[override]
        rows = self._s.execute(select(MediaAnalysisModel).order_by(MediaAnalysisModel.created_at.desc()).limit(limit)).scalars().all()
        return [MediaAnalyzeOut.model_validate(r) for r in rows]


# ------------------------------------------------------------------ simulation
class SQLiteSimulationRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_state(self) -> dict[str, Any]:
        row = self._s.execute(select(SimulationStateModel).limit(1)).scalar_one_or_none()
        if row is None:
            row = SimulationStateModel()
            self._s.add(row)
            self._s.flush()
        return {
            "running": row.running,
            "speed": row.speed,
            "scenario": row.scenario,
            "stage": row.stage,
            "ticks": row.ticks,
            "signals_generated": row.signals_generated,
        }

    def update_state(self, data: dict[str, Any]) -> None:
        row = self._s.execute(select(SimulationStateModel).limit(1)).scalar_one_or_none()
        if row is None:
            row = SimulationStateModel()
            self._s.add(row)
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = utcnow()
        self._s.flush()


# ------------------------------------------------------------------ ground reports
class SQLiteGroundReportRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, data: dict[str, Any]) -> GroundReportOut:
        row = GroundReportModel(id=new_id(), **data)
        self._s.add(row)
        self._s.flush()
        return GroundReportOut.model_validate(row)

    def get_by_tracking(self, tracking_id: str) -> GroundReportOut | None:
        row = self._s.execute(select(GroundReportModel).where(GroundReportModel.tracking_id == tracking_id)).scalar_one_or_none()
        return GroundReportOut.model_validate(row) if row else None

    def list_page(self, *, page: int, page_size: int) -> tuple[list[GroundReportOut], int]:
        total = int(self._s.execute(select(func.count(GroundReportModel.id))).scalar() or 0)
        rows = (
            self._s.execute(select(GroundReportModel).order_by(GroundReportModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
            .scalars()
            .all()
        )
        return [GroundReportOut.model_validate(r) for r in rows], total

    def set_status(self, report_id: str, status: str) -> None:
        row = self._s.get(GroundReportModel, report_id)
        if row:
            row.status = status
            self._s.flush()

    def count(self) -> int:
        return int(self._s.execute(select(func.count(GroundReportModel.id))).scalar() or 0)


# ------------------------------------------------------------------ unit of work
class SQLiteUnitOfWork:
    """Commits the request-scoped session. Repositories flush; this commits."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def commit(self) -> None:
        self._s.commit()

    def rollback(self) -> None:
        self._s.rollback()
