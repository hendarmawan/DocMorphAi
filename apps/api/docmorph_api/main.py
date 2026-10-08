from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from docmorph_ai import get_provider
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from docmorph_api import __version__
from docmorph_api.config import Settings, get_settings
from docmorph_api.db import Database
from docmorph_api.errors import install_error_handlers
from docmorph_api.routers import design, documents, health, templates
from docmorph_api.storage import make_storage

log = logging.getLogger("docmorph.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # M1: create tables directly; versioned migrations (Alembic) arrive with M2.
        app.state.db.create_all()
        log.info("DocMorph API %s ready (env=%s, ai=%s)", __version__, settings.env, settings.ai_provider)
        yield

    app = FastAPI(
        title="DocMorph AI API",
        version=__version__,
        description="Upload documents, inspect structure, apply templates, reprompt designs, export.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.db = Database(settings.database_url)
    app.state.storage = make_storage(settings)
    app.state.ai = get_provider(settings.ai_provider, **({"model": settings.ai_model} if settings.ai_model else {}))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-Tenant-ID"],
        expose_headers=["Content-Disposition", "X-DocMorph-SHA256"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        return response

    install_error_handlers(app)
    for router in (health.router, templates.router, documents.router, design.router):
        app.include_router(router)
    return app


def run() -> None:  # pragma: no cover - CLI entry point
    import uvicorn

    uvicorn.run("docmorph_api.main:create_app", factory=True, host="0.0.0.0", port=8000)  # noqa: S104
