import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

# Alembic Config object
config = context.config

# Setup loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Підставляємо DATABASE_URL з .env автоматично
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Імпортуємо моделі щоб Alembic знав про них при autogenerate
import app.models
from app.core.database import db

target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (без живого з'єднання)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (з живим з'єднанням)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
