"""Repository registry — the single switchboard between services and storage.

Today: SQLite. Tomorrow: MongoDB. Services never know the difference.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.repositories.interfaces import (
    AlertRepository,
    AuditRepository,
    EventRepository,
    EvidenceRepository,
    GroundReportRepository,
    MediaRepository,
    ObservationRepository,
    SignalRepository,
    SimulationRepository,
    SourceRepository,
    UserRepository,
    VerificationRepository,
)
from app.repositories.sqlite_repo import (
    SQLiteAlertRepository,
    SQLiteAuditRepository,
    SQLiteEventRepository,
    SQLiteEvidenceRepository,
    SQLiteGroundReportRepository,
    SQLiteGraphRepository,
    SQLiteMediaRepository,
    SQLiteObservationRepository,
    SQLiteAnomalyRepository,
    SQLiteSignalRepository,
    SQLiteSimulationRepository,
    SQLiteSourceRepository,
    SQLiteUserRepository,
    SQLiteVerificationRepository,
)


class RepositoryRegistry:
    """Per-request container holding every repository.

    To migrate to MongoDB: instantiate this class with Mongo-backed
    implementations of the same interfaces. Zero service changes.
    """

    def __init__(self, session: Session) -> None:
        self.users: UserRepository = SQLiteUserRepository(session)
        self.sources: SourceRepository = SQLiteSourceRepository(session)
        self.signals: SignalRepository = SQLiteSignalRepository(session)
        self.events: EventRepository = SQLiteEventRepository(session)
        self.evidence: EvidenceRepository = SQLiteEvidenceRepository(session)
        self.graph = SQLiteGraphRepository(session)
        self.observations: ObservationRepository = SQLiteObservationRepository(session)
        self.verification: VerificationRepository = SQLiteVerificationRepository(session)
        self.alerts: AlertRepository = SQLiteAlertRepository(session)
        self.audit: AuditRepository = SQLiteAuditRepository(session)
        self.anomalies: AnomalyRepository = SQLiteAnomalyRepository(session)
        self.media: MediaRepository = SQLiteMediaRepository(session)
        self.simulation: SimulationRepository = SQLiteSimulationRepository(session)
        self.ground_reports: GroundReportRepository = SQLiteGroundReportRepository(session)
        self.session = session

    # -- transaction boundary -----------------------------------------
    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


def get_registry():
    """FastAPI dependency: yields a per-request RepositoryRegistry."""
    session = SessionLocal()
    try:
        reg = RepositoryRegistry(session)
        yield reg
    finally:
        session.close()
