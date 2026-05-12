import logging
import traceback

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.db.models import RawObservation
from app.features.builder import build_features_from_raw
from app.services.repository import (
    upsert_raw,
    load_raw_df,
    upsert_features,
    load_feature_matrix,
    latest_features,
    upsert_signal,
    latest_signal,
)
from app.models.signal_engine import run_signal_engine
from app.services.teams import send_teams_alert
from app.core.config import settings


router = APIRouter()
logger = logging.getLogger(__name__)

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


@router.post("/features/build")
def build_features(db: Session = Depends(get_db)):
    logger.info("POST /features/build started")

    try:
        raw = load_raw_df(db)

        logger.info(f"Raw dataframe shape: {raw.shape}")

        if raw.empty:
            logger.warning("No raw data found for feature build")

            return {
                "status": "no_raw_data",
                "message": "No raw observations found. Run /ingest/eia first.",
                "features_written": 0,
            }

        logger.info(f"Raw columns: {list(raw.columns)}")
        logger.info(f"Raw series count: {raw['series_name'].nunique() if 'series_name' in raw else 0}")

        features = build_features_from_raw(raw)

        logger.info(f"Feature dataframe shape: {features.shape}")

        if features.empty:
            logger.warning("Feature builder returned empty dataframe")

            return {
                "status": "no_features_created",
                "message": "Raw data exists, but no engineered features were created.",
                "features_written": 0,
                "raw_rows": len(raw),
                "raw_series": sorted(raw["series_name"].dropna().unique().tolist())
                if "series_name" in raw
                else [],
            }

        logger.info(f"Feature columns: {list(features.columns)}")
        logger.info(f"Feature sample: {features.head(10).to_dict('records')}")

        count = upsert_features(
            db,
            features.to_dict("records"),
        )

        logger.info(f"Features written: {count}")

        return {
            "status": "success",
            "features_written": count,
            "feature_names": sorted(features["feature_name"].unique().tolist()),
            "sample": features.head(10).to_dict("records"),
        }

    except Exception as e:
        logger.exception("Feature build failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "feature_build_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )

@router.get("/features/latest")
def get_latest_features(db: Session = Depends(get_db)):
    try:
        return latest_features(db)

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "latest_features_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/features/matrix")
def get_feature_matrix(db: Session = Depends(get_db)):
    try:
        matrix = load_feature_matrix(db)

        if matrix.empty:
            return {
                "timestamps": [],
                "features": [],
                "rows": [],
                "status": "empty",
            }

        matrix = matrix.tail(120).fillna(0.0)

        return {
            "timestamps": [str(x) for x in matrix.index],
            "features": list(matrix.columns),
            "rows": matrix.reset_index(drop=True).to_dict("records"),
            "status": "success",
        }

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "feature_matrix_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/signals/run")
def run_signals(
    instrument: str = "WTI",
    horizon: str = "5d",
    db: Session = Depends(get_db),
):
    try:
        matrix = load_feature_matrix(db)

        if matrix.empty:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "no_features",
                    "message": "No features available.",
                    "fix": "Run /features/build first.",
                },
            )

        record = run_signal_engine(
            matrix,
            instrument=instrument,
            horizon=horizon,
        )

        upsert_signal(db, record)

        return {
            "status": "success",
            "signal": record,
        }

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "signal_generation_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/signals/latest")
def get_latest_signal(
    instrument: str = "WTI",
    horizon: str = "5d",
    db: Session = Depends(get_db),
):
    try:
        sig = latest_signal(
            db=db,
            instrument=instrument,
            horizon=horizon,
        )

        if sig is None:
            return {
                "status": "no_signal",
                "message": "No signal found yet.",
                "fix": "Run /features/build and then /signals/run.",
                "instrument": instrument,
                "horizon": horizon,
                "probability_up": None,
                "probability_down": None,
                "expected_return": None,
                "confidence": None,
                "signal": "not_available",
                "regime": None,
                "feature_contributions": {},
                "feature_zscores": {},
            }

        return {
            "status": "success",
            "timestamp": sig.timestamp.isoformat() if sig.timestamp else None,
            "instrument": sig.instrument,
            "horizon": sig.horizon,
            "probability_up": sig.probability_up,
            "probability_down": sig.probability_down,
            "expected_return": sig.expected_return,
            "confidence": sig.confidence,
            "signal": sig.signal,
            "regime": sig.regime,
            "feature_contributions": sig.feature_contributions,
            "feature_zscores": sig.feature_zscores,
        }

    except Exception as e:
        logger.exception("Latest signal failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "latest_signal_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/regime/latest")
def get_latest_regime(db: Session = Depends(get_db)):
    try:
        matrix = load_feature_matrix(db)

        if matrix.empty:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "no_features",
                    "message": "No features found.",
                    "fix": "Run /features/build first.",
                },
            )

        from app.models.regime import detect_latest_regime

        return {
            "timestamp": matrix.index[-1],
            "regime": detect_latest_regime(matrix),
            "status": "success",
        }

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "regime_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.post("/alerts/teams/latest")
def alert_latest_signal(
    instrument: str = "WTI",
    horizon: str = "5d",
    db: Session = Depends(get_db),
):
    try:
        sig = latest_signal(
            db=db,
            instrument=instrument,
            horizon=horizon,
        )

        if sig is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "no_signal",
                    "message": "No signal found.",
                    "fix": "Run /signals/run first.",
                },
            )

        payload = {
            "instrument": sig.instrument,
            "horizon": sig.horizon,
            "signal": sig.signal,
            "probability_up": sig.probability_up,
            "confidence": sig.confidence,
            "regime": sig.regime,
        }

        return send_teams_alert(payload)

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "teams_alert_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


from app.api.qh_routes import router as qh_router
from app.api.health_routes import router as health_router
from app.api.debug_routes import router as debug_router
from app.api.eia_routes import router as eia_router
from app.api.cot_routes import router as cot_router
from app.api.news_routes import router as news_router

router.include_router(health_router)
router.include_router(debug_router)
router.include_router(eia_router)
router.include_router(cot_router)
router.include_router(news_router)
router.include_router(qh_router)