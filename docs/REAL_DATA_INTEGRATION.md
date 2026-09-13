# Real Data Integration Guide

Everything external in MausamNet is a **connector** behind the same protocol:

```python
class WeatherConnector(Protocol):
    id: str
    name: str
    category: str                       # GOVERNMENT | WEATHER_API | NEWS | SOCIAL | PUBLIC_DATASET | CITIZEN

    def connect(self) -> bool: ...                  # authenticate / open session
    def fetch(self, now, rng) -> list[dict]: ...    # pull raw payloads
    def normalize(self, raw: dict) -> dict: ...     # vendor schema → signal schema
    def health_check(self) -> dict: ...             # surfaced on /sources
```

Demo connectors today (`backend/app/connectors/demo_connectors.py`) implement
this protocol and are registered in `CONNECTOR_FACTORY`. Real connectors
implement the same protocol and replace/extend the factory entries — **no
changes anywhere else in the app**.

## Credential slots (all optional in `.env`)

| Variable | Connector | Plugs into |
|---|---|---|
| `IMD_API_URL` / `IMD_API_KEY` | Real Government connector | Replaces `DemoGovernmentConnector`; category GOVERNMENT |
| `WEATHER_API_URL` / `WEATHER_API_KEY` | Real Weather-API connector (OpenWeather, Tomorrow.io, MeteoAPI) | Replaces `DemoWeatherApiConnector` |
| `NEWS_API_URL` / `NEWS_API_KEY` | News connector (GDELT, NewsAPI) | Replaces `DemoNewsConnector` |
| `SOCIAL_API_URL` / `SOCIAL_API_KEY` | Social firehose adapter (X API, Reddit) | Replaces `DemoSocialConnector` |
| `SATELLITE_API_URL` / `SATELLITE_API_KEY` / `MOSDAC_SATELLITE_URL` | Satellite/MOSDAC ingestion | New PUBLIC_DATASET connector |
| `MONGODB_URI` | Future persistence | See `docs/MONGODB_MIGRATION.md` |
| `JWT_SECRET` | Security | **Required** before any real deployment |

## Activation rules (prototype guarantees preserved)

1. A connector is "LIVE" only when its key variables are non-empty — the UI
   shows **DEMO CONNECTOR** until then (`/sources` reflects `mode`).
2. `normalize()` must map vendor fields into the canonical signal dict:
   `headline, content, media_url, event_type, severity, metrics{rainfall_mm,
   wind_kph, temp_c, visibility_km}, city, district, state, latitude, longitude,
   occurred_at, source_id`. Never hard-code assumptions about vendor response
   shapes outside `normalize()`.
3. Every raw record still flows through the same pipeline: classify → dedup →
   trust → cluster → alert → SSE. TrustEngine's source-reliability priors stay
   category-based, so provenance weighting works identically for real feeds.
4. Sources page "Switch to LIVE" (admin) toggles the mode flag; the connector
   factory consults env + mode to choose the implementation.

## Suggested per-source notes

- **IMD**: use `imd-api` style endpoints or data.gov.in datasets; respect rate
  limits; map bulletins' colors (yellow/orange/red) to severity.
- **Weather APIs**: poll 3-5 models for cross-model agreement — the fusion
  engine already weights cross-source agreement, so multiple weather APIs
  strengthen confidence automatically.
- **News**: GDELT 2.0 doc API is keyless for prototyping; keyword filters on
  Indian states/districts; `normalize()` extracts location via the city gazetteer
  in `app/connectors/base.py::CITIES`.
- **Social**: start with keyword + bbox search APIs; mark everything
  `SOCIAL` (low prior) and let WeatherTrust + duplicate detection filter noise.
- **Satellite (MOSDAC)**: rainfall estimates (e.g., 3B42-like products) map to
  `metrics.rainfall_mm` with `source_category=PUBLIC_DATASET`.

## Media forensics upgrade path

`MediaAnalyzer` (aHash today) can be replaced by a CLIP/ViT embedding analyzer
with the same `analyze()` signature; add a vector index (FAISS/Mongo Atlas
Vector Search) behind `MediaRepository.find_similar` — the API route and UI are
unchanged.
