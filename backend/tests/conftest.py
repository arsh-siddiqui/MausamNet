"""Pytest fixtures — isolated temp SQLite database per test session."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parent))

# Point the app at a throwaway database BEFORE any app import happens.
_TMP = tempfile.mkdtemp(prefix="mausamnet-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["SEED_SIGNAL_COUNT"] = "400"

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seeded_db():
    from app.database.connection import init_db

    init_db()
    from tests import scripts_seed as _seed  # noqa: F401  (seed small deterministic dataset)

    _seed.main()

    yield


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def analyst_token(client):
    r = client.post("/api/auth/login", json={"email": "analyst@mausamnet.demo", "password": "demo-analyst-2026"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def verifier_token(client):
    r = client.post("/api/auth/login", json={"email": "verifier@mausamnet.demo", "password": "demo-verifier-2026"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def admin_token(client):
    r = client.post("/api/auth/login", json={"email": "admin@mausamnet.demo", "password": "demo-admin-2026"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def auth_headers(analyst_token):
    return {"Authorization": f"Bearer {analyst_token}"}
