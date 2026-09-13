"""Shared FastAPI dependencies for route modules."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query

from app.analytics.service import AnalyticsService
from app.repositories.registry import RepositoryRegistry, get_registry
from app.services.system_service import SystemService
from app.services.view_service import (
    AnomalyService,
    DashboardService,
    EventService,
    GroundReportService,
    MediaForensicsService,
    SearchService,
    SignalService,
)

RegistryDep = Annotated[RepositoryRegistry, Depends(get_registry)]


def get_event_service(registry: RegistryDep) -> EventService:
    return EventService(registry)


def get_signal_service(registry: RegistryDep) -> SignalService:
    return SignalService(registry)


def get_dashboard_service(registry: RegistryDep) -> DashboardService:
    return DashboardService(registry)


def get_search_service(registry: RegistryDep) -> SearchService:
    return SearchService(registry)


def get_anomaly_service(registry: RegistryDep) -> AnomalyService:
    return AnomalyService(registry)


def get_ground_service(registry: RegistryDep) -> GroundReportService:
    return GroundReportService(registry)


def get_media_service(registry: RegistryDep) -> MediaForensicsService:
    return MediaForensicsService(registry)


def get_analytics_service(registry: RegistryDep) -> AnalyticsService:
    return AnalyticsService(registry)


def get_system_service(registry: RegistryDep) -> SystemService:
    return SystemService(registry)


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
SignalServiceDep = Annotated[SignalService, Depends(get_signal_service)]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
AnomalyServiceDep = Annotated[AnomalyService, Depends(get_anomaly_service)]
GroundServiceDep = Annotated[GroundReportService, Depends(get_ground_service)]
MediaServiceDep = Annotated[MediaForensicsService, Depends(get_media_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
SystemServiceDep = Annotated[SystemService, Depends(get_system_service)]

PageDep = Annotated[int, Query(ge=1, default=1)]
PageSizeDep = Annotated[int, Query(ge=1, le=100, default=25)]
