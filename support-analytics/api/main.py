from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.router import router
from config import get_settings
from database.session import Base, engine


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Customer Support Ticket Intelligence & Product Telemetry API",
        description="Analytics endpoints powering the portfolio dashboard",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup_event():
        logger.info("Ensuring database schema exists at %s", settings.database_url)
        Base.metadata.create_all(bind=engine)

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    app.include_router(router)
    return app


app = create_app()

