"""Application configuration.

All settings are environment-driven (12-factor). The prototype has NO
required secrets or API keys — every external integration runs in demo
mode until credentials are provided.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = BACKEND_DIR / "database"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "MausamNet"
    app_version: str = "0.1.0"
    environment: str = "prototype"
    api_prefix: str = "/api"

    # --- security -------------------------------------------------
    jwt_secret: str = "mausamnet-prototype-secret-do-not-use-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    refresh_token_expire_minutes: int = 60 * 24 * 7

    # --- database -------------------------------------------------
    database_url: str = f"sqlite:///{DB_DIR / 'mausamnet.db'}"

    # --- demo accounts (seeded) -----------------------------------
    demo_analyst_email: str = "analyst@mausamnet.demo"
    demo_analyst_password: str = "demo-analyst-2026"
    demo_verifier_email: str = "verifier@mausamnet.demo"
    demo_verifier_password: str = "demo-verifier-2026"
    demo_admin_email: str = "admin@mausamnet.demo"
    demo_admin_password: str = "demo-admin-2026"

    # --- runtime limits -------------------------------------------
    max_upload_bytes: int = 8 * 1024 * 1024  # 8 MB
    rate_limit_per_minute: int = 120

    # --- apis -----------------------------------------------------
    open_meteo_api_url: str = "https://api.open-meteo.com/v1"
    weather_api_url: str = "https://api.openweathermap.org"
    weather_api_key: str | None = None
    news_api_url: str = "https://newsapi.org/v2"
    news_api_key: str | None = None

    # --- simulation ------------------------------------------------
    simulation_default_speed: float = 1.0
    seed_signal_count: int = 18000


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

DB_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
