"""Small deterministic seed used by the test suite (subset of full seeding)."""
from __future__ import annotations

import datetime as dt
import random

from app.auth.security import hash_password
from app.config import settings
from app.database.connection import SessionLocal
from app.repositories.registry import RepositoryRegistry
from scripts.seed_data import SOURCE_DEFAULTS, build_clusters, generate_observations, generate_signals


def main() -> None:
    init = SessionLocal()
    reg = RepositoryRegistry(init)
    rng = random.Random(99)

    if reg.users.count() == 0:
        for acct in [
            (settings.demo_admin_email, settings.demo_admin_password, "ADMIN", "Demo Admin"),
            (settings.demo_verifier_email, settings.demo_verifier_password, "VERIFIER", "Demo Verifier"),
            (settings.demo_analyst_email, settings.demo_analyst_password, "ANALYST", "Demo Analyst"),
        ]:
            reg.users.create(email=acct[0], full_name=acct[3], organization="QA", hashed_password=hash_password(acct[1]), role=acct[2])

    reg.sources.upsert_defaults(SOURCE_DEFAULTS)
    observations = generate_observations(days=10, rng=rng)
    reg.observations.bulk_create(observations)
    signals = generate_signals(int(settings.seed_signal_count), observations, rng)
    created = [reg.signals.create(s) for s in signals]
    clusters = build_clusters([c.model_dump() for c in created], rng, min_signals=3)
    from app.services.pipeline import IngestionService

    svc = IngestionService(reg)
    for members in clusters:
        first = members[0]
        ev = reg.events.create({
            "title": f"{first['city']} {first['event_type'].replace('_',' ').title()}",
            "event_type": first["event_type"], "severity": first["severity"], "status": "CANDIDATE",
            "latitude": sum(m["latitude"] for m in members) / len(members),
            "longitude": sum(m["longitude"] for m in members) / len(members),
            "city": first["city"], "district": first["district"], "state": first["state"],
            "started_at": min(m["occurred_at"] for m in members),
            "latest_at": max(m["occurred_at"] for m in members),
        })
        reg.signals.set_event([m["id"] for m in members], ev.id)
        svc.rebuild_event(ev.id)
    reg.commit()
    init.close()


main()
