from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.lifespan import verify_dependencies

router = APIRouter(tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> JSONResponse:
    checks = await verify_dependencies()
    is_ready = checks.get("database") == "ok" and checks.get("redis") in {"ok", "disabled"}
    payload = {"status": "ok" if is_ready else "degraded", "service": settings.app_name, **checks}
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )
