<![CDATA[# 🛢️ Oil Market Intelligence API

> **FastAPI-powered analytics engine for oil market data ingestion, feature engineering, regime detection, and directional signal generation.**

API-first architecture with a built-in interactive dashboard at `/dashboard`, backed by the same REST endpoints.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Data Model](#data-model)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
  - [Health & Debug](#health--debug)
  - [Ingestion](#ingestion)
  - [Feature & Signal Pipeline](#feature--signal-pipeline)
  - [Alerts](#alerts)
- [End-to-End Workflow](#end-to-end-workflow)
- [Model & Feature Engineering](#model--feature-engineering)
  - [Standardization Transforms](#standardization-transforms)
  - [Feature Builder](#feature-builder)
  - [Factor Model & Weights](#factor-model--weights)
  - [Regime Detection](#regime-detection)
  - [Signal Engine](#signal-engine)
  - [Time Decay](#time-decay)
- [Logging & Artifacts](#logging--artifacts)
- [Testing](#testing)
- [Utility Scripts](#utility-scripts)
- [Security & Operations](#security--operations)
- [License](#license)

---

## Overview

Oil Market Intelligence API ingests data from multiple sources — EIA weekly petroleum status reports, CFTC Commitments of Traders (COT), QuantHub market data, news feeds, and X (Twitter) — normalizes them into a unified schema, engineers standardized features, detects market regimes via clustering, and produces actionable directional signals (bullish / neutral / bearish) with probabilities, confidence scores, and factor-level attribution.

Signals can optionally be pushed to Microsoft Teams via webhook for real-time alerting.

---

## Key Features

| Capability | Description |
|---|---|
| **Multi-source ingestion** | EIA WPSR PDF parsing, CFTC COT scraping (futures & options), QuantHub OHLC/TAS/Fair Value/VAP, NewsAPI, X API |
| **Unified data layer** | All sources normalized into `raw_observations` with shared schema |
| **Feature engineering** | Automated z-score, momentum, inventory surprise, and week-over-week transforms |
| **Regime detection** | KMeans clustering + deterministic overlay rules for interpretable market regimes |
| **Signal generation** | Weighted factor model with regime-conditional multipliers and sigmoid probability conversion |
| **Interactive dashboard** | Single-page HTML dashboard served at `/dashboard` consuming API endpoints |
| **Teams alerting** | Push latest signal snapshots to Microsoft Teams webhook |
| **Dual database support** | SQLite for local development, TimescaleDB/PostgreSQL for production |
| **Docker-ready** | Dockerfile + Docker Compose with TimescaleDB included |
| **Backtest scaffolding** | Forward return calculation and performance metrics (Sharpe, drawdown, hit rate) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Data Sources                              │
│  EIA PDF  │  CFTC COT  │  QuantHub  │  NewsAPI  │  X (Twitter)  │
└─────┬─────┴─────┬──────┴─────┬──────┴─────┬─────┴──────┬────────┘
      │           │            │            │            │
      ▼           ▼            ▼            ▼            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Ingestion Adapters                             │
│  app/ingestion/eia.py │ cot_petroleum.py │ quanthub.py │ etc.    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              raw_observations (canonical store)                   │
│         timestamp │ source │ series_name │ raw_value │ metadata  │
└─────────────────────────────┬────────────────────────────────────┘
                              │  POST /features/build
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Feature Builder                                │
│  z-scores │ momentum │ inventory surprise │ WoW scaling           │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│            oil_features (standardized feature matrix)             │
│  timestamp │ feature_name │ standardized_value │ confidence       │
└─────────────────────────────┬────────────────────────────────────┘
                              │  POST /signals/run
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              Signal Engine                                        │
│  Regime Detection → Factor Model → Score → Probability → Signal  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              oil_signals (model outputs)                          │
│  probability_up │ expected_return │ signal │ regime │ contribs    │
└──────────────────────────────────────────────────────────────────┘
```

**Pipeline summary:**

1. `POST /ingest/*` — Write raw rows into `raw_observations`
2. `POST /features/build` — Pivot raw rows into a feature matrix; write standardized rows into `oil_features`
3. `POST /signals/run` — Load latest features, infer regime, compute factor contributions, write to `oil_signals`
4. `GET /signals/latest` / `GET /regime/latest` — Expose latest model outputs

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Web framework** | FastAPI + Uvicorn | 0.115.6 / 0.34.0 |
| **Validation** | Pydantic + pydantic-settings | 2.10.4 / 2.7.1 |
| **ORM** | SQLAlchemy | 2.0.36 |
| **Data processing** | Pandas + NumPy | 2.2.3 / 2.2.1 |
| **ML / Clustering** | scikit-learn | 1.6.0 |
| **Gradient boosting** | XGBoost | 2.1.3 |
| **Web scraping** | Requests + BeautifulSoup4 + lxml | 2.32.3 / 4.12.3 / 5.3.0 |
| **PDF parsing** | PyPDF2 | 3.0.1 |
| **Excel export** | openpyxl | 3.1.5 |
| **Scheduling** | APScheduler | 3.11.0 |
| **Environment** | python-dotenv | 1.0.1 |
| **Testing** | pytest | 8.3.4 |
| **Containerization** | Docker + Docker Compose | — |
| **Production DB** | TimescaleDB (PostgreSQL 16) | — |
| **Local DB** | SQLite | — |
| **Runtime** | Python | 3.11+ |

---

## Repository Structure

```text
oil_market_intel_fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI app factory, middleware, startup, static mount
│   ├── api/                           # API routers
│   │   ├── __init__.py                # Router aggregation
│   │   ├── routes.py                  # Feature build, signal run, regime, Teams alert
│   │   ├── eia_routes.py              # EIA ingestion + PDF parsing endpoints
│   │   ├── cot_routes.py              # CFTC COT petroleum endpoints
│   │   ├── qh_routes.py               # QuantHub OHLC/TAS/Fair Value/VAP endpoints
│   │   ├── news_routes.py             # NewsAPI + X ingestion endpoints
│   │   ├── health_routes.py           # Health check + DB diagnostics
│   │   └── debug_routes.py            # Debug/introspection endpoints
│   ├── core/
│   │   ├── config.py                  # Pydantic Settings (env vars)
│   │   └── logging_config.py          # Rotating file + console log setup
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy ORM models (4 tables)
│   │   └── session.py                 # Engine, session factory, table creation
│   ├── features/
│   │   └── builder.py                 # Feature engineering from raw observations
│   ├── ingestion/
│   │   ├── eia.py                     # EIA WPSR PDF download + parsing (~25KB)
│   │   ├── cot.py                     # Legacy COT ingestion
│   │   ├── cot_petroleum.py           # CFTC petroleum COT HTML scraper
│   │   ├── cot_scraper.py             # Generic COT scraping utilities
│   │   ├── quanthub.py                # QuantHub API client (auth + data)
│   │   ├── news.py                    # NewsAPI adapter
│   │   └── x_api.py                   # X (Twitter) API v2 adapter
│   ├── models/
│   │   ├── regime.py                  # KMeans regime detection + overlay rules
│   │   ├── factor_model.py            # Weighted factor scoring + regime multipliers
│   │   └── signal_engine.py           # Orchestrates regime → score → signal
│   ├── standardization/
│   │   ├── transforms.py              # Rolling z-score, momentum, bounded probability
│   │   └── decay.py                   # Exponential time decay by feature type
│   ├── schemas/
│   │   └── common.py                  # Pydantic request/response schemas
│   ├── services/
│   │   ├── repository.py              # SQLite-safe upsert logic + data loaders
│   │   └── teams.py                   # Microsoft Teams webhook integration
│   ├── jobs/
│   │   └── scheduler.py               # APScheduler bootstrap (optional)
│   ├── backtest/
│   │   └── backtester.py              # Forward returns + performance metrics
│   ├── scripts/
│   │   └── fix_sqlite_schema.py       # Migration: BigInteger → INTEGER PK fix
│   ├── static/
│   │   └── index.html                 # Interactive dashboard (single-page, ~79KB)
│   └── tests/                         # App-level tests (placeholder)
├── sql/
│   └── init.sql                       # TimescaleDB bootstrap (4 hypertables)
├── eia_weekly_output/
│   ├── raw/                           # Downloaded WPSR PDF files
│   └── processed/                     # Parsed EIA outputs (JSON/CSV/XLSX)
├── logs/                              # Runtime log files (auto-created)
├── tests/
│   └── test_transforms.py             # Transform unit tests
├── .env.example                       # Environment variable template
├── .gitignore
├── cache_delete.py                    # __pycache__ cleanup utility
├── Dockerfile                         # Python 3.11-slim container
├── docker-compose.yml                 # API + TimescaleDB services
├── main.py                            # Local development runner (uvicorn)
├── requirements.txt                   # Pinned Python dependencies
└── README.md                          # This file
```

---

## Data Model

### Core Tables

| Table | Purpose | Primary Key |
|---|---|---|
| `raw_observations` | Canonical source events from all adapters | `id` (auto-increment) + unique on (`timestamp`, `source`, `series_name`) |
| `oil_features` | Engineered standardized features | (`timestamp`, `feature_name`) |
| `oil_prices` | Price series (reserved) | (`timestamp`, `instrument`) |
| `oil_signals` | Model outputs with probabilities and attributions | (`timestamp`, `instrument`, `horizon`) |

### Schema Details

**`raw_observations`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment row ID |
| `timestamp` | DATETIME | Event timestamp (stored UTC-naive) |
| `source` | TEXT | Data source identifier (e.g., `EIA_PDF`, `CFTC_COT`, `QUANTHUB`) |
| `series_name` | TEXT | Metric name (e.g., `commercial_crude_stocks_wow_change`) |
| `raw_value` | FLOAT | Numeric observation value |
| `metadata` | JSON | Source-specific metadata |
| `created_at` | DATETIME | Row creation timestamp |

**`oil_features`**

| Column | Type | Description |
|---|---|---|
| `timestamp` | DATETIME | Feature timestamp |
| `feature_name` | TEXT | Standardized feature identifier (e.g., `eia_crude_inventory_surprise_z`) |
| `source` | TEXT | Originating data source |
| `raw_value` | FLOAT | Original value before standardization |
| `standardized_value` | FLOAT | Z-score or scaled value |
| `confidence` | FLOAT | Source reliability (0.0–1.0) |
| `decay` | FLOAT | Time decay factor (0.0–1.0) |
| `horizon` | TEXT | Forecast horizon (default: `5d`) |
| `directional_impact` | TEXT | `bullish_when_positive`, `bearish_when_positive`, or `mixed` |
| `metadata` | JSON | Additional context |

**`oil_signals`**

| Column | Type | Description |
|---|---|---|
| `timestamp` | DATETIME | Signal generation timestamp |
| `instrument` | TEXT | Instrument code (`WTI`, `BRENT`) |
| `horizon` | TEXT | Forecast horizon (`5d`, `1d`, `20d`) |
| `probability_up` | FLOAT | Probability of upward move |
| `probability_down` | FLOAT | Probability of downward move |
| `expected_return` | FLOAT | Expected directional return |
| `confidence` | FLOAT | Model confidence (0.0–1.0) |
| `signal` | TEXT | `bullish`, `neutral`, or `bearish` |
| `regime` | TEXT | Detected market regime |
| `feature_contributions` | JSON | Per-feature score contributions |
| `feature_zscores` | JSON | Per-feature z-score values |

---

## Configuration

### 1. Create your `.env` file

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 2. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_NAME` | No | `Oil Market Intelligence API` | Application display name |
| `ENV` | No | `dev` | Environment (`dev`, `staging`, `prod`) |
| `DATABASE_URL` | No | `sqlite:///./oilintel.db` | Database connection string |
| `EIA_API_KEY` | No | — | EIA API key (optional — PDF ingestion uses public endpoint) |
| `X_BEARER_TOKEN` | No | — | X (Twitter) API v2 bearer token |
| `QUANTHUB_BASE_URL` | No | `https://qh-api.corp.hertshtengroup.com` | QuantHub API base URL |
| `QUANTHUB_USERNAME` | No | — | QuantHub login username |
| `QUANTHUB_PASSWORD` | No | — | QuantHub login password |
| `QUANTHUB_ACCESS_TOKEN` | No | — | Pre-generated QuantHub access token |
| `QUANTHUB_REFRESH_TOKEN` | No | — | Pre-generated QuantHub refresh token |
| `NEWS_API_KEY` | No | — | NewsAPI.org API key |
| `TEAMS_WEBHOOK_URL` | No | — | Microsoft Teams incoming webhook URL |
| `WTI_SYMBOL` | No | `WTI` | WTI instrument symbol |
| `BRENT_SYMBOL` | No | `BRENT` | Brent instrument symbol |
| `CFTC_PETROLEUM_FUTURES_URL` | No | CFTC default | CFTC petroleum futures report URL |
| `CFTC_PETROLEUM_OPTIONS_URL` | No | CFTC default | CFTC petroleum options report URL |
| `CFTC_DEFAULT_MODE` | No | `futures` | Default COT mode (`futures` or `options`) |

> **Note:** EIA ingestion currently uses the public WPSR overview PDF endpoint, so `EIA_API_KEY` is optional.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for containerized deployment)

### Local Development

```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment template
cp .env.example .env    # or: Copy-Item .env.example .env

# 4. Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Alternative local runner with preconfigured reload exclusions:

```bash
python main.py
```

The app auto-creates SQLite tables on first startup.

### Docker Deployment

```bash
# Start API + TimescaleDB
docker compose up --build

# Stop services
docker compose down
```

**Compose services:**

| Service | Image | Port | Notes |
|---|---|---|---|
| `db` | `timescale/timescaledb:latest-pg16` | 5432 | Bootstrapped with `sql/init.sql` |
| `api` | Custom (Dockerfile) | 8000 | Hot-reload enabled |

> When using Docker, set `DATABASE_URL` in `.env` to point to the Postgres container (e.g., `postgresql://postgres:postgres@db:5432/oilintel`).

### Access Points

| URL | Description |
|---|---|
| `http://localhost:8000/` | Redirects to dashboard |
| `http://localhost:8000/dashboard` | Interactive dashboard |
| `http://localhost:8000/docs` | Swagger UI (OpenAPI) |
| `http://localhost:8000/redoc` | ReDoc API documentation |
| `http://localhost:8000/health` | Health check |

---

## API Reference

### Health & Debug

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check with DB connectivity status |
| `GET` | `/debug/config` | Current app configuration (redacted secrets) |
| `GET` | `/debug/db` | Database connection diagnostics |
| `GET` | `/debug/routes` | Registered router routes |
| `GET` | `/debug/router-routes` | Router-level route listing |
| `GET` | `/debug/app-routes` | All FastAPI app routes |
| `GET` | `/debug/eia/pdf` | EIA PDF parsing debug info |
| `GET` | `/debug/logs/app` | Tail of application log |
| `GET` | `/debug/logs/eia` | Tail of EIA parser log |
| `GET` | `/debug/log-file` | Raw log file content |
| `GET` | `/debug/cot/petroleum/parse` | COT petroleum parse debug |
| `GET` | `/debug/quanthub/auth` | QuantHub auth status |
| `GET` | `/debug/quanthub/ohlc-v2` | QuantHub OHLC debug |
| `GET` | `/debug/quanthub/raw` | QuantHub raw response |
| `GET` | `/debug/quanthub/counts` | QuantHub record counts |
| `GET` | `/debug/qh-routes` | QuantHub route listing |

### Ingestion

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest/eia` | Ingest EIA WPSR data |
| `POST` | `/eia/pdf/run` | Download + parse latest EIA WPSR PDF |
| `GET` | `/eia/history` | Retrieve EIA ingestion history |
| `POST` | `/ingest/cot` | Ingest CFTC COT data (legacy) |
| `POST` | `/ingest/cot-scrape` | Scrape CFTC COT from HTML |
| `POST` | `/ingest/cot/petroleum` | Ingest CFTC petroleum COT (`?mode=futures\|options`) |
| `GET` | `/cot/petroleum/contracts` | List available COT petroleum contracts |
| `GET` | `/cot/petroleum/history` | COT petroleum ingestion history |
| `GET` | `/cot/petroleum/signals` | COT-derived positioning signals |
| `POST` | `/ingest/news` | Ingest from NewsAPI |
| `POST` | `/ingest/x` | Ingest from X (Twitter) API |
| `POST` | `/ingest/demo` | Generate synthetic test data (non-production) |
| `POST` | `/ingest/quanthub` | Ingest QuantHub events |
| `POST` | `/ingest/quanthub/ohlc-v2` | QuantHub OHLC v2 ingestion |
| `POST` | `/ingest/quanthub/tas-v2` | QuantHub TAS v2 ingestion |
| `POST` | `/ingest/quanthub/fairvalue-v2` | QuantHub Fair Value v2 ingestion |
| `POST` | `/ingest/quanthub/vap-v2` | QuantHub VAP v2 ingestion |
| `GET` | `/quanthub/history` | QuantHub ingestion history |

### Feature & Signal Pipeline

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/features/build` | Build features from raw observations |
| `GET` | `/features/latest` | Latest 200 engineered features |
| `GET` | `/features/matrix` | Pivoted feature matrix (last 120 timestamps) |
| `POST` | `/signals/run` | Run signal engine (`?instrument=WTI&horizon=5d`) |
| `GET` | `/signals/latest` | Latest signal for instrument/horizon |
| `GET` | `/regime/latest` | Current market regime |

### Alerts

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/alerts/teams/latest` | Push latest signal to Teams webhook |

---

## End-to-End Workflow

```bash
# 1. Verify environment and database
curl http://localhost:8000/health
curl http://localhost:8000/debug/db

# 2. Ingest data from one or more sources
curl -X POST http://localhost:8000/ingest/eia
curl -X POST "http://localhost:8000/ingest/cot/petroleum?mode=futures"
curl -X POST "http://localhost:8000/ingest/quanthub/ohlc-v2?instruments=CLN26&interval=1D&count=50"

# 3. Build feature matrix
curl -X POST http://localhost:8000/features/build

# 4. Generate signal
curl -X POST "http://localhost:8000/signals/run?instrument=WTI&horizon=5d"

# 5. Read outputs
curl http://localhost:8000/signals/latest?instrument=WTI&horizon=5d
curl http://localhost:8000/regime/latest

# 6. (Optional) Push alert to Teams
curl -X POST "http://localhost:8000/alerts/teams/latest?instrument=WTI&horizon=5d"
```

---

## Model & Feature Engineering

### Standardization Transforms

Located in `app/standardization/transforms.py`:

| Function | Description |
|---|---|
| `rolling_zscore(series, window=52)` | Rolling z-score with configurable lookback (default 52 weeks) |
| `momentum_z(series, short=4, long=13)` | Short/long moving average crossover, z-scored |
| `inventory_surprise_z(series, window=52)` | Week-over-week change, z-scored |
| `bounded_probability(score)` | Sigmoid function mapping score → [0, 1] probability |

### Feature Builder

Located in `app/features/builder.py`:

- **EIA WoW change features**: Scales raw week-over-week changes into bounded standardized values using domain-specific denominators (e.g., crude stocks ÷ 5.0 MMbbl, production ÷ 300 kbpd)
- **Historical fallback**: When only level data is available (no WoW), applies `inventory_surprise_z` or `momentum_z` on the raw series
- **COT petroleum features**: Dynamically generates z-scores for managed money net %, dealer vs. spec, swap dealer positioning
- **News / X / QuantHub**: Rolling z-score (window=30) on event-based series

**Source confidence defaults:**

| Source | Confidence |
|---|---|
| EIA / EIA_PDF | 0.95 |
| CFTC_COT | 0.90 |
| CFTC_COT_SCRAPE | 0.88 |
| QUANTHUB | 0.75 |
| NEWS | 0.65 |
| X | 0.55 |

### Factor Model & Weights

Located in `app/models/factor_model.py`:

The score model uses explicit feature weights with regime-conditional multipliers:

**Base weight examples:**

| Feature | Weight | Interpretation |
|---|---|---|
| `eia_crude_inventory_surprise_z` | -0.25 | Inventory builds are bearish |
| `eia_export_momentum_z` | +0.15 | Rising exports are bullish |
| `news_geopolitical_supply_risk_z` | +0.20 | Geopolitical risk is bullish |
| `cot_managed_money_crowding_z` | -0.15 | Crowded positioning is contrarian bearish |

**Regime multipliers** amplify relevant features in detected regimes (e.g., inventory features get 1.3–1.6x boost during `inventory_mean_reversion`).

**Signal thresholds:**

| Probability Up | Signal |
|---|---|
| ≥ 0.55 | `bullish` |
| ≤ 0.45 | `bearish` |
| 0.45–0.55 | `neutral` |

**Confidence** is computed as 50% directional agreement + 50% contribution magnitude (bounded 0–1).

### Regime Detection

Located in `app/models/regime.py`:

1. **Clustering**: KMeans (2–4 clusters, auto-scaled) on regime features
2. **Deterministic overlay** (takes precedence):
   - Geopolitical supply risk z > 1.0 → `supply_shock_bullish`
   - Inventory surprise |z| > 1.2 → `inventory_mean_reversion`
   - Managed money crowding |z| > 1.5 → `positioning_crowded`
3. **Fallback**: Cluster label mapped to regime name, or `neutral`

**Named regimes:** `neutral`, `inventory_mean_reversion`, `supply_shock_bullish`, `positioning_crowded`, `macro_demand`

### Signal Engine

Located in `app/models/signal_engine.py`:

Orchestrates the full pipeline:
1. Sort and fill feature matrix
2. Detect regime from historical features
3. Compute weighted score with regime-adjusted weights
4. Convert score to probability via sigmoid
5. Derive signal label and expected return
6. Bundle with per-feature contributions and z-scores

### Time Decay

Located in `app/standardization/decay.py`:

Exponential decay with feature-type-specific half-lives:

| Feature Type | Half-Life (days) |
|---|---|
| News (`news_*`) | 5 |
| COT (`cot_*`) | 21 |
| Inventory | 10 |
| Momentum | 14 |
| Default | 10 |

---

## Logging & Artifacts

| Path | Description |
|---|---|
| `logs/oilintel_app.log` | Application log (rotating, 5MB × 5 backups) |
| `logs/eia_pdf_debug.log` | Dedicated EIA PDF parser log |
| `eia_weekly_output/raw/` | Downloaded WPSR PDF files |
| `eia_weekly_output/processed/` | Parsed EIA outputs (JSON, CSV, XLSX) |

Log format: `YYYY-MM-DD HH:MM:SS | LEVEL | logger | file:line | message`

---

## Testing

```bash
# Run all tests
pytest -q

# Run with verbose output
pytest -v
```

Current test suite: `tests/test_transforms.py` — validates rolling z-score transform behavior.

---

## Utility Scripts

| Script | Description | Usage |
|---|---|---|
| `cache_delete.py` | Recursively removes `__pycache__/` dirs and `.pyc` files | `python cache_delete.py` |
| `app/scripts/fix_sqlite_schema.py` | Migrates `raw_observations.id` from BigInteger to INTEGER PK | `python -m app.scripts.fix_sqlite_schema` |

---

## Security & Operations

- **Never commit** `.env`, database files (`*.db`), or log files
- **Rotate credentials** (QuantHub, X, NewsAPI) immediately if exposed
- **Production scheduling**: Use external orchestration (cron, n8n, Airflow) — in-process APScheduler is optional and meant for development
- **`POST /ingest/demo`** generates synthetic data — do not use in production
- **SQLite limitations**: Uses Python-side upsert logic; datetimes are normalized to UTC-naive before persistence
- **TimescaleDB**: Full schema with hypertables available via `sql/init.sql`

---

## License

No license file is currently present in this repository. Add one if distribution terms are required.
]]>
