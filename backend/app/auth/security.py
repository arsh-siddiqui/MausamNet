"""Authentication & authorization (prototype-grade, real primitives).

- Password hashing: passlib bcrypt.
- Tokens: JWT (python-jose) — access + refresh.
- Roles: ANALYST / VERIFIER / ADMIN with route guards.
- Simple in-memory rate limiter (per-process; swap for Redis later).
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict, deque
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings
from app.repositories.registry import RepositoryRegistry, get_registry
from app.schemas.common import UserOut

bearer_scheme = HTTPBearer(auto_error=False)


# ------------------------------------------------------------------ passwords
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# ------------------------------------------------------------------ tokens
def _create_token(subject: str, minutes: int, token_type: str) -> str:
    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)
    payload = {"sub": subject, "exp": expire, "type": token_type}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    return _create_token(user_id, settings.access_token_expire_minutes, "access")


def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id, settings.refresh_token_expire_minutes, "refresh")


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


# ------------------------------------------------------------------ current user
async def get_current_user(
    request: Request,
    registry: Annotated[RepositoryRegistry, Depends(get_registry)],
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserOut:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    claims = decode_token(credentials.credentials)
    if not claims or claims.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = registry.users.get_by_id(claims["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


CurrentUser = Annotated[UserOut, Depends(get_current_user)]


def require_roles(*roles: str):
    async def guard(user: CurrentUser) -> UserOut:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return guard


RequireVerifier = Depends(require_roles("VERIFIER", "ADMIN"))
RequireAdmin = Depends(require_roles("ADMIN"))


# ------------------------------------------------------------------ rate limiting
class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, deque[dt.datetime]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        q = self._hits[key]
        while q and (now - q[0]).total_seconds() > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests")
        q.append(now)


limiter = RateLimiter(settings.rate_limit_per_minute)


def rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    limiter.check(f"{request.method}:{request.url.path}:{client}")


# ------------------------------------------------------------------ audit
def audit(registry: RepositoryRegistry, *, user_id: str | None, action: str, entity_type: str = "", entity_id: str | None = None, detail: dict | None = None, ip: str = "") -> str:
    return registry.audit.create({
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "detail": detail or {},
        "ip": ip,
    })
