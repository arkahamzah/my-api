import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import metadata
from app.core.config import settings
from app.infrastructure.database.base import Base
target_metadata = Base.metadata

def get_url():
    """Ambil DATABASE_URL sync dari env atau settings."""
    raw = os.environ.get("DATABASE_URL", "")
    if raw:
        # Railway pakai postgres:// atau postgresql://, konversi ke psycopg2
        url = raw.replace("postgresql+asyncpg://", "postgresql://", 1)
        url = url.replace("postgres://", "postgresql://", 1)
        return url
    return settings.DATABASE_URL_SYNC

def run_migrations_online():
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
