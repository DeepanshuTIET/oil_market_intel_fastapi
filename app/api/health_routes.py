from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {
        "status": "api_running",
        "dashboard": "/dashboard",
        "docs": "/docs",
        "debug_config": "/debug/config",
        "debug_db": "/debug/db",
        "database_url": settings.DATABASE_URL,
        "sources": {
            "eia_pdf": {
                "configured": True,
                "note": "EIA uses public WPSR overview PDF.",
            },
            "quanthub": {
                "base_url": getattr(settings, "QUANTHUB_BASE_URL", None),
                "username_loaded": bool(
                    getattr(settings, "QUANTHUB_USERNAME", None)
                    and settings.QUANTHUB_USERNAME.strip()
                ),
                "password_loaded": bool(
                    getattr(settings, "QUANTHUB_PASSWORD", None)
                    and settings.QUANTHUB_PASSWORD.strip()
                ),
                "access_token_loaded": bool(
                    getattr(settings, "QUANTHUB_ACCESS_TOKEN", None)
                    and settings.QUANTHUB_ACCESS_TOKEN.strip()
                ),
                "refresh_token_loaded": bool(
                    getattr(settings, "QUANTHUB_REFRESH_TOKEN", None)
                    and settings.QUANTHUB_REFRESH_TOKEN.strip()
                ),
                "endpoints": [
                    "/api/v2/ohlc/",
                    "/api/v2/tas/",
                    "/api/v2/fairvalue/",
                    "/api/v2/vap/",
                ],
            },
            "x": {
                "bearer_token_loaded": bool(
                    getattr(settings, "X_BEARER_TOKEN", None)
                    and settings.X_BEARER_TOKEN.strip()
                ),
            },
        },
    }
