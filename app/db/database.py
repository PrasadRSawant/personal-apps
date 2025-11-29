from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create the SQLAlchemy engine
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL
)
# Configure a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models to inherit from
Base = declarative_base()

def create_db_tables():
    """Function to create all tables defined in Base.metadata"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")