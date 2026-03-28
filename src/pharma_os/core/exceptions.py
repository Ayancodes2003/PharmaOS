"""Application exception hierarchy for PHARMA-OS."""

from typing import Any


class PharmaOSError(Exception):
    """Base exception type for the PHARMA-OS platform."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "PHARMA_OS_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ConfigurationError(PharmaOSError):
    """Raised when required runtime configuration is missing or invalid."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


class DatabaseConnectionError(PharmaOSError):
    """Raised when a database connection cannot be established or is unavailable."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            error_code="DATABASE_CONNECTION_ERROR",
            status_code=503,
            details=details,
        )


class RepositoryError(PharmaOSError):
    """Raised by data access layer operations."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            error_code="REPOSITORY_ERROR",
            status_code=500,
            details=details,
        )


class ServiceError(PharmaOSError):
    """Raised by service-layer operations."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            error_code="SERVICE_ERROR",
            status_code=500,
            details=details,
        )


class ValidationError(PharmaOSError):
    """Raised for generic validation issues in domain/application layers."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class DomainValidationError(ValidationError):
    """Raised for domain-specific validation rule violations."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)
        self.error_code = "DOMAIN_VALIDATION_ERROR"


class NotFoundError(PharmaOSError):
    """Raised when requested resources do not exist."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            error_code="NOT_FOUND_ERROR",
            status_code=404,
            details=details,
        )


class IntegrationError(PharmaOSError):
    """Raised when external system integration or API calls fail."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            error_code="INTEGRATION_ERROR",
            status_code=502,
            details=details,
        )
