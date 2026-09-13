"""Authentication & authorization tests."""
from __future__ import annotations


def test_register_login_me(client):
    r = client.post("/api/auth/register", json={
        "full_name": "Test Analyst", "email": "t1@example.com", "organization": "QA",
        "password": "supersecret1", "confirm_password": "supersecret1", "role": "ANALYST",
    })
    assert r.status_code == 201, r.text
    tok = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert me.status_code == 200
    assert me.json()["role"] == "ANALYST"


def test_register_rejects_admin_role(client):
    r = client.post("/api/auth/register", json={
        "full_name": "Sneaky Admin", "email": "t2@example.com", "organization": "QA",
        "password": "supersecret1", "confirm_password": "supersecret1", "role": "ADMIN",
    })
    assert r.status_code == 403


def test_register_password_mismatch(client):
    r = client.post("/api/auth/register", json={
        "full_name": "Mismatch", "email": "t3@example.com", "organization": "QA",
        "password": "supersecret1", "confirm_password": "different123", "role": "ANALYST",
    })
    assert r.status_code == 422


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"email": "analyst@mausamnet.demo", "password": "wrong-password"})
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    r = client.get("/api/dashboard/overview")
    assert r.status_code == 401


def test_demo_accounts_endpoint(client):
    r = client.get("/api/auth/demo-accounts")
    assert r.status_code == 200
    accounts = r.json()
    assert len(accounts) == 3
    assert {a["role"] for a in accounts} == {"ANALYST", "VERIFIER", "ADMIN"}


def test_admin_only_settings_update(client, analyst_token, admin_token):
    r = client.put("/api/settings", headers={"Authorization": f"Bearer {analyst_token}"}, json={"simulation_speed": 2.0})
    assert r.status_code == 403
    r = client.put("/api/settings", headers={"Authorization": f"Bearer {admin_token}"}, json={"simulation_speed": 2.0})
    assert r.status_code == 200


def test_verifier_only_actions(client, analyst_token, verifier_token):
    # find a pending event
    q = client.get("/api/verification/queue", headers={"Authorization": f"Bearer {verifier_token}"})
    assert q.status_code == 200
    items = q.json()
    if not items:
        return
    event_id = items[0]["event"]["id"]
    r = client.post(f"/api/verification/{event_id}/verify", headers={"Authorization": f"Bearer {analyst_token}"}, json={"rationale": "try"})
    assert r.status_code == 403
    r = client.post(f"/api/verification/{event_id}/verify", headers={"Authorization": f"Bearer {verifier_token}"}, json={"rationale": "ok"})
    assert r.status_code == 200
    assert r.json()["event"]["status"] == "VERIFIED"
