import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, ingestion, management
from app.core.config import get_settings


settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(message)s")

app = FastAPI(
    title="HoneyPot System API",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(management.router, prefix="/api/v1")

