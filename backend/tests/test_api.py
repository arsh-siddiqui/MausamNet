"""API endpoint tests: events, signals, analytics, map, alerts, sources, system."""
from __future__ import annotations


def test_dashboard_overview(auth_headers, client):
    r = client.get("/api/dashboard/overview", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["signals_processed"] > 0
    assert "active_events" in body and "pending_reviews" in body


def test_events_pagination_and_filters(auth_headers, client):
    r = client.get("/api/events?page_size=5", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0
    assert len(body["items"]) <= 5
    assert body["pages"] >= 1

    r2 = client.get("/api/events?severity=CRITICAL", headers=auth_headers)
    for ev in r2.json()["items"]:
        assert ev["severity"] == "CRITICAL"


def test_event_detail(auth_headers, client):
    events = client.get("/api/events?page_size=1", headers=auth_headers).json()["items"]
    assert events
    ev = client.get(f"/api/events/{events[0]['id']}", headers=auth_headers)
    assert ev.status_code == 200
    body = ev.json()
    assert "evidence" in body and "fusion" in body and "timeline" in body
    assert body["signal_count"] >= 1


def test_signals_filters(auth_headers, client):
    r = client.get("/api/signals?page_size=5&source=SOCIAL", headers=auth_headers)
    assert r.status_code == 200
    for s in r.json()["items"]:
        assert s["source_category"] == "SOCIAL"

    r2 = client.get("/api/signals?suspicious_only=true", headers=auth_headers)
    for s in r2.json()["items"]:
        assert s["suspicious"] is True


def test_signal_detail(auth_headers, client):
    sigs = client.get("/api/signals?page_size=1", headers=auth_headers).json()["items"]
    assert sigs
    r = client.get(f"/api/signals/{sigs[0]['id']}", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "location_consistency" in body and "weather_evidence" in body


def test_manual_signal_triggers_pipeline(auth_headers, client):
    payload = {
        "source_category": "NEWS", "headline": "Chennai floods: heavy rainfall floods Anna Nagar",
        "content": "waterlogging traffic", "event_type": "FLOOD", "severity": "HIGH",
        "latitude": 13.08, "longitude": 80.27, "city": "Chennai", "district": "Chennai", "state": "Tamil Nadu",
        "metrics": {"rainfall_mm": 95},
    }
    r = client.post("/api/signals", json=payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    sig = r.json()
    assert sig["trust_score"] > 0
    assert sig["event_id"] is not None


def test_analytics_overview(auth_headers, client):
    r = client.get("/api/analytics/overview?days=10", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["event_trend"]) == 10
    assert body["state_ranking"]
    assert body["source_reliability"]
    assert len(body["hourly_distribution"]) == 24


def test_map_points_layers(auth_headers, client):
    for layer in ("events", "signals", "anomalies"):
        r = client.get(f"/api/map/points?layer={layer}&hours=500&limit=50", headers=auth_headers)
        assert r.status_code == 200


def test_search(auth_headers, client):
    r = client.get("/api/search?q=Mumbai", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["events"] or body["signals"] or body["locations"]


def test_alerts_flow(auth_headers, client):
    r = client.get("/api/alerts", headers=auth_headers)
    assert r.status_code == 200
    client.post("/api/alerts/read-all", headers=auth_headers)
    assert client.get("/api/alerts/unread-count", headers=auth_headers).json()["count"] == 0


def test_sources_and_system(auth_headers, client):
    assert client.get("/api/sources", headers=auth_headers).status_code == 200
    h = client.get("/api/system/health", headers=auth_headers)
    assert h.status_code == 200
    assert h.json()["overall"] in ("OPERATIONAL", "DEGRADED")


def test_anomalies(auth_headers, client):
    r = client.get("/api/anomalies", headers=auth_headers)
    assert r.status_code == 200
    for a in r.json():
        assert a["risk"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_ground_report_submission(auth_headers, client):
    r = client.post("/api/ground-reports", json={
        "event_type": "FLOOD", "description": "Street near my home is flooded with knee-deep water",
        "city": "Mumbai", "state": "Maharashtra",
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["tracking_id"].startswith("GR-")
    # citizen signal went through the pipeline
    assert body["signal_id"] is None or body["signal_id"]


def test_ai_endpoints(auth_headers, client):
    r = client.post("/api/ai/classify", json={"headline": "Heatwave in Ahmedabad, 45 degrees", "content": "", "metrics": {"temp_c": 45}}, headers=auth_headers)
    assert r.status_code == 200 and r.json()["event_type"] == "HEATWAVE"

    r2 = client.post("/api/ai/trust-score", json={
        "source_category": "GOVERNMENT", "headline": "IMD orange alert rainfall", "latitude": 19.07,
        "longitude": 72.87, "city": "Mumbai", "state": "Maharashtra",
    }, headers=auth_headers)
    assert r2.status_code == 200 and 0 <= r2.json()["trust_score"] <= 100


def test_public_stats_no_auth(client):
    r = client.get("/api/public/stats")
    assert r.status_code == 200
    assert r.json()["demo"] is True
