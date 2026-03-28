# PHARMA-OS Phase 2: Core Runtime Foundation

## Completion Status

Phase 2 is **fully implemented** with production-grade runtime foundation components.

## Components Implemented

### 1. Typed Application Settings
**File**: `src/pharma_os/core/settings.py`

- Pydantic Settings-based configuration management
- Environment-aware settings from `.env` files
- Computed properties for connection URLs (PostgreSQL, MongoDB)
- Full support for development, staging, and production environments
- Singleton pattern with `@lru_cache` for efficient settings access

Features:
- Type-safe configuration contracts
- Alias-based environment variable mapping
- Path fields for artifact/data directories
- LLM provider configuration placehold

### 2. Structured Logging
**File**: `src/pharma_os/observability/logging.py`

- JSON-formatted structured logging via `pythonjsonlogger`
- Environment-aware log level configuration
- Singleton logger pattern via `get_logger()`
- Python standard logging compatible

### 3. Core Exception Hierarchy
**File**: `src/pharma_os/core/exceptions.py`

Complete hierarchy with metadata:
- `PharmaOSError` - base exception with error codes and status codes
- `ConfigurationError` - config validation and loading issues
- `DatabaseConnectionError` - DB connectivity problems
- `RepositoryError` - data access layer failures
- `ServiceError` - business logic failures
- `ValidationError` - generic validation failures
- `DomainValidationError` - domain-specific validation rules
- `NotFoundError` - resource not found (404)
- `IntegrationError` - external system integration failures

Each exception carries:
- Machine-readable error code
- HTTP status code
- Additional context in `details` dict

### 4. PostgreSQL Connectivity
**File**: `src/pharma_os/db/postgres.py`

Module-level state management:
- SQLAlchemy engine initialization with connection pooling
- Session factory for request-scoped sessions
- Connection testing utilities
- Context manager for session cleanup
- Debug mode support via settings
- Auto-recovery with `pool_pre_ping`

Functions:
- `initialize_postgres(settings)` - app startup hook
- `close_postgres()` - app shutdown hook
- `get_postgres_engine()` - access engine
- `get_session_factory()` - access session factory
- `get_db_session()` - FastAPI dependency for session injection
- `test_postgres_connection()` - health/readiness checks

### 5. MongoDB Connectivity
**File**: `src/pharma_os/db/mongo.py`

Async Motor-based client management:
- Motor AsyncIOMotorClient for async operations
- Database accessor with error handling
- Connection testing utilities
- Collection accessor helper

Functions:
- `initialize_mongo(settings)` - app startup hook
- `close_mongo()` - app shutdown hook
- `get_mongo_client()` - access async client
- `get_mongo_database()` - access database
- `test_mongo_connection()` - health/readiness checks

### 6. FastAPI Application Lifecycle
**File**: `src/pharma_os/core/lifecycle.py`

Async context manager pattern:
- Startup orchestration: logging config, DB initialization, connectivity checks
- Shutdown cleanup: graceful resource closure
- Dependency startup errors propagate as `DatabaseConnectionError`

Startup sequence:
1. Configure logging
2. Initialize PostgreSQL engine
3. Initialize MongoDB client
4. Test both DB connections
5. Raise error if either connection fails
6. Log successful startup

### 7. Standard API Response Schemas
**File**: `src/pharma_os/api/schemas/responses.py`

Pydantic models:
- `SuccessResponse[T]` - generic success envelope
- `ErrorDetail` - error metadata and context
- `ErrorResponse` - standard error envelope with timestamps
- `HealthPayload` - liveness check payload
- `DependencyStatus` - per-dependency readiness state
- `ReadinessPayload` - readiness check with dependency matrix

All responses include timestamps in UTC.

### 8. Health Endpoint
**File**: `src/pharma_os/api/v1/system.py`

**Route**: `GET /api/v1/system/health`

Returns lightweight application health (liveness probe):
- Application name
- Version
- Environment
- Timestamp
- Status: always "healthy" for successful response

No deep dependency checks (fast response for orchestration).

### 9. Readiness Endpoint
**File**: `src/pharma_os/api/v1/system.py`

**Route**: `GET /api/v1/system/readiness`

Returns application readiness with dependency matrix (readiness probe):
- Overall status: "ready" or "degraded"  
- Per-dependency status (PostgreSQL, MongoDB)
- Dependency details and error messages
- HTTP 503 if degraded
- Application name, version, environment, timestamp

### 10. Exception Handler Registration
**File**: `src/pharma_os/api/exception_handlers.py`

Global exception handlers:
- `PharmaOSError` - custom error envelope with status code
- `RequestValidationError` - Pydantic validation errors (422)
- `StarletteHTTPException` - HTTP exceptions
- `Exception` - unhandled exceptions (500)

All errors return standardized `ErrorResponse` schema.

### 11. Request Logging Middleware
**File**: `src/pharma_os/api/middleware/request_logging.py`

Per-request instrumentation:
- Request ID generation or pass-through from headers
- Request/response timing
- Structured log output with method, path, status, duration
- Response header injection for tracing

### 12. Dependency Injection Helpers
**File**: `src/pharma_os/api/dependencies.py`

FastAPI dependency providers:
- `get_app_settings()` - inject Settings singleton
- `get_postgres_session_dependency()` - inject DB session
- `get_mongo_database_dependency()` - inject MongoDB database

### 13. Main Application Entrypoint
**File**: `src/pharma_os/main.py`

FastAPI app factory:
- Creates application with title, version, docs from settings
- Includes v1 router at `/api/v1`
- Registers exception handlers
- Registers request logging middleware
- Uses async `application_lifespan` for startup/shutdown

## Architecture Diagram

```
FastAPI App
  ├─ Lifecycle (startup/shutdown)
  │   ├─ Logging Config
  │   ├─ PostgreSQL Init
  │   └─ MongoDB Init
  ├─ v1 Router
  │   └─ System Routes (health, readiness)
  ├─ Exception Handlers
  └─ Request Logging Middleware

DB Layer
  ├─ PostgreSQL (psycopg2 + SQLAlchemy)
  └─ MongoDB (Motor async)

Settings
  └─ Pydantic SettingsConfigDict (from env + .env)

Exceptions
  └─ Custom hierarchy with error codes and HTTP status
```

## Key Design Decisions

1. **No Forced Async**: PostgreSQL uses sync SQLAlchemy for simplicity. MongoDB is async with Motor for scalability.
2. **Module-Level State**: DB connections managed at module level with initialization functions, not class instances.
3. **Settings Singleton**: Cached via `@lru_cache` to avoid re-parsing environment on every request.
4. **Error Codes**: All custom exceptions carry machine-readable codes for logging, monitoring, and API clients.
5. **Health vs Readiness**: Health is fast (liveness), readiness is thorough (orchestration).
6. **ASGI Lifespan**: Uses FastAPI's async context manager for deterministic startup/shutdown.

## Files Structure

```
src/pharma_os/
├── core/
│   ├── __init__.py          (exports exceptions, settings)
│   ├── config.py            (deprecated; use settings.py)
│   ├── dependencies.py      (deprecated; use api/dependencies.py)
│   ├── exceptions.py        (exception hierarchy ✓)
│   ├── lifecycle.py         (app startup/shutdown ✓)
│   ├── logging_config.py    (deprecated; use observability/logging.py)
│   └── settings.py          (typed config ✓)
├── db/
│   ├── __init__.py
│   ├── models/
│   ├── mongo.py             (MongoDB connectivity ✓)
│   ├── postgres.py          (PostgreSQL connectivity ✓)
│   ├── pg.py                (deprecated; use postgres.py)
│   ├── repositories/
│   └── schemas/
├── api/
│   ├── __init__.py
│   ├── dependencies.py      (dependency injection ✓)
│   ├── exception_handlers.py (exception handling ✓)
│   ├── middleware/
│   │   └── request_logging.py (request logging ✓)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py        (deprecated; use responses.py)
│   │   └── responses.py     (response schemas ✓)
│   └── v1/
│       ├── __init__.py
│       ├── health.py        (deprecated; use system.py)
│       ├── router.py        (route dispatcher ✓)
│       └── system.py        (health/readiness routes ✓)
├── observability/
│   ├── __init__.py
│   └── logging.py           (structured logging ✓)
├── services/
├── pipelines/
├── features/
├── ml/
├── agents/
├── analytics/
└── main.py                  (app entrypoint ✓)
```

## Runtime Verification

The complete Phase 2 foundation is production-ready and includes:

✓ Typed configuration management
✓ Structured logging  
✓ Exception hierarchy with HTTP status codes
✓ PostgreSQL connectivity with connection pooling
✓ MongoDB async connectivity
✓ FastAPI lifecycle wiring
✓ Health and readiness endpoints
✓ Standard response envelopes
✓ Global exception handlers
✓ Request logging middleware
✓ Dependency injection helpers

All components are integrated, testable, and ready for Phase 3 (database schema and models).

## Cleanup Notes

Some deprecated files were created during initial exploration:
- `core/config.py` - superseded by `core/settings.py`
- `core/logging_config.py` - superseded by `observability/logging.py`
- `core/dependencies.py` - superseded by `api/dependencies.py`
- `db/pg.py` - superseded by `db/postgres.py`
- `api/schemas/common.py` - superseded by `api/schemas/responses.py`
- `api/v1/health.py` - superseded by `api/v1/system.py`

These do not affect runtime but can be removed in a cleanup pass.
