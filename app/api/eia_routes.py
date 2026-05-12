import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.models import RawObservation
from app.ingestion.eia import fetch_all_eia, run_eia_pdf_report
from app.services.repository import upsert_raw


logger = logging.getLogger(__name__)

router = APIRouter(tags=["EIA"])


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


@router.post("/ingest/eia")
def ingest_eia(
    start: str | None = None,
    end: str | None = None,
    db: Session = Depends(get_db),
):
    logger.info("POST /ingest/eia started")
    logger.info(f"EIA ingest params: start={start}, end={end}")

    try:
        df = fetch_all_eia(start=start, end=end)

        logger.info(f"EIA fetch_all_eia returned shape={df.shape}")

        if df.empty:
            logger.warning("EIA ingestion returned empty dataframe")

            return {
                "source": "EIA_PDF",
                "records": 0,
                "status": "no_data",
                "message": "EIA PDF parsed, but no rows were extracted.",
            }

        logger.debug(f"EIA dataframe columns: {list(df.columns)}")
        logger.debug(f"EIA dataframe head: {df.head(10).to_dict('records')}")

        count = upsert_raw(db, df.to_dict("records"))

        logger.info(f"EIA rows written to raw_observations: {count}")

        return {
            "source": "EIA_PDF",
            "records": count,
            "status": "success",
            "columns": list(df.columns),
            "sample": df.head(5).to_dict("records"),
        }

    except SQLAlchemyError as e:
        logger.exception("Database error during EIA ingestion")
        raise db_error_response(e)

    except Exception as e:
        logger.exception("EIA ingestion failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "eia_ingestion_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
                "debug_hint": "Open /debug/eia/pdf to inspect PDF parse status and /debug/logs/eia to inspect logs.",
            },
        )


@router.post("/eia/pdf/run")
def run_eia_pdf_report_endpoint():
    logger.info("POST /eia/pdf/run started")

    try:
        result = run_eia_pdf_report(save_files=True)

        logger.info("EIA PDF report parsed successfully")
        logger.info(f"EIA PDF summary: {result.get('summary')}")
        logger.info(f"EIA PDF files: {result.get('files')}")
        logger.debug(f"EIA PDF latest rows: {result.get('latest')}")

        return {
            "status": "success",
            "message": "EIA WPSR PDF parsed successfully.",
            "summary": result["summary"],
            "latest": result["latest"],
            "files": result["files"],
        }

    except Exception as e:
        logger.exception("EIA PDF report failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "eia_pdf_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
                "debug_hint": "Open /debug/eia/pdf and /debug/logs/eia.",
            },
        )


@router.get("/eia/history")
def get_eia_history(
    metric: str = "refinery_utilization",
    limit: int = 260,
    db: Session = Depends(get_db),
):
    """
    Returns weekly EIA history stored in SQLite.

    This is used for dashboard charts.
    Data is append/update by week and is not deleted.
    """

    try:
        rows = db.execute(
            select(RawObservation)
            .where(
                RawObservation.series_name == metric,
                RawObservation.source == "EIA_PDF",
            )
            .order_by(RawObservation.timestamp.asc())
        ).scalars().all()

        output = []

        for row in rows[-limit:]:
            output.append(
                {
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "metric": row.series_name,
                    "value": row.raw_value,
                    "metadata": row.metadata_json or {},
                }
            )

        return {
            "status": "success",
            "metric": metric,
            "count": len(output),
            "rows": output,
        }

    except Exception as e:
        logger.exception("EIA history endpoint failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "eia_history_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )
