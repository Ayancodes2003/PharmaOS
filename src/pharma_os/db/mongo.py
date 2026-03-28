"""MongoDB client and database lifecycle management."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from pharma_os.core.exceptions import ConfigurationError, DatabaseConnectionError
from pharma_os.core.settings import Settings
from pharma_os.observability.logging import get_logger

logger = get_logger(__name__)

_mongo_client: AsyncIOMotorClient | None = None
_mongo_database_name: str | None = None


async def initialize_mongo(settings: Settings) -> None:
    """Initialize MongoDB client and verify connectivity."""
    global _mongo_client, _mongo_database_name

    mongo_url = settings.resolved_mongo_url
    if not mongo_url:
        raise ConfigurationError("MongoDB URL is not configured")

    logger.info("initializing mongodb client")
    _mongo_client = AsyncIOMotorClient(mongo_url)
    _mongo_database_name = settings.mongo_db


async def close_mongo() -> None:
    """Close MongoDB client resources."""
    global _mongo_client, _mongo_database_name

    if _mongo_client is not None:
        logger.info("closing mongodb client")
        _mongo_client.close()

    _mongo_client = None
    _mongo_database_name = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Return initialized MongoDB client."""
    if _mongo_client is None:
        raise DatabaseConnectionError("MongoDB client not initialized")
    return _mongo_client


def get_mongo_database() -> AsyncIOMotorDatabase:
    """Return initialized MongoDB database handle."""
    client = get_mongo_client()
    if _mongo_database_name is None:
        raise DatabaseConnectionError("MongoDB database name not initialized")
    return client[_mongo_database_name]


async def test_mongo_connection() -> tuple[bool, str]:
    """Run a lightweight connection check against MongoDB."""
    try:
        client = get_mongo_client()
        await client.admin.command("ping")
        return True, "MongoDB connection successful"
    except Exception as exc:
        return False, f"MongoDB connection failed: {exc}"
