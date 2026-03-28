"""Top-level API router for v1 endpoints."""

from fastapi import APIRouter

from pharma_os.api.v1.system import router as system_router

v1_router = APIRouter(tags=["v1"])
v1_router.include_router(system_router)
