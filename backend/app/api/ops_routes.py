"""Analytics, verification, ground reports, AI endpoints, simulation, settings."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form, status

from app.ai.trust import SOURCE_BASE_RELIABILITY
from app.analytics.service import AnalyticsService
from app.api.deps import (
    AnalyticsServiceDep,
    GroundServiceDep,
    MediaServiceDep,
    RegistryDep,
)
from app.auth.security import audit, get_current_user, rate_limit
from app.config import settings
from app.schemas.common import (
    AnalyticsOverview,
    ClassifyIn,
    ClassifyOut,
    DuplicateCheckIn,
    DuplicateCheckOut,
    GroundReportIn,
    GroundReportOut,
    MediaAnalyzeOut,
    SettingsOut,
    SimulationControlIn,
    SimulationStatusOut,
    TrustScoreIn,
    TrustScoreOut,
    UserOut,
    VerificationActionIn,
    VerificationActionOut,
    VerificationItem,
)

router = APIRouter(tags=["ops"])


# ------------------------------------------------------------------ analytics
@router.get("/analytics/overview", response_model=AnalyticsOverview)
def analytics_overview(
    analytics: AnalyticsServiceDep, state: str = "", event_type: str = "", days: int = Query(14, ge=7, le=30),
    user: UserOut = Depends(get_current_user),
):
    return analytics.overview(state=state, event_type=event_type, days=days)


# ------------------------------------------------------------------ verification
@router.get("/verification/queue", response_model=list[VerificationItem])
def verification_queue(registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    events, _ = registry.events.list_page(filters={"status": "CANDIDATE"}, page=1, page_size=12, sort="confidence", direction="desc")
    high, _ = registry.events.list_page(filters={"status": "ACTIVE"}, page=1, page_size=8, sort="confidence", direction="desc")
    seen: set[str] = set()
    items: list[VerificationItem] = []
    for ev in events + high:
        if ev.id in seen:
            continue
        seen.add(ev.id)
        breakdown = (ev.metrics or {}).get("source_breakdown", {})
        rec = "VERIFY" if ev.confidence >= 75 and ev.trust_score >= 65 else ("INVESTIGATE" if ev.confidence >= 55 else "REJECT")
        evidence_summary = list((ev.fusion or {}).get("explanations", []))[:4]
        items.append(VerificationItem(
            event=ev, source_breakdown=breakdown, trust_score=ev.trust_score,
            ai_recommendation=rec, evidence_summary=evidence_summary,
        ))
    return items[:16]


@router.post("/verification/{event_id}/{action}", response_model=VerificationActionOut)
def verification_action(
    event_id: str, action: str, registry: RegistryDep, payload: VerificationActionIn | None = None,
    user: UserOut = Depends(get_current_user),
):
    if user.role not in ("ANALYST", "VERIFIER", "ADMIN"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Authorized role required")
    if user.role == "ANALYST" and action in ("verify", "reject"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ANALYST cannot verify or reject events")
    if action not in ("verify", "reject", "investigate", "escalate"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown action")
    ev = registry.events.get(event_id)
    if ev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")

    status_map = {
        "verify": "VERIFIED",
        "reject": "REJECTED",
        "investigate": "ACTIVE",      # stays active, flagged for investigation
        "escalate": "ACTIVE",
    }
    new_status = status_map[action]
    registry.events.update(event_id, {"status": new_status})

    rationale = (payload.rationale if payload else "") or ""
    audit_id = audit(registry, user_id=user.id, action=f"verification.{action}", entity_type="event", entity_id=event_id, detail={"rationale": rationale, "from_status": ev.status, "to_status": new_status})
    registry.verification.create({
        "event_id": event_id, "verifier_id": user.id, "action": action.upper(),
        "rationale": rationale, "ai_recommendation": "VERIFY" if ev.confidence >= 75 else "INVESTIGATE",
    })

    alert_type = {"verify": "EVENT_VERIFIED", "reject": "EVENT_REJECTED"}.get(action)
    if alert_type:
        registry.alerts.create({
            "type": alert_type, "severity": ev.severity, "title": f"Event {action.upper()}D: {ev.title}",
            "message": f"{ev.city}, {ev.state} — {ev.signal_count} signals, confidence {ev.confidence:.0f}%.",
            "event_id": event_id,
        })

    registry.commit()

    from app import realtime

    realtime.publish("verification_updated", {"event_id": event_id, "status": new_status, "action": action.upper()})
    realtime.publish("event_updated", {"event_id": event_id, "status": new_status})
    realtime.publish("dashboard_update", {})

    updated = registry.events.get(event_id)
    return VerificationActionOut(ok=True, event=updated, audit_id=audit_id)


@router.get("/verification/history")
def verification_history(registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    rows = registry.verification.recent(limit=25)
    out = []
    for r in rows:
        ev = registry.events.get(r["event_id"]) if r.get("event_id") else None
        verifier = registry.users.get_by_id(r["verifier_id"]) if r.get("verifier_id") else None
        out.append({**r, "event_title": ev.title if ev else None, "verifier_name": verifier.full_name if verifier else "Unknown"})
    return out


# ------------------------------------------------------------------ ground reports
@router.post("/ground-reports", response_model=GroundReportOut, status_code=201)
def submit_ground_report(payload: GroundReportIn, request: Request, ground: GroundServiceDep, user: UserOut = Depends(get_current_user)):
    rate_limit(request)
    report, error = ground.submit(payload.model_dump())
    if error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, error)
    return report


@router.get("/ground-reports")
def list_ground_reports(registry: RegistryDep, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), user: UserOut = Depends(get_current_user)):
    items, total = registry.ground_reports.list_page(page=page, page_size=page_size)
    pages = max(1, -(-total // page_size))
    return {"items": [GroundReportOut.model_validate(i) for i in items], "total": total, "page": page, "pages": pages}


@router.get("/ground-reports/{tracking_id}", response_model=GroundReportOut)
def ground_report_by_tracking(tracking_id: str, registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    report = registry.ground_reports.get_by_tracking(tracking_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tracking ID not found")
    return report


# ------------------------------------------------------------------ AI endpoints
@router.post("/ai/classify", response_model=ClassifyOut)
def ai_classify(payload: ClassifyIn, user: UserOut = Depends(get_current_user)):
    from app.ai.classifier import DemoEventClassifier

    result = DemoEventClassifier().classify(payload.headline, payload.content, payload.metrics)
    return ClassifyOut(**result)


@router.post("/ai/trust-score", response_model=TrustScoreOut)
def ai_trust_score(payload: TrustScoreIn, registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    from app.ai.trust import DemoTrustEngine
    from app.services.pipeline import cross_source_agreement, location_component, time_component, weather_evidence
    from app.settings_store import SettingsStore

    store = SettingsStore(registry)
    occurred = payload.occurred_at or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    wx = weather_evidence(registry, payload.city, occurred, payload.metrics)
    loc = location_component(payload.latitude, payload.longitude, payload.city)
    tim = time_component(occurred)
    cross = payload.cross_source_agreement or cross_source_agreement(registry, event_type="OTHER", latitude=payload.latitude, longitude=payload.longitude, occurred_at=occurred, exclude_id=None)
    result = DemoTrustEngine().score({
        "source_category": payload.source_category, "headline": payload.headline, "content": payload.content,
        "media_url": payload.media_url, "weather_evidence": wx, "location_component": loc,
        "time_component": tim, "cross_source_agreement": cross, "duplicate_score": payload.duplicate_score,
        "weights": store.trust_weights(),
    })
    return TrustScoreOut(**result)


@router.post("/ai/duplicate-check", response_model=DuplicateCheckOut)
def ai_duplicate_check(payload: DuplicateCheckIn, registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    from app.ai.duplicate import SpatialTemporalDuplicateDetector

    corpus = registry.signals.candidates_for_duplicate_check(since=payload.occurred_at - dt.timedelta(hours=48), limit=500)
    result = SpatialTemporalDuplicateDetector().check(payload.model_dump(), [s.model_dump() for s in corpus])
    return DuplicateCheckOut(**result)


@router.post("/ai/analyze-media", response_model=MediaAnalyzeOut)
async def ai_analyze_media(
    request: Request,
    registry: RegistryDep,
    media: MediaServiceDep = None,
    file: UploadFile | None = File(None),
    media_url: str = Form(""),
    claimed_location: str = Form(""),
    user: UserOut = Depends(get_current_user),
):
    rate_limit(request)
    if file is not None:
        allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in allowed:
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only JPEG/PNG/WebP/GIF images are accepted")
        data = await file.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Max upload size is {settings.max_upload_bytes // (1024*1024)} MB")
        if not data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty file")
        result = media.analyze_upload(filename=file.filename or "upload.jpg", image_bytes=data, claimed_location=claimed_location)
        return MediaAnalyzeOut(**result)
    if media_url:
        result = media.analyze_by_url(media_url=media_url)
        if result is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Could not analyze that media URL")
        return MediaAnalyzeOut(**result)
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Provide an image file or media_url")


# ------------------------------------------------------------------ simulation
@router.get("/simulation/status", response_model=SimulationStatusOut)
def simulation_status(registry: RegistryDep):
    from app.main import get_engine

    return SimulationStatusOut(**get_engine().status())


@router.post("/simulation/start", response_model=SimulationStatusOut)
def simulation_start(registry: RegistryDep, payload: SimulationControlIn | None = None, user: UserOut = Depends(get_current_user)):
    from app.main import get_engine

    body = payload or SimulationControlIn()
    return SimulationStatusOut(**get_engine().start_sync(speed=body.speed, scenario=body.scenario))


@router.post("/simulation/pause", response_model=SimulationStatusOut)
def simulation_pause(registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    from app.main import get_engine

    return SimulationStatusOut(**get_engine().pause_sync())


@router.post("/simulation/reset", response_model=SimulationStatusOut)
def simulation_reset(registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    from app.main import get_engine

    return SimulationStatusOut(**get_engine().reset_sync())


# ------------------------------------------------------------------ settings
@router.get("/settings", response_model=SettingsOut)
def get_settings_endpoint(registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    from app.settings_store import SettingsStore

    return SettingsOut(**SettingsStore(registry).all_settings())


@router.put("/settings", response_model=SettingsOut)
def update_settings(payload: dict, registry: RegistryDep, user: UserOut = Depends(get_current_user)):
    if user.role != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    from app.settings_store import RISK_THRESHOLD_KEYS, TRUST_WEIGHT_DEFAULTS, SettingsStore

    store = SettingsStore(registry)
    if "trust_weights" in payload:
        cleaned = {k: float(v) for k, v in payload["trust_weights"].items() if k in TRUST_WEIGHT_DEFAULTS}
        store.set("trust_weights", cleaned)
    if "risk_thresholds" in payload:
        cleaned = {k: float(v) for k, v in payload["risk_thresholds"].items() if k in RISK_THRESHOLD_KEYS}
        store.set("risk_thresholds", cleaned)
    if "simulation_speed" in payload:
        store.set("simulation_speed", float(payload["simulation_speed"]))
    registry.commit()
    audit(registry, user_id=user.id, action="settings.update", entity_type="settings", detail={"keys": list(payload.keys())})
    registry.commit()
    return SettingsOut(**store.all_settings())
