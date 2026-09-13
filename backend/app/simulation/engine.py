"""Live intelligence simulation engine.

Generates realistic signal bursts from demo connectors, pushes them through
the ingestion pipeline, and supports the signature "Mumbai Extreme Rainfall
→ Urban Flooding" scenario with 15 scripted stages.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import random
from typing import Any

from app.ai.trust import SOURCE_BASE_RELIABILITY  # noqa: F401
from app.connectors.base import CITIES
from app.connectors.demo_connectors import CONNECTOR_FACTORY

MUMBAI = next(c for c in CITIES if c["city"] == "Mumbai")
RECYCLED_URL = "https://demo.mausamnet.in/media/recycled_01.jpg"

SCENARIO_STAGES: list[str] = [
    "Rainfall anomaly appears",
    "Government weather signal",
    "Weather APIs confirm",
    "News signals appear",
    "Social signals cluster",
    "Candidate event created",
    "More image evidence",
    "Recycled media appears",
    "Trust engine evaluates",
    "Event confidence 94%",
    "Verification requested",
    "Verifier approves",
    "Dashboard: UNVERIFIED → VERIFIED",
    "Analytics update",
    "Timeline recorded",
]


class SimulationEngine:
    """Owns the asyncio task for live signal generation."""

    def __init__(self, registry_factory=None) -> None:
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._speed = 1.0
        self._scenario = "general"
        self._stage = 0
        self._ticks = 0
        self._generated = 0
        self._rng = random.Random(42)

    # ---------------------------------------------------------------- status
    def status(self) -> dict[str, Any]:
        return {
            "running": self._task is not None and not self._task.done(),
            "speed": self._speed,
            "scenario": self._scenario,
            "stage": self._stage,
            "ticks": self._ticks,
            "signals_generated": self._generated,
            "scenario_stages": SCENARIO_STAGES if self._scenario == "mumbai" else [],
        }

    # ---------------------------------------------------------------- control (async core)
    async def start(self, speed: float = 1.0, scenario: str = "general") -> dict[str, Any]:
        async with self._lock:
            if self._task is not None and not self._task.done():
                self._speed = max(0.5, min(5.0, speed))
                self._scenario = scenario if scenario in ("general", "mumbai") else "general"
                return self.status()
            self._speed = max(0.5, min(5.0, speed))
            self._scenario = scenario if scenario in ("general", "mumbai") else "general"
            if scenario == "mumbai":
                self._stage = 0
            self._task = asyncio.create_task(self._loop())
            await self._persist()
            return self.status()

    async def pause(self) -> dict[str, Any]:
        async with self._lock:
            if self._task:
                self._task.cancel()
                self._task = None
            await self._persist()
            return self.status()

    async def reset(self) -> dict[str, Any]:
        async with self._lock:
            if self._task:
                self._task.cancel()
                self._task = None
            self._speed = 1.0
            self._scenario = "general"
            self._stage = 0
            self._ticks = 0
            self._generated = 0
            await self._persist()
            from app import realtime

            realtime.publish("simulation_update", self.status())
            return self.status()

    # ---------------------------------------------------------------- sync wrappers for routes
    def start_sync(self, speed: float = 1.0, scenario: str = "general") -> dict[str, Any]:
        return _run_coro(self.start(speed, scenario))

    def pause_sync(self) -> dict[str, Any]:
        return _run_coro(self.pause())

    def reset_sync(self) -> dict[str, Any]:
        return _run_coro(self.reset())

    # ---------------------------------------------------------------- persistence
    async def _persist(self) -> None:
        def _work() -> None:
            from app.database.connection import SessionLocal
            from app.repositories.registry import RepositoryRegistry as R

            session = SessionLocal()
            try:
                reg = R(session)
                reg.simulation.update_state(self.status())
                reg.commit()
            finally:
                session.close()

        await asyncio.to_thread(_work)

    # ---------------------------------------------------------------- loop
    async def _loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(3.0 / max(self._speed, 0.5))
                self._ticks += 1
                await asyncio.to_thread(self._tick)
        except asyncio.CancelledError:
            pass
        except Exception:
            self._task = None

    # ---------------------------------------------------------------- tick
    def _tick(self) -> None:
        from app import realtime
        from app.database.connection import SessionLocal
        from app.repositories.registry import RepositoryRegistry as R
        from app.services.pipeline import IngestionService

        session = SessionLocal()
        try:
            reg = R(session)
            now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
            svc = IngestionService(reg)

            if self._scenario == "mumbai":
                self._tick_mumbai(reg, svc, now)
            else:
                self._tick_general(reg, svc, now)

            reg.simulation.update_state(self.status())
            reg.commit()
        finally:
            session.close()

    # ---------------------------------------------------------------- general mode
    def _tick_general(self, reg, svc, now: dt.datetime) -> None:
        from app import realtime

        rng = self._rng
        if self._ticks % 5 == 0:
            self._refresh_anomalies(reg)

        for cat, connector_cls in CONNECTOR_FACTORY.items():
            if rng.random() < 0.75:
                connector = connector_cls()
                raws = connector.fetch(now, rng)
                take = 2 if rng.random() < 0.5 else 1
                for raw in raws[:take]:
                    summary = svc.ingest(raw, publish_realtime=False)
                    self._generated += 1
                    realtime.publish("new_signal", _signal_payload(summary))
                    ev = summary.get("event")
                    if ev:
                        realtime.publish("event_created" if summary.get("event_created") else "event_updated", _event_payload(ev))
        realtime.publish("dashboard_update", {"ticks": self._ticks})
        realtime.publish("simulation_update", self.status())

    def _refresh_anomalies(self, reg) -> None:
        from app.ai.anomaly import StatisticalAnomalyDetector

        rows = reg.observations.stats_by_city(since=now_minus(dt.timedelta(days=3)))
        anomalies = StatisticalAnomalyDetector().detect(rows)
        if anomalies:
            reg.anomalies.replace_all(anomalies[:60])
            from app import realtime

            realtime.publish("anomaly_update", {"count": len(anomalies[:60])})

    # ---------------------------------------------------------------- mumbai scenario
    def _tick_mumbai(self, reg, svc, now: dt.datetime) -> None:
        from app import realtime

        rng = self._rng
        stage = self._stage
        mumbai = dict(MUMBAI)
        base = {
            "city": mumbai["city"], "district": mumbai["district"], "state": mumbai["state"],
            "latitude": mumbai["lat"] + rng.uniform(-0.03, 0.03),
            "longitude": mumbai["lon"] + rng.uniform(-0.03, 0.03),
            "occurred_at": now,
        }

        def _mk(category: str, headline: str, metrics: dict, **kw) -> dict[str, Any]:
            d = dict(base)
            d.update({
                "source_id": {"GOVERNMENT": "imd-demo", "WEATHER_API": "wxapi-demo", "NEWS": "news-demo", "SOCIAL": "social-demo", "CITIZEN": "ground-demo", "PUBLIC_DATASET": "dataset-demo"}.get(category, "social-demo"),
                "source_category": category,
                "headline": headline,
                "content": kw.get("content", "Simulated signal for the signature Mumbai flood demo scenario. DEMO DATA."),
                "metrics": metrics,
                "event_type": "FLOOD" if "flood" in headline.lower() or "waterlog" in headline.lower() or "underwater" in headline.lower() else ("RAINFALL" if stage < 4 else "FLOOD"),
                "severity": "CRITICAL" if stage >= 8 else "HIGH" if stage >= 3 else "MEDIUM",
            })
            if kw.get("media_url"):
                d["media_url"] = kw["media_url"]
            return d

        published: list[dict[str, Any]] = []
        if stage == 0:
            published.append(_mk("PUBLIC_DATASET", "Station S-4471 (Mumbai) logs 38 mm in 30 minutes — sharply above seasonal quantile.", {"rainfall_mm": 38}))
        elif stage == 1:
            published.append(_mk("GOVERNMENT", "IMD red alert: intense rainfall spell over Mumbai Suburban; 120 mm expected in 6 hours.", {"rainfall_mm": 96}))
        elif stage == 2:
            published.append(_mk("WEATHER_API", "Nowcast: convective cell stationary over Mumbai; 96 mm/hr precipitation estimate.", {"rainfall_mm": 96, "wind_kph": 42}))
        elif stage == 3:
            published.append(_mk("NEWS", "Mumbai: waterlogging reported on Western Express Highway; trains running late.", {"rainfall_mm": 88}))
        elif stage == 4:
            for i in range(3):
                published.append(_mk("SOCIAL", f"Posts from Andheri & Sion show flooded underpasses; #MumbaiRains trending.", {"rainfall_mm": 84}, media_url=f"https://demo.mausamnet.in/media/flood_{i:02d}.jpg"))
        elif stage == 6:
            for i in range(2):
                published.append(_mk("SOCIAL", "Citizen videos from Kurla and Dadar show submerged vehicles.", {"rainfall_mm": 90}, media_url=f"https://demo.mausamnet.in/media/flood_{i+3:02d}.jpg"))
        elif stage == 7:
            published.append(_mk("SOCIAL", "SHOCKING: Mumbai completely underwater!! Share everywhere!!", {"rainfall_mm": 220}, media_url=RECYCLED_URL, content="Recycled image test: phash matches August 2025 Ahmedabad flood image."))
            published.append(_mk("SOCIAL", "Old image circulating again as today's Mumbai flood", {"rainfall_mm": 90}, media_url=RECYCLED_URL))
            self._register_recycled_media(reg)
        elif stage == 8:
            published.append(_mk("GOVERNMENT", "IMD bulletin: rainfall intensity decreasing over Mumbai; orange alert continues.", {"rainfall_mm": 45}))
        elif stage == 9:
            published.append(_mk("NEWS", "Mumbai civic body pumps deployed; two locations report severe waterlogging.", {"rainfall_mm": 60}))
        else:
            published.append(_mk("WEATHER_API", "Mumbai nowcast: residual light rain, 12 mm/hr.", {"rainfall_mm": 12}))

        for raw in published:
            summary = svc.ingest(raw, publish_realtime=False)
            self._generated += 1
            realtime.publish("new_signal", _signal_payload(summary))
            if summary.get("event"):
                realtime.publish("event_created" if summary.get("event_created") else "event_updated", _event_payload(summary["event"]))

        # verification request once confidence is high (stage >= 10)
        mumbai_event = None
        events_list = reg.events.list_all({"state": "Maharashtra"}, limit=60)
        for e in events_list:
            if e.city == "Mumbai" and e.event_type in ("FLOOD", "RAINFALL") and e.status in ("CANDIDATE", "ACTIVE", "VERIFIED"):
                if mumbai_event is None or e.latest_at > mumbai_event.latest_at:
                    mumbai_event = e
                    
        if mumbai_event is not None:
            if "explanations" not in mumbai_event.fusion:
                mumbai_event.fusion["explanations"] = [
                    "✓ Rainfall anomaly detected",
                    "✓ Weather model agreement",
                    "✓ News corroboration",
                    "✓ Social cluster detected",
                    "✓ Satellite evidence",
                    "✓ Historical baseline exceeded"
                ]
                reg.events.update(mumbai_event.id, mumbai_event)

        if mumbai_event is not None and stage >= 10 and mumbai_event.status in ("CANDIDATE", "ACTIVE"):
            reg.alerts.create({
                "type": "VERIFICATION_TASK", "severity": mumbai_event.severity,
                "title": f"Verification requested: {mumbai_event.title}",
                "message": f"AI recommends VERIFY (confidence {mumbai_event.confidence:.0f}%, {mumbai_event.signal_count} signals).",
                "event_id": mumbai_event.id,
            })
            realtime.publish("alert_created", {"title": f"Verification requested: {mumbai_event.title}", "event_id": mumbai_event.id})

        if mumbai_event is not None and mumbai_event.status == "VERIFIED" and stage >= 12:
            realtime.publish("event_verified", {"event_id": mumbai_event.id, "title": mumbai_event.title})

        self._stage = min(stage + 1, 15)
        realtime.publish("dashboard_update", {"ticks": self._ticks})
        realtime.publish("simulation_update", self.status())

    def _register_recycled_media(self, reg) -> None:
        """Seed the media store with the 'old Ahmedabad' image so forensics finds it.

        The archive row stores the synthetic bytes of RECYCLED_URL, so a later
        forensics run on that URL hashes to the identical phash and similarity is
        exactly 100% (prototype determinism).
        """
        from app.ai.media import average_phash, synthetic_bytes_for_url

        image_bytes = synthetic_bytes_for_url(RECYCLED_URL)
        reg.media.create({
            "signal_id": None,
            "filename": "ahmedabad_flood_aug2025.jpg",
            "phash": average_phash(image_bytes),
            "width": 1280, "height": 720, "filesize": 245760, "format": "jpeg",
            "captured_at": dt.datetime(2025, 8, 12, 9, 30),
            "exif_ok": True,
            "similarity": 0.0,
            "match_signal_id": None,
            "previous_seen_at": dt.datetime(2025, 8, 12, 10, 0),
            "previous_location": "Ahmedabad",
            "finding": "ARCHIVE",
            "checks": {"claimed_location": "Ahmedabad", "note": "August 2025 Ahmedabad flood image (archive)"},
        })


def _signal_payload(summary: dict[str, Any]) -> dict[str, Any]:
    sig = summary["signal"]
    return {"id": sig.id, "headline": sig.headline, "source_category": sig.source_category, "city": sig.city, "severity": sig.severity, "trust_score": sig.trust_score}


def _event_payload(ev) -> dict[str, Any]:
    return {"id": ev.id, "title": ev.title, "confidence": ev.confidence, "severity": ev.severity, "signal_count": ev.signal_count, "status": ev.status, "city": ev.city}


def now_minus(delta: dt.timedelta) -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - delta


def _run_coro(coro):
    """Run a coroutine from sync route context, reusing the running loop if possible."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        # inside a running loop — can't block; execute as a task and wait
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(asyncio.run, coro).result()
    return asyncio.run(coro)
