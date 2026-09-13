"""Core read APIs: dashboard, events, signals, map, search, anomalies, alerts, sources, system."""
from __future__ import annotations

import datetime as dt
import random

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.trust import SOURCE_BASE_RELIABILITY
from app.api.deps import (
    AnalyticsServiceDep,
    AnomalyServiceDep,
    DashboardServiceDep,
    EventServiceDep,
    RegistryDep,
    SearchServiceDep,
    SignalServiceDep,
    SystemServiceDep,
)
from app.auth.security import get_current_user
from app.domain import SEVERITY_ORDER
from app.repositories.sqlite_repo import utcnow
from app.schemas.common import (
    AlertsPage,
    AnalyticsOverview,
    AnomalyOut,
    DashboardOverview,
    EventDetail,
    EventOut,
    EventsPage,
    MapPointOut,
    SearchResults,
    SignalDetail,
    SignalOut,
    SignalsPage,
    SourceOut,
    SystemHealthOut,
    UserOut,
)
from sqlalchemy import select

from app.models.entities import WeatherSignalModel

router = APIRouter(tags=["core"])


# ------------------------------------------------------------------ dashboard
@router.get("/dashboard/overview", response_model=DashboardOverview)
def dashboard_overview(dash: DashboardServiceDep, user: UserOut = Depends(get_current_user)):
    return dash.overview()


@router.get("/dashboard/recent-signals", response_model=list[SignalOut])
def dashboard_recent(dash: DashboardServiceDep, limit: int = 8, user: UserOut = Depends(get_current_user)):
    return dash.recent_intelligence(limit=limit)


@router.get("/dashboard/priority-queue", response_model=list[EventOut])
def dashboard_priority(dash: DashboardServiceDep, limit: int = 6, user: UserOut = Depends(get_current_user)):
    return dash.priority_queue(limit=limit)


@router.get("/dashboard/source-activity")
def dashboard_source_activity(dash: DashboardServiceDep, user: UserOut = Depends(get_current_user)):
    return dash.source_activity()


# ------------------------------------------------------------------ events
@router.get("/events", response_model=EventsPage)
def list_events(
    q: str = "",
    event_type: str = "",
    severity: str = "",
    status_filter: str = Query("", alias="status"),
    state: str = "",
    min_confidence: float = 0.0,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort: str = "latest_at",
    direction: str = "desc",
    events: EventServiceDep = None,
    user: UserOut = Depends(get_current_user),
):
    filters = {"q": q, "event_type": event_type, "severity": severity, "status": status_filter, "state": state, "min_confidence": min_confidence}
    items, total = events.list(filters, page, page_size, sort, direction)
    pages = max(1, -(-total // page_size))
    return EventsPage(items=items, total=total, page=page, pages=pages)


@router.get("/events/{event_id}", response_model=EventDetail)
def event_detail(event_id: str, events: EventServiceDep, user: UserOut = Depends(get_current_user)):
    ev = events.detail(event_id)
    if ev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    return ev


# ------------------------------------------------------------------ signals
@router.get("/signals", response_model=SignalsPage)
def list_signals(
    q: str = "",
    source: str = "",
    event_type: str = "",
    severity: str = "",
    status_filter: str = Query("", alias="status"),
    state: str = "",
    city: str = "",
    suspicious_only: bool = False,
    duplicate_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort: str = "occurred_at",
    direction: str = "desc",
    registry: RegistryDep = None,
    user: UserOut = Depends(get_current_user),
):
    filters = {
        "q": q, "source": source, "event_type": event_type, "severity": severity,
        "status": status_filter, "state": state, "city": city,
        "suspicious_only": suspicious_only, "duplicate_only": duplicate_only,
    }
    items, total = registry.signals.list_page(filters=filters, page=page, page_size=page_size, sort=sort, direction=direction)
    pages = max(1, -(-total // page_size))
    return SignalsPage(items=items, total=total, page=page, pages=pages)


@router.get("/signals/{signal_id}", response_model=SignalDetail)
def signal_detail(signal_id: str, signals: SignalServiceDep, user: UserOut = Depends(get_current_user)):
    sig = signals.detail(signal_id)
    if sig is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Signal not found")
    return sig


@router.post("/signals", response_model=SignalOut, status_code=201)
def create_signal(payload: dict, registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    """Manual signal creation — runs the full AI pipeline."""
    from app.services.pipeline import IngestionService

    svc = IngestionService(registry)
    summary = svc.ingest(payload)
    return summary["signal"]


# ------------------------------------------------------------------ live map
@router.get("/map/points", response_model=list[MapPointOut])
def map_points(
    layer: str = "events",
    hours: int = 72,
    state: str = "",
    severity: str = "",
    event_type: str = "",
    limit: int = Query(400, le=1500),
    registry: RegistryDep = None,
    user: UserOut = Depends(get_current_user),
):  # noqa: F722
    since = utcnow() - dt.timedelta(hours=hours)
    points: list[MapPointOut] = []
    
    include_signals = layer in ("signals", "all")
    include_anomalies = layer in ("anomalies", "all")
    include_events = layer in ("events", "all")
    
    if include_signals:
        rows, _ = registry.signals.list_page(
            filters={"since": since, "state": state, "severity": severity, "event_type": event_type},
            page=1, page_size=min(limit, 1000), sort="occurred_at", direction="desc",
        )
        for s in rows:
            points.append(MapPointOut(
                id=s.id, kind="signal", latitude=s.latitude, longitude=s.longitude,
                title=s.headline, event_type=s.event_type, severity=s.severity,
                source_category=s.source_category, trust_score=s.trust_score,
                suspicious=s.suspicious, occurred_at=s.occurred_at,
                state=s.state, district=s.district, city=s.city
            ))
    if include_anomalies:
        for a in registry.anomalies.list_all(limit=200, state=state):
            points.append(MapPointOut(
                id=a.id, kind="anomaly", latitude=a.latitude, longitude=a.longitude,
                title=f"{a.city} {a.metric.title()} Anomaly", event_type="RAINFALL" if a.metric == "RAINFALL" else "OTHER",
                severity=a.risk, deviation_pct=a.deviation_pct, metric=a.metric, occurred_at=a.observed_at,
                state=a.state, district=a.district, city=a.city
            ))
    if include_events:
        events = registry.events.list_all(
            {"state": state, "severity": severity, "event_type": event_type}, limit=min(limit, 800)
        )
        for e in events:
            if e.latest_at >= since or e.status in ("ACTIVE", "CANDIDATE", "VERIFIED"):
                points.append(MapPointOut(
                    id=e.id, kind="event", latitude=e.latitude, longitude=e.longitude,
                    title=e.title, event_type=e.event_type, severity=e.severity, status=e.status,
                    confidence=e.confidence, trust_score=e.trust_score, signal_count=e.signal_count,
                    state=e.state, district=e.district, city=e.city
                ))
    return points


# ------------------------------------------------------------------ search
@router.get("/search", response_model=SearchResults)
def global_search(q: str, search: SearchServiceDep, user: UserOut = Depends(get_current_user)):
    return search.search(q)


# ------------------------------------------------------------------ anomalies
@router.get("/anomalies", response_model=list[AnomalyOut])
def list_anomalies(anomalies: AnomalyServiceDep, state: str = "", risk: str = "", metric: str = "", user: UserOut = Depends(get_current_user)):
    return anomalies.list(state=state, risk=risk, metric=metric)


@router.get("/anomalies/series")
def anomaly_series(anomalies: AnomalyServiceDep, city: str, metric: str = "rainfall_mm", user: UserOut = Depends(get_current_user)):
    return anomalies.series_for(city, metric)


# ------------------------------------------------------------------ alerts
@router.get("/alerts", response_model=AlertsPage)
def list_alerts(
    page: int = Query(1, ge=1), page_size: int = Query(15, ge=1, le=50),
    unread_only: bool = False, registry: RegistryDep = None, user: UserOut = Depends(get_current_user),
):
    items, total = registry.alerts.list_page(page=page, page_size=page_size, unread_only=unread_only)
    pages = max(1, -(-total // page_size))
    return AlertsPage(items=items, total=total, page=page, pages=pages)


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: str, registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    registry.alerts.mark_read(alert_id)
    registry.commit()
    return {"ok": True}


@router.post("/alerts/read-all")
def mark_all_alerts_read(registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    registry.alerts.mark_all_read()
    registry.commit()
    return {"ok": True}


@router.get("/alerts/unread-count")
def unread_count(registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    return {"count": registry.alerts.unread_count()}


# ------------------------------------------------------------------ sources
@router.get("/sources", response_model=list[SourceOut])
def list_sources(registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    return registry.sources.list_all()


@router.get("/sources/health")
def sources_health(system: SystemServiceDep, user: UserOut = Depends(get_current_user)):
    return system.source_health()


@router.post("/sources/{source_id}/mode")
def set_source_mode(source_id: str, payload: dict, registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    if user.role != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    mode = payload.get("mode", "DEMO")
    if mode not in ("DEMO", "LIVE"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "mode must be DEMO or LIVE")
    registry.sources.set_mode(source_id, mode)
    registry.commit()
    return {"ok": True, "id": source_id, "mode": mode}


# ------------------------------------------------------------------ system
@router.get("/system/health", response_model=SystemHealthOut)
def system_health(system: SystemServiceDep, user: UserOut = Depends(get_current_user)):
    h = system.health()
    return SystemHealthOut(**h)


# ------------------------------------------------------------------ stats helper for landing page
@router.get("/public/stats")
def public_stats(registry: RegistryDep = None):
    """Prototype statistics for the public landing page (SIMULATED DEMO DATA)."""
    total = registry.signals.count()
    # deterministic "big national numbers" derived from real counts
    display_signals = 18420 if total < 1000 else total
    events_active = registry.events.count({"status": "ACTIVE"}) + registry.events.count({"status": "CANDIDATE"})
    suspicious = registry.signals.count({"suspicious_only": True})
    states = len({s.state for s in registry.events.list_all(limit=400)})
    return {
        "signals_processed": display_signals,
        "active_events": events_active,
        "suspicious_signals": suspicious,
        "states_monitored": states,
        "demo": True,
    }
