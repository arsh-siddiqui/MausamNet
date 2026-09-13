"""AI engine tests: classifier, trust, duplicates, clustering, anomalies, fusion."""
from __future__ import annotations

import datetime as dt

from app.ai.classifier import DemoEventClassifier
from app.ai.clustering import DemoEventClusterer
from app.ai.duplicate import SpatialTemporalDuplicateDetector, average_phash, hamming_similarity, text_similarity
from app.ai.fusion import evidence_matrix, fuse_event_confidence, fusion_components
from app.ai.trust import DemoTrustEngine


def test_classifier_rainfall():
    r = DemoEventClassifier().classify("IMD red alert heavy rainfall in Mumbai", "waterlogging across the city", {"rainfall_mm": 120})
    assert r["event_type"] in ("RAINFALL", "FLOOD")
    assert r["severity"] in ("HIGH", "CRITICAL")
    assert r["confidence"] > 0.5


def test_classifier_heatwave():
    r = DemoEventClassifier().classify("Severe heatwave grips Jaipur", "temperatures soar", {"temp_c": 45})
    assert r["event_type"] == "HEATWAVE"


def test_classifier_fog():
    r = DemoEventClassifier().classify("Dense fog reduces visibility in Delhi", "flights delayed", {"visibility_km": 0.05})
    assert r["event_type"] == "FOG"
    assert r["severity"] in ("HIGH", "CRITICAL")


def test_trust_high_for_gov():
    r = DemoTrustEngine().score({
        "source_category": "GOVERNMENT", "headline": "IMD red alert: 120mm rainfall", "content": "",
        "media_url": None, "weather_evidence": {"score": 0.9}, "location_component": 0.95,
        "time_component": 0.95, "cross_source_agreement": 0.8, "duplicate_score": 0.0,
    })
    assert r["trust_score"] >= 80
    assert r["confidence_band"] == "HIGH"
    assert len(r["explanation"]) >= 3


def test_trust_low_for_recycled_social():
    r = DemoTrustEngine().score({
        "source_category": "SOCIAL", "headline": "SHOCKING flood", "content": "",
        "media_url": "x.jpg", "weather_evidence": {"score": 0.2}, "location_component": 0.5,
        "time_component": 0.5, "cross_source_agreement": 0.1, "duplicate_score": 0.95,
    })
    assert r["trust_score"] < 55
    assert r["verdict"] in ("NEEDS VERIFICATION", "POTENTIALLY MISLEADING")


def test_duplicate_detection():
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    detector = SpatialTemporalDuplicateDetector()
    corpus = [{
        "id": "a", "headline": "Heavy rainfall floods Mumbai streets near Andheri",
        "content": "waterlogging traffic", "latitude": 19.07, "longitude": 72.87,
        "occurred_at": now, "media_phash": "",
    }]
    result = detector.check({
        "id": "b", "headline": "Heavy rainfall floods Mumbai streets near Andheri",
        "content": "waterlogging traffic", "latitude": 19.08, "longitude": 72.88,
        "occurred_at": now, "media_phash": "",
    }, corpus)
    assert result["is_duplicate"] is True
    assert result["score"] > 0.7


def test_duplicate_distinct_events():
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    detector = SpatialTemporalDuplicateDetector()
    corpus = [{
        "id": "a", "headline": "Heatwave alert in Jaipur", "content": "temperature 45",
        "latitude": 26.9, "longitude": 75.78, "occurred_at": now, "media_phash": "",
    }]
    result = detector.check({
        "id": "b", "headline": "Dense fog in Srinagar", "content": "visibility 50m",
        "latitude": 34.08, "longitude": 74.79, "occurred_at": now, "media_phash": "",
    }, corpus)
    assert result["is_duplicate"] is False


def test_phash_similarity():
    h = average_phash(b"fake-bytes-not-an-image")
    assert len(h) == 16
    assert hamming_similarity(h, h) == 1.0


def test_text_similarity():
    assert text_similarity("heavy rain floods mumbai roads", "heavy rain floods mumbai roads") == 1.0


def test_clustering_groups_nearby_signals():
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    signals = []
    for i in range(5):
        signals.append({"id": f"m{i}", "event_type": "FLOOD", "latitude": 19.07 + i * 0.01, "longitude": 72.87, "occurred_at": now, "city": "Mumbai"})
    for i in range(5):
        signals.append({"id": f"c{i}", "event_type": "FLOOD", "latitude": 13.08 + i * 0.01, "longitude": 80.27, "occurred_at": now, "city": "Chennai"})
    clusters = DemoEventClusterer(radius_km=100, time_window_hours=6, min_signals=2).cluster(signals)
    assert len(clusters) == 2
    city_sets = [{m["city"] for m in c} for c in clusters]
    assert {"Mumbai"} in city_sets and {"Chennai"} in city_sets


def test_fusion_and_confidence():
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    signals = [
        {"source_category": "GOVERNMENT", "latitude": 19.07, "longitude": 72.87, "occurred_at": now, "trust_score": 85, "metrics": {"rainfall_mm": 90}, "media_url": None, "suspicious": False},
        {"source_category": "WEATHER_API", "latitude": 19.08, "longitude": 72.88, "occurred_at": now, "trust_score": 80, "metrics": {"rainfall_mm": 88}, "media_url": None, "suspicious": False},
        {"source_category": "NEWS", "latitude": 19.06, "longitude": 72.86, "occurred_at": now, "trust_score": 75, "metrics": {}, "media_url": None, "suspicious": False},
        {"source_category": "SOCIAL", "latitude": 19.05, "longitude": 72.85, "occurred_at": now, "trust_score": 70, "metrics": {}, "media_url": "x.jpg", "suspicious": False},
        {"source_category": "CITIZEN", "latitude": 19.04, "longitude": 72.84, "occurred_at": now, "trust_score": 65, "metrics": {}, "media_url": None, "suspicious": False},
    ]
    comps = fusion_components(signals, latitude=19.06, longitude=72.86)
    conf = fuse_event_confidence(comps)
    assert conf > 70
    matrix = evidence_matrix(signals)
    assert matrix["GOVERNMENT"]["strength"] in ("STRONG", "SUPPORTING")
    assert matrix["CITIZEN"]["count"] == 1
