from app.api.routes import router
from app.api.qh_routes import router as qh_router
from app.api.health_routes import router as health_router
from app.api.debug_routes import router as debug_router
from app.api.eia_routes import router as eia_router
from app.api.cot_routes import router as cot_router
from app.api.news_routes import router as news_router

__all__ = ["router", "qh_router", "health_router", "debug_router", "eia_router", "cot_router", "news_router"]