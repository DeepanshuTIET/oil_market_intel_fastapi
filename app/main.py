from pathlib import Path
import sys
import logging
import traceback
import time

import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import RawObservation

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.routes import router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.session import create_db_and_tables


setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.4.0-debug",
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    started = time.perf_counter()

    logger.info(
        f"REQUEST START method={request.method} path={request.url.path} query={request.url.query}"
    )

    try:
        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        logger.info(
            f"REQUEST END method={request.method} path={request.url.path} "
            f"status={response.status_code} elapsed_ms={elapsed_ms}"
        )

        return response

    except Exception as e:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        logger.exception(
            f"REQUEST ERROR method={request.method} path={request.url.path} "
            f"elapsed_ms={elapsed_ms} error={e}"
        )

        raise


@app.on_event("startup")
def on_startup():
    logger.info("Application startup started")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")

    create_db_and_tables()

    logger.info("Database tables checked/created")
    logger.info("Application startup completed")

    logger.info("Registered FastAPI app routes:")
    for route in app.routes:
        methods = sorted(list(route.methods)) if getattr(route, "methods", None) else []
        logger.info(f"ROUTE path={route.path} methods={methods} name={route.name}")


app.include_router(router)


@app.get("/debug/app-routes")
def debug_app_routes():
    """
    Shows all routes registered on the FastAPI app.
    Use this to verify /quanthub/history is active.
    """

    return {
        "status": "success",
        "routes": [
            {
                "path": route.path,
                "name": route.name,
                "methods": sorted(list(route.methods)) if route.methods else [],
            }
            for route in app.routes
        ],
    }


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    requested_path = request.url.path

    routes = []

    for route in app.routes:
        path = getattr(route, "path", "")
        methods = sorted(list(route.methods)) if getattr(route, "methods", None) else []

        routes.append(
            {
                "path": path,
                "methods": methods,
                "name": getattr(route, "name", None),
            }
        )

    candidates = [
        route
        for route in routes
        if "quanthub" in route["path"].lower()
        or "qh" in route["path"].lower()
        or (requested_path.split("/")[1:2] and requested_path.split("/")[1] in route["path"])
    ]

    logger.warning(
        f"404 NOT FOUND requested_path={requested_path}, candidates={candidates}"
    )

    return JSONResponse(
        status_code=404,
        content={
            "detail": "Not Found",
            "requested_path": requested_path,
            "hint": "Route not registered on active FastAPI app. Check /debug/app-routes.",
            "candidate_routes": candidates,
        },
    )


STATIC_DIR = PROJECT_ROOT / "app" / "static"

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/static/index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        reload_excludes=[
            ".venv",
            "venv",
            "__pycache__",
            "*.pyc",
            ".git",
            "logs",
            "oilintel.db",
            "eia_weekly_output",
        ],
        log_level="debug",
    )