"""System-level endpoints for health and readiness probes."""

from fastapi import APIRouter, Depends, Response, status

from pharma_os.api.dependencies import get_app_settings
from pharma_os.api.schemas.responses import (
    DependencyStatus,
    HealthPayload,
    ReadinessPayload,
    SuccessResponse,
)
from pharma_os.core.settings import Settings
from pharma_os.db.mongo import test_mongo_connection
from pharma_os.db.postgres import test_postgres_connection
from pharma_os.observability.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health", response_model=SuccessResponse[HealthPayload], status_code=status.HTTP_200_OK)
async def health(settings: Settings = Depends(get_app_settings)) -> SuccessResponse[HealthPayload]:
    """Liveness endpoint for basic process checks."""
    payload = HealthPayload(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
    return SuccessResponse(message="service healthy", data=payload)


@router.get(
    "/readiness",
    response_model=SuccessResponse[ReadinessPayload],
    status_code=status.HTTP_200_OK,
)
async def readiness(
    response: Response,
    settings: Settings = Depends(get_app_settings),
) -> SuccessResponse[ReadinessPayload]:
    """Readiness endpoint for dependency-level checks."""
    pg_ok, pg_detail = test_postgres_connection()
    mongo_ok, mongo_detail = await test_mongo_connection()

    dependencies = {
        "postgresql": DependencyStatus(status="ready" if pg_ok else "not_ready", detail=pg_detail),
        "mongodb": DependencyStatus(status="ready" if mongo_ok else "not_ready", detail=mongo_detail),
    }

    overall_status = "ready" if pg_ok and mongo_ok else "degraded"
    if overall_status == "degraded":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.warning("readiness degraded", extra={"dependencies": {k: v.status for k, v in dependencies.items()}})

    payload = ReadinessPayload(
        status=overall_status,
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        dependencies=dependencies,
    )

    return SuccessResponse(message="readiness evaluated", data=payload)


@router.get("/metadata", response_model=SuccessResponse[dict[str, str]], status_code=status.HTTP_200_OK)
async def metadata(settings: Settings = Depends(get_app_settings)) -> SuccessResponse[dict[str, str]]:
    """Basic service metadata endpoint for deployment and diagnostics."""
    payload = {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "api_prefix": settings.api_v1_prefix,
    }
    return SuccessResponse(message="service metadata retrieved", data=payload)
