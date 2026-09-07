from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import ping_database

settings = get_settings()

app = FastAPI(
    title="LEO HQ API",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.get("/api/v1/health")
def api_health() -> dict[str, str]:
    db_ok = ping_database()
    return {
        "status": "ok" if db_ok else "degraded",
        "env": settings.app_env,
        "database": "up" if db_ok else "down",
    }
