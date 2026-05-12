import logging
import math
import random
import traceback
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.ingestion.news import fetch_news
from app.ingestion.x_api import fetch_x_oil_events
from app.services.repository import upsert_raw


logger = logging.getLogger(__name__)

router = APIRouter(tags=["News"])


def db_error_response(e: Exception):
    message = str(e)

    if "Connection refused" in message or "could not connect" in message:
        return HTTPException(
            status_code=503,
            detail={
                "status": "database_disconnected",
                "message": "PostgreSQL/TimescaleDB is not running or not reachable on localhost:5432.",
                "fix": "Start database using: docker compose up db",
                "database_url": settings.DATABASE_URL,
                "raw_error": message,
            },
        )

    return HTTPException(
        status_code=500,
        detail={
            "status": "database_error",
            "message": "Database operation failed.",
            "database_url": settings.DATABASE_URL,
            "raw_error": message,
        },
    )


@router.post("/ingest/x")
def ingest_x(
    max_results: int = 50,
    db: Session = Depends(get_db),
):
    try:
        df = fetch_x_oil_events(max_results=max_results)

        if df.empty:
            return {
                "source": "X",
                "records": 0,
                "status": "no_data",
                "message": "X returned no matching oil posts.",
            }

        count = upsert_raw(db, df.to_dict("records"))

        return {
            "source": "X",
            "records": count,
            "status": "success",
            "columns": list(df.columns),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "missing_or_invalid_config",
                "source": "X",
                "message": str(e),
                "fix": "Put X_BEARER_TOKEN in root .env and restart API.",
            },
        )

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "x_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/ingest/news")
def ingest_news(db: Session = Depends(get_db)):
    try:
        df = fetch_news()

        if df.empty:
            return {
                "source": "NEWS",
                "records": 0,
                "status": "no_data",
                "message": "News returned 0 rows. Check NEWS_API_KEY or vendor limits.",
            }

        count = upsert_raw(db, df.to_dict("records"))

        return {
            "source": "NEWS",
            "records": count,
            "status": "success",
            "columns": list(df.columns),
        }

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "news_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/ingest/demo")
def ingest_demo(db: Session = Depends(get_db)):
    try:
        now = datetime.now(timezone.utc).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        records = []

        for i in range(220):
            ts = now - timedelta(days=7 * (219 - i))

            crude = 430000 + 12000 * math.sin(i / 9) + random.uniform(-3500, 3500)
            cushing = 32000 + 5000 * math.sin(i / 13) + random.uniform(-1000, 1000)
            util = 87 + 5 * math.sin(i / 15) + random.uniform(-1, 1)
            imports = 6200 + 600 * math.sin(i / 8) + random.uniform(-250, 250)
            exports = 4100 + 700 * math.sin(i / 10) + random.uniform(-300, 300)
            cot = 220000 + 90000 * math.sin(i / 20) + random.uniform(-15000, 15000)
            x_geo = random.choice([0, 0, 0.4, -0.2, 0.8])
            quant_event = random.choice([0, 0.2, -0.3, 0.5])

            rows = [
                ("EIA", "us_crude_stocks_ex_spr", crude),
                ("EIA", "cushing_crude_stocks", cushing),
                ("EIA", "refinery_utilization", util),
                ("EIA", "crude_imports", imports),
                ("EIA", "crude_exports", exports),
                ("CFTC_COT_SCRAPE", "managed_money_net_crude", cot),
                ("X", "x_geopolitical_supply_risk", x_geo),
                ("QUANTHUB", "quanthub_oil_event", quant_event),
            ]

            for source, series_name, value in rows:
                records.append(
                    {
                        "timestamp": ts,
                        "source": source,
                        "series_name": series_name,
                        "raw_value": float(value),
                        "metadata": {
                            "demo": True,
                            "warning": "Synthetic dashboard test data only",
                        },
                    }
                )

        count = upsert_raw(db, records)

        return {
            "source": "DEMO_SYNTHETIC",
            "records": count,
            "status": "success",
            "warning": "Synthetic data only. Do not use for trading/backtesting.",
        }

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "demo_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )
