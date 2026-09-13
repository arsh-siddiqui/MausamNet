"""MausamNet FastAPI application entrypoint.

Run:  uvicorn app.main:app --reload --port 8000   (from backend/)
"""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app import realtime
from app.api import auth_routes, core_routes, ops_routes
from app.auth.security import decode_token
from app.config import settings
from app.database.connection import init_db
from app.simulation.engine import SimulationEngine

_engine: SimulationEngine | None = None


def get_engine() -> SimulationEngine:
    global _engine
    if _engine is None:
        _engine = SimulationEngine()
    return _engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    eng = get_engine()
    if eng._task is not None and not eng._task.done():
        eng._task.cancel()


app = FastAPI(
    title="MausamNet API",
    version=settings.app_version,
    description="National Weather Intelligence & Verification Platform — prototype API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def safe_error_handler(request: Request, exc: Exception):
    """Safe error messages — never leak internals to the client."""
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth_routes.router, prefix=settings.api_prefix)
app.include_router(core_routes.router, prefix=settings.api_prefix)
app.include_router(ops_routes.router, prefix=settings.api_prefix)


# ------------------------------------------------------------------ realtime (SSE)
@app.get("/api/realtime/events")
async def realtime_events(request: Request, token: str = ""):
    """Server-Sent Events stream. EventSource cannot send Authorization
    headers, so the access token may be passed as ?token= (prototype)."""
    if token:
        claims = decode_token(token)
        if not claims or claims.get("type") != "access":
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Invalid token"})

    queue = await realtime.subscribe()

    async def stream():
        try:
            yield {"event": "connected", "data": json.dumps({"type": "connected", "at": realtime.utcnow_iso()})}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {"event": "message", "data": message}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            await realtime.unsubscribe(queue)

    return EventSourceResponse(stream())


@app.get("/api/health")
async def public_health():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version, "environment": settings.environment}


@app.get("/")
async def root():
    return {"app": settings.app_name, "docs": "/docs", "api": settings.api_prefix}
