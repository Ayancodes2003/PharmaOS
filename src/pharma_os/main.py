"""FastAPI application entrypoint for PHARMA-OS."""

from fastapi import FastAPI

from pharma_os.api.exception_handlers import register_exception_handlers
from pharma_os.api.middleware.request_logging import register_request_logging_middleware
from pharma_os.api.v1.router import v1_router
from pharma_os.core.lifecycle import application_lifespan
from pharma_os.core.settings import get_settings


def create_application() -> FastAPI:
    """Create and configure the PHARMA-OS ASGI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.app_debug,
        lifespan=application_lifespan,
    )

    app.include_router(v1_router, prefix=settings.api_v1_prefix)
    register_exception_handlers(app)
    register_request_logging_middleware(app)

    return app


app = create_application()
