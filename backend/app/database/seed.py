"""Automatic, idempotent startup database seeding for MausamNet."""
from __future__ import annotations

import datetime as dt
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.auth.security import hash_password
from app.config import settings
from app.database.connection import SessionLocal
from app.repositories.registry import RepositoryRegistry


def seed_demo_users_and_data() -> None:
    db = SessionLocal()
    try:
        reg = RepositoryRegistry(db)

        # 1. Seed demo accounts (commit IMMEDIATELY)
        demo_accounts = [
            {
                "email": settings.demo_admin_email,
                "password": settings.demo_admin_password,
                "role": "ADMIN",
                "name": "Demo Admin",
                "org": "MND (Demo)",
            },
            {
                "email": settings.demo_verifier_email,
                "password": settings.demo_verifier_password,
                "role": "VERIFIER",
                "name": "Demo Verifier",
                "org": "Verification Cell (Demo)",
            },
            {
                "email": settings.demo_analyst_email,
                "password": settings.demo_analyst_password,
                "role": "ANALYST",
                "name": "Demo Analyst",
                "org": "Analysis Wing (Demo)",
            },
        ]

        users_created = 0
        for acct in demo_accounts:
            email_clean = acct["email"].lower().strip()
            if reg.users.get_by_email(email_clean) is None:
                reg.users.create(
                    email=email_clean,
                    full_name=acct["name"],
                    organization=acct["org"],
                    hashed_password=hash_password(acct["password"]),
                    role=acct["role"],
                )
                users_created += 1

        if users_created > 0:
            reg.commit()
            print(f"[Seed] Created {users_created} demo user accounts successfully.")

        # 2. Seed initial sources & prototype data if DB has no signals
        from scripts.seed_data import SOURCE_DEFAULTS
        reg.sources.upsert_defaults(SOURCE_DEFAULTS)
        reg.commit()

        if reg.signals.count() == 0:
            print("[Seed] Seeding prototype signals and events...")
            _seed_prototype_data(reg)
            reg.commit()

    except Exception as exc:
        db.rollback()
        print("[Seed Error]", exc)
    finally:
        db.close()


def _seed_prototype_data(reg: RepositoryRegistry) -> None:
    from scripts.seed_data import (
        build_clusters,
        generate_alerts,
        generate_observations,
        generate_signals,
    )
    rng = random.Random(2026)
    observations = generate_observations(days=21)
    reg.observations.bulk_create(observations)

    # Seed 1200 signals for fast startup
    signals = generate_signals(1200, observations, rng)
    created = [reg.signals.create(s) for s in signals]
    reg.commit()

    clusters = build_clusters([c.model_dump() for c in created], rng)
    from app.services.pipeline import IngestionService
    svc = IngestionService(reg)
    events_created = []

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

    admin = reg.users.get_by_email(settings.demo_admin_email)
    for ev in events_created:
        if ev.status in ("CANDIDATE", "ACTIVE") and ev.confidence >= 82 and rng.random() < 0.55:
            reg.events.update(ev.id, {"status": "VERIFIED"})
            if admin:
                reg.verification.create({
                    "event_id": ev.id,
                    "verifier_id": admin.id,
                    "action": "VERIFY",
                    "rationale": "Auto-verified by seed: strong multi-source evidence.",
                    "ai_recommendation": "VERIFY",
                    "created_at": ev.latest_at,
                })

    refreshed = reg.events.list_all(limit=200)
    alerts = generate_alerts(refreshed, rng)
    for a in alerts:
        reg.alerts.create(a)

    from app.ai.anomaly import StatisticalAnomalyDetector
    stats = reg.observations.stats_by_city(since=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(days=10))
    anomalies = StatisticalAnomalyDetector().detect(stats)
    if anomalies:
        reg.anomalies.replace_all(anomalies[:80])
