"""Alembic environment configuration for PHARMA-OS."""

from __future__ import annotations

import os
from logging.config import fileConfig
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import engine_from_config, pool

from pharma_os.db.models import target_metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _resolved_postgres_url() -> str:
    """Resolve database URL from environment variables for Alembic execution."""
    explicit_url = os.getenv("POSTGRES_URL")
    if explicit_url:
        return explicit_url

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "pharma_os")
    user = quote_plus(os.getenv("POSTGRES_USER", "pharma_admin"))
    password = quote_plus(os.getenv("POSTGRES_PASSWORD", "pharma_admin"))
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


config.set_main_option("sqlalchemy.url", _resolved_postgres_url())


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
