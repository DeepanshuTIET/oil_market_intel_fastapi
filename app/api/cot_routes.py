import logging
import math
import traceback
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.models import RawObservation
from app.ingestion.cot import fetch_cot_crude
from app.ingestion.cot_scraper import fetch_cot_disaggregated_scrape
from app.ingestion.cot_petroleum import (
    parse_cot_petroleum,
    fetch_all_cot_petroleum,
    COT_SOURCE_NAME,
)
from app.services.repository import upsert_raw


logger = logging.getLogger(__name__)

router = APIRouter(tags=["COT"])


def _json_safe_value(v: Any) -> Any:
    """Coerce NaN/Inf and numpy scalars so JSON clients never see invalid floats."""
    if v is None:
        return None
    if isinstance(v, (float, np.floating)):
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def _sanitize_json_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _sanitize_json_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_json_obj(v) for v in obj]
    return _json_safe_value(obj)


def _rolling_z(series: pd.Series, window: int = 52, min_periods: int = 10) -> pd.Series:
    mean = series.rolling(window, min_periods=min_periods).mean()
    std = series.rolling(window, min_periods=min_periods).std()
    z = (series - mean) / std
    z = z.mask((std == 0) | std.isna())
    return z.replace([np.inf, -np.inf], np.nan)


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


@router.post("/ingest/cot")
def ingest_cot(
    limit: int = 1000,
    db: Session = Depends(get_db),
):
    try:
        df = fetch_cot_crude(limit=limit)

        if df.empty:
            return {
                "source": "CFTC_COT",
                "records": 0,
                "status": "no_data",
                "message": "COT API endpoint returned no rows.",
            }

        count = upsert_raw(db, df.to_dict("records"))

        return {
            "source": "CFTC_COT",
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
                "status": "cot_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/ingest/cot-scrape")
def ingest_cot_scrape(
    year: int | None = None,
    market_filter: str = "CRUDE OIL",
    db: Session = Depends(get_db),
):
    try:
        df = fetch_cot_disaggregated_scrape(
            year=year,
            market_filter=market_filter,
        )

        if df.empty:
            return {
                "source": "CFTC_COT_SCRAPE",
                "records": 0,
                "status": "no_data",
                "message": "COT scrape returned no crude rows.",
            }

        count = upsert_raw(db, df.to_dict("records"))

        return {
            "source": "CFTC_COT_SCRAPE",
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
                "status": "cot_scrape_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


# =============================================================================
# CFTC COT Petroleum Routes
# =============================================================================

@router.post("/ingest/cot/petroleum")
def ingest_cot_petroleum(
    mode: str = "futures",
    db: Session = Depends(get_db),
):
    logger.info(f"POST /ingest/cot/petroleum started mode={mode}")

    try:
        df = fetch_all_cot_petroleum(mode=mode)

        logger.info(f"CFTC COT raw observation dataframe shape={df.shape}")

        if df.empty:
            return {
                "status": "no_data",
                "source": COT_SOURCE_NAME,
                "records": 0,
                "mode": mode,
            }

        count = upsert_raw(
            db,
            df.to_dict("records"),
        )

        return {
            "status": "success",
            "source": COT_SOURCE_NAME,
            "mode": mode,
            "records": count,
            "columns": list(df.columns),
            "sample": df.head(10).to_dict("records"),
        }

    except Exception as e:
        logger.exception("CFTC COT Petroleum ingestion failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "cot_petroleum_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/debug/cot/petroleum/parse")
def debug_cot_petroleum_parse(
    mode: str = "futures",
):
    logger.info(f"GET /debug/cot/petroleum/parse mode={mode}")

    try:
        df = parse_cot_petroleum(mode=mode)

        return {
            "status": "success",
            "mode": mode,
            "contracts": len(df),
            "columns": list(df.columns),
            "sample": df.head(20).to_dict("records"),
        }

    except Exception as e:
        logger.exception("CFTC COT Petroleum parse debug failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "cot_petroleum_parse_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/cot/petroleum/contracts")
def list_cot_petroleum_contracts(
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(RawObservation)
        .where(RawObservation.source == COT_SOURCE_NAME)
        .order_by(RawObservation.series_name.asc())
    ).scalars().all()

    contracts = {}

    for row in rows:
        meta = row.metadata_json or {}
        contract = meta.get("contract", "unknown")

        contracts[contract] = contracts.get(contract, 0) + 1

    return {
        "status": "success",
        "contracts_count": len(contracts),
        "contracts": contracts,
    }


@router.get("/cot/petroleum/history")
def get_cot_petroleum_history(
    contract_contains: str = "WTI",
    mode: str | None = None,
    limit: int = 260,
    db: Session = Depends(get_db),
):
    """
    Dashboard-ready COT petroleum history.

    Filters by contract substring because CFTC contract names are verbose.
    Example:
        contract_contains=WTI
        contract_contains=BRENT
    """

    rows = db.execute(
        select(RawObservation)
        .where(RawObservation.source == COT_SOURCE_NAME)
        .order_by(RawObservation.timestamp.asc())
    ).scalars().all()

    records = []

    contract_contains_lower = contract_contains.lower().strip()

    for row in rows:
        meta = row.metadata_json or {}
        contract = str(meta.get("contract", ""))

        if contract_contains_lower not in contract.lower():
            continue

        if mode and str(meta.get("mode", "")).lower() != mode.lower():
            continue

        records.append(
            {
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "contract": contract,
                "metric": meta.get("metric"),
                "value": row.raw_value,
                "series_name": row.series_name,
                "metadata": meta,
            }
        )

    if not records:
        return {
            "status": "empty",
            "contract_contains": contract_contains,
            "count": 0,
            "rows": [],
            "wide": [],
        }

    df = pd.DataFrame(records)

    wide = (
        df.pivot_table(
            index=["timestamp", "contract"],
            columns="metric",
            values="value",
            aggfunc="last",
        )
        .reset_index()
        .sort_values("timestamp")
        .tail(limit)
    )

    return {
        "status": "success",
        "contract_contains": contract_contains,
        "count": len(wide),
        "latest": wide.to_dict("records")[-1] if len(wide) else {},
        "wide": wide.to_dict("records"),
    }


@router.get("/cot/petroleum/signals")
def get_cot_petroleum_signals(
    contract_contains: str = "WTI",
    db: Session = Depends(get_db),
):
    """
    Signal-friendly latest COT values.
    """

    history = get_cot_petroleum_history(
        contract_contains=contract_contains,
        limit=260,
        db=db,
    )

    if history["status"] != "success" or not history["wide"]:
        return history

    rows = history["wide"]
    df = pd.DataFrame(rows)

    if "mm_net" in df.columns:
        df["mm_net_z"] = _rolling_z(df["mm_net"])

    if "mm_net" in df.columns:
        df["mm_net_change_4w"] = df["mm_net"].diff(4)

    if "dealer_vs_spec" in df.columns:
        df["dealer_vs_spec_z"] = _rolling_z(df["dealer_vs_spec"])

    latest = _sanitize_json_obj(df.tail(1).to_dict("records")[0])
    rows = _sanitize_json_obj(df.tail(100).to_dict("records"))

    return {
        "status": "success",
        "contract_contains": contract_contains,
        "latest": latest,
        "rows": rows,
    }
