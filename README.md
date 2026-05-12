# Oil Market Intelligence API

FastAPI service for oil-market data ingestion, feature engineering, regime detection, and signal generation.

It is API-first, with a lightweight built-in dashboard (`/dashboard`) backed by the same endpoints.

## What this project does

- Ingests market data from EIA (public WPSR PDF), CFTC COT (multiple routes), QuantHub, X, and News.
- Normalizes all sources into `raw_observations` with a shared schema.
- Builds standardized feature vectors (`oil_features`) from historical and week-over-week series.
- Detects the latest market regime and computes a weighted factor score.
- Produces directional signal outputs (`bullish` / `neutral` / `bearish`) with probabilities and confidence.
- Optionally pushes latest signal snapshots to Microsoft Teams webhook.

## Architecture overview

The default pipeline is:

1. `POST /ingest/*` endpoints write raw rows into `raw_observations`.
2. `POST /features/build` pivots raw rows into a feature matrix and writes standardized rows into `oil_features`.
3. `POST /signals/run` loads latest features, infers regime, computes factor contributions, and writes to `oil_signals`.
4. `GET /signals/latest` and `/regime/latest` expose the latest model outputs.

## Tech stack

- FastAPI + Uvicorn
- SQLAlchemy 2.0
- Pandas + NumPy
- Scikit-learn (regime clustering)
- Requests + BeautifulSoup + lxml + PyPDF2 (ingestion/parsing)
- APScheduler (optional in-process scheduler)
- Docker + Docker Compose

## Current repository structure

```text
oil_market_intel_fastapi/
|-- app/
|   |-- api/                  # FastAPI routers (ingestion, debug, health, signals)
|   |-- backtest/             # backtest module scaffolding
|   |-- core/                 # config and logging setup
|   |-- db/                   # SQLAlchemy models/session
|   |-- features/             # feature builder
|   |-- ingestion/            # EIA/COT/QuantHub/News/X adapters
|   |-- jobs/                 # APScheduler bootstrap
|   |-- models/               # regime + factor + signal logic
|   |-- schemas/              # schema placeholders/common
|   |-- scripts/              # utility scripts
|   |-- services/             # repository + Teams webhook
|   |-- standardization/      # z-scores/momentum/probability transforms
|   |-- static/index.html     # simple dashboard
|   `-- main.py               # FastAPI app instance
|-- eia_weekly_output/
|   |-- raw/                  # downloaded WPSR PDFs
|   `-- processed/            # parsed EIA outputs (json/csv/xlsx)
|-- logs/                     # app and EIA debug logs
|-- sql/init.sql              # TimescaleDB bootstrap schema
|-- tests/test_transforms.py
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
`-- main.py                   # local runner
```

## Data model

Core tables:

- `raw_observations`: canonical source events (`timestamp`, `source`, `series_name`, `raw_value`, `metadata`).
- `oil_features`: engineered standardized features (`standardized_value`, `confidence`, `directional_impact`, etc).
- `oil_prices`: reserved for price series.
- `oil_signals`: model outputs (`probability_up`, `expected_return`, `signal`, `regime`, contributions).

Uniqueness constraints:

- `raw_observations`: unique on (`timestamp`, `source`, `series_name`).
- `oil_features`: primary key (`timestamp`, `feature_name`).
- `oil_signals`: primary key (`timestamp`, `instrument`, `horizon`).

## Configuration

Copy env template:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Important env vars:

- `DATABASE_URL` (default SQLite: `sqlite:///./oilintel.db`)
- `QUANTHUB_BASE_URL`
- `QUANTHUB_USERNAME`, `QUANTHUB_PASSWORD` (or `QUANTHUB_ACCESS_TOKEN`)
- `X_BEARER_TOKEN`
- `NEWS_API_KEY`
- `TEAMS_WEBHOOK_URL`
- `CFTC_PETROLEUM_FUTURES_URL`, `CFTC_PETROLEUM_OPTIONS_URL`, `CFTC_DEFAULT_MODE`

Note: EIA ingestion currently uses the public WPSR overview PDF endpoint, so `EIA_API_KEY` is optional in current code.

## Run locally

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Alternative local runner:

```bash
python main.py
```

## Run with Docker

```bash
docker compose up --build
```

Compose services:

- `db`: `timescale/timescaledb:latest-pg16` with `sql/init.sql`
- `api`: FastAPI app (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`)

## API docs and web entry points

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`
- Dashboard: `http://localhost:8000/dashboard`

## Endpoint reference

### Health

- `GET /health`

### Ingestion

- `POST /ingest/eia`
- `POST /eia/pdf/run`
- `GET /eia/history`
- `POST /ingest/cot`
- `POST /ingest/cot-scrape`
- `POST /ingest/cot/petroleum`
- `GET /cot/petroleum/contracts`
- `GET /cot/petroleum/history`
- `GET /cot/petroleum/signals`
- `POST /ingest/news`
- `POST /ingest/x`
- `POST /ingest/demo` (synthetic test data)
- `POST /ingest/quanthub`
- `POST /ingest/quanthub/ohlc-v2`
- `POST /ingest/quanthub/tas-v2`
- `POST /ingest/quanthub/fairvalue-v2`
- `POST /ingest/quanthub/vap-v2`
- `GET /quanthub/history`

### Feature and signal pipeline

- `POST /features/build`
- `GET /features/latest`
- `GET /features/matrix`
- `POST /signals/run`
- `GET /signals/latest`
- `GET /regime/latest`
- `POST /alerts/teams/latest`

### Debug and diagnostics

- `GET /debug/config`
- `GET /debug/db`
- `GET /debug/routes`
- `GET /debug/router-routes`
- `GET /debug/app-routes`
- `GET /debug/eia/pdf`
- `GET /debug/logs/app`
- `GET /debug/logs/eia`
- `GET /debug/log-file`
- `GET /debug/cot/petroleum/parse`
- `GET /debug/quanthub/auth`
- `GET /debug/quanthub/ohlc-v2`
- `GET /debug/quanthub/raw`
- `GET /debug/quanthub/counts`
- `GET /debug/qh-routes`

## Typical end-to-end workflow

1. Verify environment and DB:
   - `GET /health`
   - `GET /debug/db`
2. Ingest one or more sources (for example):
   - `POST /ingest/eia`
   - `POST /ingest/cot/petroleum?mode=futures`
   - `POST /ingest/quanthub/ohlc-v2?instruments=CLN26&interval=1D&count=50`
3. Build features:
   - `POST /features/build`
4. Generate signal:
   - `POST /signals/run?instrument=WTI&horizon=5d`
5. Read outputs:
   - `GET /signals/latest?instrument=WTI&horizon=5d`
   - `GET /regime/latest`

## Feature engineering and model notes

- Feature builder handles both week-over-week EIA metrics and historical fallback transforms.
- COT petroleum metrics are dynamically transformed into z-score features by suffix pattern.
- Regime detection uses clustering plus deterministic overlay rules for interpretability.
- Score model uses explicit feature weights, optional regime multipliers, and bounded probability conversion.
- Confidence blends directional agreement and contribution magnitude.

## Logging and generated artifacts

- App logs: `logs/oilintel_app.log`
- EIA parser logs: `logs/eia_pdf_debug.log`
- EIA raw PDFs: `eia_weekly_output/raw/`
- EIA parsed outputs: `eia_weekly_output/processed/`

## Testing

Run tests:

```bash
pytest -q
```

Current test suite includes a baseline transform test in `tests/test_transforms.py`.

## Known implementation details

- SQLite is the default local DB and uses Python-side upsert logic in `app/services/repository.py`.
- Datetimes are normalized to UTC-naive before persistence for SQLite compatibility.
- `app/db/session.py` creates tables automatically on startup via SQLAlchemy metadata.
- TimescaleDB schema is available through `sql/init.sql` for containerized Postgres deployments.

## Security and operations guidance

- Do not commit `.env`, DB files, or logs.
- Rotate QuantHub/X/News credentials if exposed.
- Use external scheduling (cron, orchestrator, or n8n) for production jobs; in-process scheduler is optional.
- Treat `POST /ingest/demo` as non-production only.

## License

No license file is currently present in this repository. Add one if distribution terms are required.
