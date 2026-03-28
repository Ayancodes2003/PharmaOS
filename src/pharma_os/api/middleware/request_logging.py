"""Request logging middleware with request-id propagation."""

from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.responses import Response

from pharma_os.observability.logging import get_logger

logger = get_logger(__name__)


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log inbound API requests with request correlation metadata."""
    request_id = request.headers.get("x-request-id") or str(uuid4())
    start = perf_counter()

    response = await call_next(request)

    duration_ms = round((perf_counter() - start) * 1000, 2)
    response.headers["x-request-id"] = request_id

    logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    return response


def register_request_logging_middleware(app: FastAPI) -> None:
    """Register request logging middleware for API-safe request tracing."""
    app.middleware("http")(request_logging_middleware)
