# tests/conftest.py

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, drop_database, database_exists

# Local app imports
from app.main import app
from app.db.database import Base
from app.core.dependencies import get_db
from app.core.config import settings

# 1. Setup a Test Database URL
TEST_DATABASE_URL = "postgresql://{user}:{password}@{host}:{port}/{db_name}_test".format(
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    db_name=settings.POSTGRES_DB
)

# 2. Setup a ROOT Database URL (used for managing the test database)
# This URL connects to a standard database (like 'postgres') to execute administrative tasks.
ROOT_DATABASE_URL = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    db_name='postgres' # Connect to 'postgres' to manage the test DB
)
TEST_DB_NAME = settings.POSTGRES_DB + '_test'


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Fixture to create and drop the test database once per session."""
    
    # Engine pointing to the ROOT DB for administrative tasks (like dropping)
    root_engine = create_engine(ROOT_DATABASE_URL, isolation_level="AUTOCOMMIT")
    # Engine pointing to the TEST DB for table creation/existence check
    test_engine = create_engine(TEST_DATABASE_URL)
    
    # --- Start Pre-Test Setup ---
    if database_exists(test_engine.url):
        print(f"Dropping existing test database: {TEST_DB_NAME}")
        
        # 1. Force disconnect all active sessions to the test database
        with root_engine.connect() as conn:
            # Query to find and terminate all other connections to the test database
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
                  AND pid <> pg_backend_pid();
            """))
        
        # 2. Now drop the database (should succeed after terminating connections)
        drop_database(test_engine.url)

    # 3. Create the clean test database
    print(f"Creating test database: {TEST_DB_NAME}")
    create_database(test_engine.url)

    # 4. Create all tables in the test database
    Base.metadata.create_all(bind=test_engine)
    
    # Yield control to run the tests
    yield
    
    # --- Start Post-Test Cleanup ---
    # 5. Drop the test database when the session finishes
    print(f"Dropping test database: {TEST_DB_NAME} after session completion.")
    
    # Force disconnect before dropping the final time
    if database_exists(test_engine.url):
        with root_engine.connect() as conn:
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
                  AND pid <> pg_backend_pid();
            """))
            
        drop_database(test_engine.url)


@pytest.fixture(scope="function")
def test_db_session() -> Generator[Session, None, None]:
    """Fixture to provide an independent database session for each test."""
    
    test_engine = create_engine(TEST_DATABASE_URL)
    connection = test_engine.connect()
    
    # Begin a transaction that can be rolled back
    transaction = connection.begin()
    session = Session(bind=connection)

    # Override the application's get_db dependency to use the test session
    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    
    yield session  # Run the test

    # Rollback the transaction to ensure the database state is reset after each test
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(test_db_session):
    """Fixture to provide a reusable FastAPI TestClient."""
    # The client uses the dependency override set by test_db_session
    with TestClient(app) as c:
        yield c