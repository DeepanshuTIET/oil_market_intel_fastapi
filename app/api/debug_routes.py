import logging
import traceback
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.ingestion.eia import debug_eia_pdf_parse


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Debug"])


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


@router.get("/debug/config")
def debug_config():
    return {
        "app_name": settings.APP_NAME,
        "env": settings.ENV,
        "database_url": settings.DATABASE_URL,
        "sources": {
            "eia_pdf": {
                "configured": True,
                "source": "https://ir.eia.gov/wpsr/overview.pdf",
            },
            "x": {
                "configured": bool(
                    getattr(settings, "X_BEARER_TOKEN", None)
                    and settings.X_BEARER_TOKEN.strip()
                ),
            },
            "quanthub": {
                "base_url": getattr(settings, "QUANTHUB_BASE_URL", None),
                "username_configured": bool(
                    getattr(settings, "QUANTHUB_USERNAME", None)
                    and settings.QUANTHUB_USERNAME.strip()
                ),
                "password_configured": bool(
                    getattr(settings, "QUANTHUB_PASSWORD", None)
                    and settings.QUANTHUB_PASSWORD.strip()
                ),
                "access_token_configured": bool(
                    getattr(settings, "QUANTHUB_ACCESS_TOKEN", None)
                    and settings.QUANTHUB_ACCESS_TOKEN.strip()
                ),
                "refresh_token_configured": bool(
                    getattr(settings, "QUANTHUB_REFRESH_TOKEN", None)
                    and settings.QUANTHUB_REFRESH_TOKEN.strip()
                ),
                "available_endpoints": [
                    "tas",
                    "ohlc",
                    "fairvalue",
                    "gtc",
                    "premiums",
                    "ohlc_v2",
                ],
            },
            "cot_scrape": {
                "configured": True,
                "note": "COT scrape uses public CFTC historical report files.",
            },
        },
    }


@router.get("/debug/db")
def debug_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1 AS ok")).mappings().first()

        return {
            "status": "connected",
            "database_url": settings.DATABASE_URL,
            "result": dict(result),
        }

    except SQLAlchemyError as e:
        raise db_error_response(e)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "unknown_db_error",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/debug/router-routes")
def debug_router_routes():
    return {
        "status": "success",
        "routes": [
            {
                "path": route.path,
                "name": route.name,
                "methods": sorted(list(route.methods)) if route.methods else [],
            }
            for route in router.routes
        ],
    }


@router.get("/debug/logs/app")
def debug_app_logs(lines: int = 300):
    log_file = Path("logs/oilintel_app.log")

    if not log_file.exists():
        return {
            "status": "missing",
            "message": "App log file does not exist yet.",
            "path": str(log_file),
        }

    content = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    return {
        "status": "success",
        "path": str(log_file),
        "lines": lines,
        "content": content[-lines:],
    }


@router.get("/debug/logs/eia")
def debug_eia_logs(lines: int = 300):
    log_file = Path("logs/eia_pdf_debug.log")

    if not log_file.exists():
        return {
            "status": "missing",
            "message": "EIA log file does not exist yet.",
            "path": str(log_file),
        }

    content = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    return {
        "status": "success",
        "path": str(log_file),
        "lines": lines,
        "content": content[-lines:],
    }


@router.get("/debug/routes")
def debug_routes():
    """
    Shows all registered FastAPI routes.
    Useful when a route returns 404 unexpectedly.
    """

    return {
        "status": "success",
        "routes": [
            {
                "path": route.path,
                "name": route.name,
                "methods": sorted(list(route.methods)) if route.methods else [],
            }
            for route in router.routes
        ],
    }


@router.get("/debug/eia/pdf")
def debug_eia_pdf():
    logger.info("GET /debug/eia/pdf started")

    try:
        result = debug_eia_pdf_parse()

        logger.info("EIA PDF debug completed")
        logger.debug(result)

        return result

    except Exception as e:
        logger.exception("EIA PDF debug failed")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "eia_pdf_debug_failed",
                "message": str(e),
                "traceback": traceback.format_exc(),
            },
        )


@router.get("/debug/log-file")
def debug_log_file(lines: int = 500):
    log_file = Path("logs/oilintel_app.log")

    if not log_file.exists():
        return {
            "status": "missing",
            "path": str(log_file),
            "content": [],
        }

    content = log_file.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines()

    return {
        "status": "success",
        "path": str(log_file),
        "lines": lines,
        "content": content[-lines:],
    }
