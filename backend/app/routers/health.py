
#
from fastapi import APIRouter

from app.redis import redis_pool
from app.schemas.responses import HealthResponse

router = APIRouter(tags=["Infraestructura"])


@router.get("/health", response_model=HealthResponse)
async def health_check():

    redis_status = "connected"
    try:
        await redis_pool.ping()
    except Exception:
        redis_status = "disconnected"

    overall_status = "ok" if redis_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "service": "virtual-queue-api",
        "redis": redis_status,
    }
