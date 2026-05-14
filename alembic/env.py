import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add backend/ to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import settings
from core.database import Base

# Import all models so Alembic can detect them
from models.report import Report, Category, Issue, GoodPoint  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Use sync psycopg2 URL for Alembic (strip asyncpg, strip unsupported params)
def get_sync_url() -> str:
    url = settings.DATABASE_URL
    # asyncpg → psycopg2 driver
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    # asyncpg uses ssl=require, psycopg2 uses sslmode=require
    url = url.replace("ssl=require", "sslmode=require")
    # Strip params unsupported by psycopg2
    if "?" in url:
        base, qs = url.split("?", 1)
        params = [p for p in qs.split("&") if "channel_binding" not in p]
        url = base + ("?" + "&".join(params) if params else "")
    return url


def run_migrations_offline() -> None:
    url = get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_sync_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
