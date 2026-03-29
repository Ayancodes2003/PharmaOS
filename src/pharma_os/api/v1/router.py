"""Top-level API router for v1 endpoints."""

from fastapi import APIRouter

from pharma_os.api.v1.adverse_events import router as adverse_events_router
from pharma_os.api.v1.agents import router as agents_router
from pharma_os.api.v1.drug_exposures import router as drug_exposures_router
from pharma_os.api.v1.operations import router as operations_router
from pharma_os.api.v1.patients import router as patients_router
from pharma_os.api.v1.predictions import router as predictions_router
from pharma_os.api.v1.system import router as system_router
from pharma_os.api.v1.trials import router as trials_router

v1_router = APIRouter(tags=["v1"])
v1_router.include_router(system_router)
v1_router.include_router(patients_router)
v1_router.include_router(trials_router)
v1_router.include_router(adverse_events_router)
v1_router.include_router(drug_exposures_router)
v1_router.include_router(predictions_router)
v1_router.include_router(agents_router)
v1_router.include_router(operations_router)
