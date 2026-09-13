# MausamNet System Architecture

MausamNet is designed as a highly decoupled, multi-tier intelligence platform. It separates the raw data ingestion layer from the AI processing engine and the final human-in-the-loop verification workflow.

## High-Level Architecture Diagram

```mermaid
graph TD
    %% Define Styles
    classDef client fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef api fill:#1e1b4b,stroke:#a78bfa,stroke-width:2px,color:#f8fafc;
    classDef ai fill:#450a0a,stroke:#f87171,stroke-width:2px,color:#f8fafc;
    classDef db fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#f8fafc;
    classDef external fill:#172554,stroke:#60a5fa,stroke-width:2px,stroke-dasharray: 5 5,color:#f8fafc;

    %% External Data Sources
    subgraph External["External Intelligence Sources"]
        Gov[Government Alerts]:::external
        Met[Meteorological Data\nOpen-Meteo]:::external
        News[News Scrapers\nNewsAPI]:::external
        Social[Social Media Feeds]:::external
        Cit[Citizen Ground Reports]:::external
    end

    %% Frontend Tier
    subgraph Frontend["Frontend Tier (Next.js 14)"]
        UI[React 18 SPA]:::client
        Map[Leaflet GIS Engine]:::client
        State[Zustand & TanStack Query]:::client
        SSEClient[SSE Realtime Client]:::client
    end

    %% Backend API Tier
    subgraph Backend["Backend API Tier (FastAPI)"]
        Ingest[Ingestion Routers]:::api
        Auth[JWT Auth & RBAC]:::api
        SSEServer[Realtime SSE Broker]:::api
        Ops[Operational Endpoints]:::api
    end

    %% AI & Core Services
    subgraph Services["Intelligence Engine (Python Services)"]
        Norm[Data Normalizer]:::ai
        Detect[Anomaly Engine\nZ-Score]:::ai
        Media[Media Forensics\naHash Fingerprinting]:::ai
        Cluster[Spatio-Temporal\nEvent Clustering]:::ai
        Fusion[Confidence & Trust\nFusion Scoring]:::ai
    end

    %% Data Tier
    subgraph DataTier["Data Tier"]
        SQLite[(SQLite WAL\nPrimary DB)]:::db
        Mongo[(MongoDB\nMigration Target)]:::db
    end

    %% Workflows
    Gov --> Ingest
    Met --> Ingest
    News --> Ingest
    Social --> Ingest
    Cit --> Ingest

    Ingest --> Norm
    Norm --> Detect
    Norm --> Media
    Detect --> Cluster
    Media --> Cluster
    Cluster --> Fusion
    Fusion --> SQLite

    SQLite -.-> Mongo

    UI <--> Ops
    Map <--> Ops
    State <--> Ops
    
    Ops <--> SQLite
    
    SQLite --> SSEServer
    SSEServer -. "Real-time updates" .-> SSEClient
    SSEClient --> State
```

## Component Breakdown

### 1. External Data Sources
MausamNet utilizes connector interfaces to ingest heterogeneous weather intelligence. 
- **Active Real APIs**: Integrates with Open-Meteo for live meteorological data and NewsAPI for local event reporting.
- **Pluggable Connectors**: Designed so government APIs (e.g., IMD) or social scraping pipelines can be easily plugged into the standard `Signal` model.

### 2. Frontend Tier (Next.js 14)
- **Command Center UI**: A dark-mode, GIS-heavy React application built with Tailwind CSS.
- **Progressive Disclosure Map**: Built on Leaflet, it handles rendering thousands of markers, heatmaps, and dynamic risk zones via GeoJSON.
- **Real-Time State**: Uses TanStack Query for caching and an SSE (Server-Sent Events) listener to instantly reflect new emergencies without browser polling.

### 3. Backend API (FastAPI)
- **High-Performance Routers**: Asynchronous Pydantic-validated endpoints handling thousands of signals.
- **RBAC (Role-Based Access Control)**: Strict JWT enforcement separating `ANALYST` (investigation) from `VERIFIER` (approval).
- **SSE Broker**: Streams event state changes and alert notifications to active connected clients.

### 4. Intelligence Engine (The AI Layer)
This is where raw signals become actionable events.
- **Anomaly Engine**: Calculates Z-scores against local baselines to flag statistically unusual observations.
- **Media Forensics**: Uses perceptual hashing (aHash) to check uploaded disaster imagery against a historical corpus to detect recycled media.
- **Spatio-Temporal Clustering**: Groups related signals occurring near each other in space and time into a unified "Event".
- **Fusion Scoring**: Computes AI Confidence (analytical probability) and Trust Score (source reliability).

### 5. Data Tier
- **Current**: SQLite in WAL (Write-Ahead Logging) mode, fully capable of handling the prototype's high read/write concurrency.
- **Future-Ready**: Built using the Repository Pattern. The services don't know they are talking to SQLite. The codebase includes documentation (`MONGODB_MIGRATION.md`) detailing how to swap the repository implementation to MongoDB for horizontal scaling without changing a single line of business logic.
