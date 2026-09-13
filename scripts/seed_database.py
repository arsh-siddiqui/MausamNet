#!/usr/bin/env python
"""Seed the MausamNet prototype database with deterministic demo data.

Usage:
    cd backend
    python ../scripts/seed_database.py          # or: python -m scripts.seed_database
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parent))

import datetime as dt
import random

from app.auth.security import hash_password
from app.config import settings, DB_DIR
from app.database.connection import SessionLocal, init_db
from app.repositories.registry import RepositoryRegistry
from app.repositories.sqlite_repo import utcnow
from scripts.seed_data import (
    SOURCE_DEFAULTS,
    build_clusters,
    generate_alerts,
    generate_observations,
    generate_signals,
)


def main() -> None:
    print("== MausamNet database seeding ==")
    init_db()
    db = SessionLocal()
    reg = RepositoryRegistry(db)
    rng = random.Random(2026)

    try:
        # ---------------- users ------------------------------------------------
        from app.models.entities import UserModel

        existing_users = reg.users.count()
        demo_accounts = [
            {"email": settings.demo_admin_email, "password": settings.demo_admin_password, "role": "ADMIN", "name": "Demo Admin", "org": "MND (Demo)"},
            {"email": settings.demo_verifier_email, "password": settings.demo_verifier_password, "role": "VERIFIER", "name": "Demo Verifier", "org": "Verification Cell (Demo)"},
            {"email": settings.demo_analyst_email, "password": settings.demo_analyst_password, "role": "ANALYST", "name": "Demo Analyst", "org": "Analysis Wing (Demo)"},
        ]
        if existing_users == 0:
            for acct in demo_accounts:
                reg.users.create(
                    email=acct["email"], full_name=acct["name"], organization=acct["org"],
                    hashed_password=hash_password(acct["password"]), role=acct["role"],
                )
            print(f"  users: created {len(demo_accounts)} demo accounts")
        else:
            print(f"  users: {existing_users} exist, skipping")

        # ---------------- sources ------------------------------------------------
        reg.sources.upsert_defaults(SOURCE_DEFAULTS)
        print(f"  sources: {len(SOURCE_DEFAULTS)} connectors registered")

        # ---------------- observations ----------------------------------------------
        if reg.observations.stats_by_city() == []:
            observations = generate_observations(days=21)
            reg.observations.bulk_create(observations)
            print(f"  observations: {len(observations)} rows")
        else:
            print("  observations: exist, skipping")

        # ---------------- signals ------------------------------------------------
        target = max(2000, settings.seed_signal_count)
        if reg.signals.count() < 500:
            signals = generate_signals(target, observations, rng)
            created = []
            for chunk_start in range(0, len(signals), 500):
                for s in signals[chunk_start: chunk_start + 500]:
                    created.append(reg.signals.create(s))
            print(f"  signals: {len(created)} generated")

            # ---------------- events via clustering -----------------------------------
            clusters = build_clusters([c.model_dump() for c in created], rng)
            events_created = []
            from app.services.pipeline import IngestionService

            svc = IngestionService(reg)
            for members in clusters:
                first = members[0]
                ev = reg.events.create({
                    "title": f"{first['city']} {first['event_type'].replace('_',' ').title()}",
                    "event_type": first["event_type"],
                    "severity": first["severity"],
                    "status": "CANDIDATE",
                    "latitude": sum(m["latitude"] for m in members) / len(members),
                    "longitude": sum(m["longitude"] for m in members) / len(members),
                    "city": first["city"],
                    "district": first["district"],
                    "state": first["state"],
                    "started_at": min(m["occurred_at"] for m in members),
                    "latest_at": max(m["occurred_at"] for m in members),
                    "signal_count": 0,
                })
                reg.signals.set_event([m["id"] for m in members], ev.id)
                summary = svc.rebuild_event(ev.id)
                events_created.append(summary["event"])
            print(f"  events: {len(events_created)} built from clusters")

            # ---------------- statuses: verify a share deterministically ----------------
            verified = 0
            for ev in events_created:
                if ev.status in ("CANDIDATE", "ACTIVE") and ev.confidence >= 82 and rng.random() < 0.55:
                    reg.events.update(ev.id, {"status": "VERIFIED"})
                    admin = reg.users.get_by_email(settings.demo_admin_email)
                    reg.verification.create({
                        "event_id": ev.id, "verifier_id": admin.id, "action": "VERIFY",
                        "rationale": "Auto-verified by seed: strong multi-source evidence.",
                        "ai_recommendation": "VERIFY", "created_at": ev.latest_at,
                    })
                    verified += 1
            print(f"  events: {verified} auto-verified by seed")

            # ---------------- alerts ------------------------------------------------
            refreshed = reg.events.list_all(limit=200)
            alerts = generate_alerts(refreshed, rng)
            for a in alerts:
                reg.alerts.create(a)
            print(f"  alerts: {len(alerts)}")

            # ---------------- anomalies ------------------------------------------------
            from app.ai.anomaly import StatisticalAnomalyDetector

            stats = reg.observations.stats_by_city(since=utcnow() - dt.timedelta(days=10))
            anomalies = StatisticalAnomalyDetector().detect(stats)
            if anomalies:
                reg.anomalies.replace_all(anomalies[:80])
            print(f"  anomalies: {min(len(anomalies), 80)} stored")

            # link anomalies to matching events
            for an in reg.anomalies.list_all(limit=100):
                for ev in refreshed:
                    if an.event_id is None and ev.city == an.city and ev.event_type in ("RAINFALL", "FLOOD"):
                        reg.anomalies.link_event(an.id, ev.id)
                        break
        else:
            print("  signals/events: already seeded, skipping")

        # ---------------- media archive (recycled-media demo) -----------------------------
        from app.ai.media import average_phash, synthetic_bytes_for_url
        from app.simulation.engine import RECYCLED_URL

        archive_name = "ahmedabad_flood_aug2025.jpg"
        if all(m.filename != archive_name for m in reg.media.list_recent(limit=200)):
            image_bytes = synthetic_bytes_for_url(RECYCLED_URL)
            reg.media.create({
                "signal_id": None,
                "filename": archive_name,
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
            print("  media archive: recycled-image demo row registered")

        # ---------------- simulation state ------------------------------------------------
        reg.simulation.update_state({"running": False, "speed": 1.0, "scenario": "general", "stage": 0, "ticks": 0, "signals_generated": 0})

        reg.commit()
        print("== Seeding complete ==")
        print(f"   DB: {DB_DIR / 'mausamnet.db'}")
        print("   Demo logins: analyst@mausamnet.demo / verifier@mausamnet.demo / admin@mausamnet.demo (passwords in .env.example)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
