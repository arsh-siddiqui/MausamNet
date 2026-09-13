# MongoDB Migration Guide

MausamNet's data layer is deliberately isolated so the prototype's SQLite
storage can be replaced with MongoDB **without touching services, AI engines,
API routes or the frontend**.

## Current vs future

```
CURRENT                                   FUTURE
───────────────────────────────────      ───────────────────────────────────
Services (pipeline, events, …)           Services (unchanged)
   ↓                                        ↓
Repository interfaces                    Repository interfaces (unchanged)
   ↓                                        ↓
SQLite*Repository implementations        Mongo*Repository implementations
   ↓                                        ↓
SQLAlchemy Session                       Motor/PyMongo client session
   ↓                                        ↓
SQLite (WAL)                             MongoDB
```

The only files that change during a migration:

1. New `backend/app/repositories/mongo_repo.py` implementing every interface in
   `backend/app/repositories/interfaces.py`.
2. `backend/app/repositories/registry.py` — swap the concrete classes.
3. New connection module (Motor client) behind the same `UnitOfWork`
   `commit()/rollback()` semantics.
4. `MONGODB_URI` from `.env` (already declared in `.env.example`).

## Table → collection mapping

| SQLite table (SQLAlchemy model) | MongoDB collection | Notes |
|---|---|---|
| `users` (`UserModel`) | `users` | email unique index; role field unchanged |
| `sources` (`SourceModel`) | `sources` | `config` JSON → embedded document |
| `weather_signals` (`WeatherSignalModel`) | `signals` | `event_id` → indexed ObjectId/link; `metrics`/`suspicious_reasons`/`explanation` JSON → embedded docs/arrays. Geo pair → `location: {type:"Point", coordinates:[lon,lat]}` for `$near` queries |
| `weather_events` (`WeatherEventModel`) | `events` | `fusion`, `evidence`, `timeline`, `metrics` JSON → embedded documents. Centroid stored as GeoJSON Point + `2dsphere` index; `open_event_near` becomes `$geoWithin/$centerSphere` |
| `evidence` (`EvidenceModel`) | `evidence` | or embed inside event doc (recommended: embed) |
| `event_graph_edges` (`EventGraphEdgeModel`) | `event_graph_edges` | or embed inside event doc |
| `weather_observations` (`WeatherObservationModel`) | `observations` | time-series collection + `location` GeoJSON |
| `verification_actions` (`VerificationActionModel`) | `verification_actions` | audit-preserving |
| `alerts` (`AlertModel`) | `alerts` | TTL index optional for auto-expiry |
| `audit_logs` (`AuditLogModel`) | `audit_logs` | append-only |
| `anomalies` (`AnomalyModel`) | `anomalies` | deviation/zscore fields unchanged |
| `media_analysis` (`MediaAnalysisModel`) | `media_analysis` | `phash` indexed for similarity scan (or swap to vector index later) |
| `simulation_state` (`SimulationStateModel`) | `simulation_state` | single document |
| `ground_reports` (`GroundReportModel`) | `ground_reports` | `tracking_id` unique |
| `app_settings` (`KeyValueModel`) | `app_settings` | key/value documents |

## Implementation sketch

```python
# app/repositories/mongo_repo.py (sketch)
class MongoEventRepository:
    def __init__(self, db: motor.MotorDatabase) -> None:
        self._col = db["events"]

    async def open_event_near(self, *, event_type, latitude, longitude, radius_km, since):
        docs = await self._col.find({
            "event_type": event_type,
            "status": {"$in": ["CANDIDATE", "ACTIVE"]},
            "latest_at": {"$gte": since},
            "location": {"$geoWithin": {"$centerSphere": [[longitude, latitude], radius_km / 6371.0088]}},
        }).to_list(50)
        return [EventOut.model_validate(_from_doc(d)) for d in docs]
```

Because `open_event_near` returns `EventOut` (the same Pydantic schema the
SQLite repo returns), `IngestionService`, the verification queue, the map API
and the dashboard are untouched.

## Migration checklist

1. `pip install motor` (or pymongo).
2. Write `mongo_repo.py` for all 14 repositories (schema models are shared).
3. Add `_to_doc/_from_doc` mappers per entity (JSON fields map 1:1).
4. Create indexes: `signals(event_id, occurred_at, source_category, state)`,
   `events(geo 2dsphere, status, latest_at)`, `alerts(created_at)`, etc.
5. Swap the registry wiring and `DATABASE_URL=MONGODB_URI=...` in env.
6. Run the existing pytest suite — services/API contracts must pass unchanged
   (only `conftest.py`'s fixture wiring changes).
