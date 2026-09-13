# 🌦️ MausamNet

## National Weather-Event Intelligence and Verification Platform

**SIH26069 — National Weather Big Data Analytics**

MausamNet is an AI-powered national weather-event intelligence and verification platform. Instead of acting as a simple weather-monitoring dashboard, MausamNet is designed to ingest fragmented information from multiple heterogeneous sources, combine those signals, detect emerging weather events, identify anomalies and potentially recycled media, and send critical events to a **human verification workflow**.

> **SIH Prototype Notice.** This build runs locally with SQLite and integrates **real APIs** (Open-Meteo for live weather data and NewsAPI for live local news signals). Confidence scores are analytical indicators and do not replace official meteorological warnings or authorized disaster-management decisions.

---

## 1. What is MausamNet?

Traditional weather systems are excellent at producing observations and forecasts. However, during an actual disaster, information comes from many places with varying formats, reliability, and geographic coverage:
`Government Alerts → Meteorological Observations → Weather APIs → News Reports → Social Media → Citizen Reports → Public Datasets`

MausamNet solves the problem of disparate data by performing **intelligence + correlation + verification**:
1. **Signal Fusion**: Extracts structured intelligence from unstructured pings.
2. **Event Clustering**: Correlates multiple independent reports into a single, real-world event.
3. **Anomaly Detection**: Flags observations that deviate significantly from historical baselines.
4. **Media Forensics**: Prevents misinformation by detecting potentially recycled disaster imagery.
5. **Human-in-the-Loop**: Leaves the final disaster declaration to authorized personnel via an audit-trailed Verification Center.

---

## 2. The 60-Second Explanation for Judges

> **"MausamNet is a national weather-event intelligence and verification platform. Instead of relying on a single weather source, it ingests heterogeneous signals from meteorological and government sources, APIs, news, social sources, public datasets and citizen ground reports.**
>
> **The system normalizes and classifies these signals, detects anomalies, checks potentially recycled media, and correlates signals spatially and temporally. Multiple related signals are then fused into a single event with AI confidence, trust and severity indicators.**
>
> **For example, if Mumbai experiences extreme rainfall, MausamNet can combine an IMD alert, abnormal rainfall observations, citizen flood reports, news reports and anomaly detection into one Mumbai Flood event. If someone submits an old flood photograph, the Media Forensics module can detect a previous similar appearance and flag it for provenance investigation.**
>
> **The important part is that AI does not make the final disaster decision. Analysts investigate the evidence, and authorized verifiers can approve or reject the event. Every important action can be audited. So MausamNet converts fragmented weather information into explainable, evidence-backed and human-verified intelligence."**

---

## 3. Architecture

```text
                   MAUSAMNET
                       │
       ┌───────────────┼────────────────┐
       │               │                │
   DATA SOURCES    MEDIA SOURCES    GROUND DATA
       │               │                │
       └───────────────┼────────────────┘
                       ↓
                 INGESTION LAYER
                       ↓
               AI CLASSIFICATION
                       ↓
          ┌────────────┴────────────┐
          ↓                         ↓
   ANOMALY ENGINE             MEDIA FORENSICS
          │                         │
          └────────────┬────────────┘
                       ↓
             SPATIO-TEMPORAL FUSION
                       ↓
              EVENT CLUSTERING
                       ↓
          CONFIDENCE + TRUST SCORE
                       ↓
            ┌──────────┴──────────┐
            ↓                     ↓
         ANALYST                VERIFIER
      (Investigate)         (Final Decision)
            └──────────┬──────────┘
                       ↓
                  AUDIT TRAIL
```

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS, TanStack Query, Leaflet, Recharts, Framer Motion.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite (WAL for real-time reads).
- **AI/Forensics:** Pluggable interfaces (`DemoEventClassifier`, `MediaAnalyzer` using aHash, `StatisticalAnomalyDetector`).

---

## 4. Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt

# initialize + seed the demo database (deterministic)
python ../scripts/seed_database.py

# run the API (defaults documented below)
python -m uvicorn app.main:app --port 8600
```
*The database auto-creates at `backend/database/mausamnet.db`.*

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local     # points at your backend url
npm run dev                          # http://localhost:3000
```

### Demo Logins
Credentials are automatically served by the `/api/auth/demo-accounts` endpoint. You can click **Launch Analyst / Verifier / Admin Demo** directly on the `/login` screen without typing passwords.

---

## 6. Environment Variables

See the `.env.example` files in both `/backend` and `/frontend` for all supported settings.

## 7. Production Deployment

MausamNet is designed to deploy cleanly to **Vercel** (Frontend) and **Render** (Backend).

Please see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for step-by-step instructions.

A `render.yaml` file is provided for automatic backend blueprint provisioning.

---

## 8. Module Map

| Area | What it does |
|---|---|
| **Dashboard** | Gives the national command-center overview |
| **Live Map** | Shows where important weather intelligence/events are occurring |
| **Events** | Converts many signals into meaningful real-world event clusters |
| **Signal Explorer** | Lets analysts inspect every raw incoming signal |
| **Media Forensics** | Detects potentially recycled/similar disaster imagery and checks provenance |
| **Anomaly Center** | Detects statistically unusual weather observations (Z-score) |
| **Analytics** | Provides national trends, source analysis, severity and state intelligence |
| **Verification Center**| Enables human investigation and final verification workflow (Analyst vs Verifier RBAC) |
| **Ground Evidence** | Collects citizen observations as supporting evidence |
