from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from docmorph_api import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness: the process is up."""
    return {"status": "ok", "version": __version__}


@router.get("/ready")
def ready(request: Request):
    """Readiness: database, object storage and (if configured) Redis respond."""
    state = request.app.state
    checks: dict[str, bool] = {}
    try:
        with state.db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    checks["storage"] = bool(state.storage.ping())
    if state.settings.redis_url:
        try:
            import redis

            checks["redis"] = bool(redis.Redis.from_url(state.settings.redis_url, socket_timeout=1).ping())
        except Exception:
            checks["redis"] = False
    ok = all(checks.values())
    return JSONResponse({"status": "ok" if ok else "degraded", "checks": checks}, status_code=200 if ok else 503)
