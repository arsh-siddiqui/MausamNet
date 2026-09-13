"""Auth API: register, login, refresh, me, demo accounts."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import RegistryDep
from app.auth.security import (
    audit,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    rate_limit,
    verify_password,
)
from app.config import settings
from app.schemas.common import (
    USER_ROLES,
    DemoAccountsOut,
    LoginIn,
    RefreshIn,
    RegisterIn,
    TokenOut,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, request: Request, registry: RegistryDep):
    rate_limit(request)
    if payload.password != payload.confirm_password:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Passwords do not match")
    if payload.role not in ("ANALYST", "VERIFIER"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ADMIN role cannot be self-registered")
    if registry.users.get_by_email(payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = registry.users.create(
        email=payload.email,
        full_name=payload.full_name,
        organization=payload.organization,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    registry.commit()
    audit(registry, user_id=user.id, action="auth.register", entity_type="user", entity_id=user.id, ip=request.client.host if request.client else "")
    registry.commit()
    return TokenOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=user,
    )


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, registry: RegistryDep):
    rate_limit(request)
    user = registry.users.get_by_email(payload.email)
    if user is None or not verify_password(payload.password, registry.users.__class__ and _hashed(registry, payload.email)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    registry.commit()
    audit(registry, user_id=user.id, action="auth.login", entity_type="user", entity_id=user.id, ip=request.client.host if request.client else "")
    registry.commit()
    return TokenOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=user,
    )


def _hashed(registry: RegistryDep, email: str) -> str:
    """Fetch stored hash via session (kept out of UserOut for safety)."""
    from sqlalchemy import select

    from app.models.entities import UserModel

    row = registry.session.execute(select(UserModel.hashed_password).where(UserModel.email == email.lower().strip())).scalar_one_or_none()
    return row or ""


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: RefreshIn, registry: RegistryDep):
    claims = decode_token(payload.refresh_token)
    if not claims or claims.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    user = registry.users.get_by_id(claims["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return TokenOut(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=user,
    )


@router.get("/me", response_model=UserOut)
def me(user: UserOut = Depends(get_current_user)):
    return user


@router.get("/demo-accounts", response_model=list[DemoAccountsOut])
def demo_accounts():
    """Prototype convenience: demo credentials surfaced for one-click login.

    Passwords come from configuration (env), never hard-coded secrets.
    """
    return [
        DemoAccountsOut(email=settings.demo_analyst_email, password=settings.demo_analyst_password, role="ANALYST", label="Launch Analyst Demo"),
        DemoAccountsOut(email=settings.demo_verifier_email, password=settings.demo_verifier_password, role="VERIFIER", label="Launch Verifier Demo"),
        DemoAccountsOut(email=settings.demo_admin_email, password=settings.demo_admin_password, role="ADMIN", label="Launch Admin Demo"),
    ]
