import os
import sys
# Add the project root to the path so we can import app modules (like config)
sys.path.append(os.getcwd()) 

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine # Need create_engine if not using an imported engine

from alembic import context

# 🔑 Imports from your FastAPI Project
from app.db.database import Base 
from app.db.models import * # Import at least one model, or all using 'import *' 
from app.core.config import settings
# ------------------------------------

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 🔑 Point target_metadata to your Base object
target_metadata = Base.metadata 

# ... (other code remains the same)

def run_migrations_offline() -> None:
    # ... (No changes needed here unless you define sqlalchemy.url in alembic.ini)
    # url = config.get_main_option("sqlalchemy.url")
    # For robust offline mode with your setup, you should use the URL from settings:
    url = settings.SQLALCHEMY_DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    This version replaces the engine_from_config call 
    with a direct connection using the URL loaded by settings.
    """
    
    # 🔑 CORRECTION: Get the SQLAlchemy URL from your application's settings
    # This ensures Alembic uses the same URL loaded from the .env file.
    connectable = create_engine(
        settings.SQLALCHEMY_DATABASE_URL,
        poolclass=pool.NullPool,
    )

    # 🛑 The original block below is replaced by the create_engine call above:
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()