import asyncio
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text


router = APIRouter(prefix="/health", tags=["Health"])


class HealthLiveResponse(BaseModel):
    """Liveness probe response model."""
    model_config = ConfigDict(extra="forbid")
    status: str = "alive"


class HealthReadyResponse(BaseModel):
    """Readiness probe response model."""
    model_config = ConfigDict(extra="forbid")
    status: str
    database: str


@router.get(
    "/live",
    response_model=HealthLiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
)
def get_liveness() -> HealthLiveResponse:
    """Confirms the process is running and reachable."""
    return HealthLiveResponse(status="alive")


@router.get(
    "/ready",
    response_model=HealthReadyResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Database or external dependency unreachable",
            "model": HealthReadyResponse,
        }
    },
    summary="Readiness check",
)
async def get_readiness(request: Request):
    """Verifies that the application and its database connection are ready to handle traffic."""
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "Engine uninitialized"},
        )

    try:
        # Protect against hanging DB calls with a 2-second timeout
        async with asyncio.timeout(2.0):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        return HealthReadyResponse(status="ready", database="connected")
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": str(exc)},
        )
