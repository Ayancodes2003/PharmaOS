"""Centralized typed runtime settings for PHARMA-OS."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="pharma-os", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: Literal["local", "dev", "staging", "prod", "test"] = Field(
        default="local",
        alias="APP_ENV",
    )
    app_debug: bool = Field(default=False, alias="APP_DEBUG")

    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    postgres_url: str | None = Field(default=None, alias="POSTGRES_URL")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="pharma_os", alias="POSTGRES_DB")
    postgres_user: str = Field(default="pharma_admin", alias="POSTGRES_USER")
    postgres_password: str = Field(default="pharma_admin", alias="POSTGRES_PASSWORD")

    mongo_url: str | None = Field(default=None, alias="MONGO_URL")
    mongo_host: str = Field(default="localhost", alias="MONGO_HOST")
    mongo_port: int = Field(default=27017, alias="MONGO_PORT")
    mongo_db: str = Field(default="pharma_os", alias="MONGO_DB")
    mongo_user: str | None = Field(default=None, alias="MONGO_USER")
    mongo_password: str | None = Field(default=None, alias="MONGO_PASSWORD")

    artifact_root: Path = Field(default=Path("./artifacts"), alias="ARTIFACT_ROOT")
    model_registry_path: Path = Field(default=Path("./artifacts/models"), alias="MODEL_REGISTRY_PATH")
    metrics_path: Path = Field(default=Path("./artifacts/metrics"), alias="METRICS_PATH")
    reports_path: Path = Field(default=Path("./artifacts/reports"), alias="REPORTS_PATH")

    data_raw_path: Path = Field(default=Path("./data/raw"), alias="DATA_RAW_PATH")
    data_processed_path: Path = Field(default=Path("./data/processed"), alias="DATA_PROCESSED_PATH")
    data_load_ready_path: Path = Field(default=Path("./data/load_ready"), alias="DATA_LOAD_READY_PATH")
    data_feature_ready_path: Path = Field(
        default=Path("./data/feature_ready"),
        alias="DATA_FEATURE_READY_PATH",
    )
    data_feature_store_path: Path = Field(
        default=Path("./data/feature_store"),
        alias="DATA_FEATURE_STORE_PATH",
    )
    data_source_path: Path = Field(default=Path("./data/source"), alias="DATA_SOURCE_PATH")
    patients_source_path: Path | None = Field(default=None, alias="PATIENTS_SOURCE_PATH")
    trials_source_path: Path | None = Field(default=None, alias="TRIALS_SOURCE_PATH")
    adverse_events_source_path: Path | None = Field(default=None, alias="ADVERSE_EVENTS_SOURCE_PATH")
    drug_exposures_source_path: Path | None = Field(default=None, alias="DRUG_EXPOSURES_SOURCE_PATH")

    llm_provider: str | None = Field(default=None, alias="LLM_PROVIDER")
    llm_base_url: str | None = Field(default=None, alias="LLM_BASE_URL")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")

    @property
    def resolved_postgres_url(self) -> str:
        """Build PostgreSQL connection URL if not explicitly provided."""
        if self.postgres_url:
            return self.postgres_url

        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return (
            f"postgresql+psycopg2://{user}:{password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def resolved_mongo_url(self) -> str:
        """Build MongoDB connection URL if not explicitly provided."""
        if self.mongo_url:
            return self.mongo_url

        if self.mongo_user and self.mongo_password:
            user = quote_plus(self.mongo_user)
            password = quote_plus(self.mongo_password)
            return f"mongodb://{user}:{password}@{self.mongo_host}:{self.mongo_port}"

        return f"mongodb://{self.mongo_host}:{self.mongo_port}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance for DI and runtime use."""
    return Settings()
