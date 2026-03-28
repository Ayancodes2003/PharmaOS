"""FastAPI exception handlers for standardized API error responses."""

from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from pharma_os.api.schemas.responses import ErrorDetail, ErrorResponse
from pharma_os.core.exceptions import PharmaOSError
from pharma_os.observability.logging import get_logger

logger = get_logger(__name__)


def _validation_errors_to_details(errors: Sequence[dict[str, object]]) -> dict[str, object]:
    return {"validation_errors": list(errors)}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(PharmaOSError)
    async def pharma_os_error_handler(_: Request, exc: PharmaOSError) -> JSONResponse:
        logger.error(
            "handled platform exception",
            extra={"error_code": exc.error_code, "details": exc.details},
        )
        payload = ErrorResponse(
            error=ErrorDetail(code=exc.error_code, message=exc.message, details=exc.details)
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = _validation_errors_to_details(exc.errors())
        payload = ErrorResponse(
            error=ErrorDetail(
                code="REQUEST_VALIDATION_ERROR",
                message="Request validation failed",
                details=details,
            )
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        _: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorDetail(
                code="HTTP_ERROR",
                message=str(exc.detail),
                details={"status_code": exc.status_code},
            )
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled exception", exc_info=exc)
        payload = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                details={},
            )
        )
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))
