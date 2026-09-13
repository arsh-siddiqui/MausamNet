"""Realtime event broker (Server-Sent Events).

Prototype: in-process pub/sub. Production: Redis pub/sub behind the same
endpoint contract. Frontend consumes `/api/realtime/events`.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
from typing import Any

_subscribers: set[asyncio.Queue] = set()
_lock = asyncio.Lock()


def utcnow_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


async def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    async with _lock:
        _subscribers.add(q)
    return q


async def unsubscribe(q: asyncio.Queue) -> None:
    async with _lock:
        _subscribers.discard(q)


def publish(event_type: str, payload: dict[str, Any]) -> None:
    """Fan-out to all subscribers (non-blocking, drops on full queue)."""
    msg = {"type": event_type, "payload": payload, "at": utcnow_iso()}
    data = json.dumps(msg, default=str)
    for q in list(_subscribers):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass


def subscriber_count() -> int:
    return len(_subscribers)
