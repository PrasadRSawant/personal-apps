# app/db/models.py

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID # Import UUID type for Postgres
from app.db.database import Base
import uuid # For generating default UUIDs

class User(Base):
    __tablename__ = "users"

    # Changed from Integer to UUID as Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    
    email = Column(String, unique=True, index=True, nullable=False)
    # Hashed password for Basic Auth. Null for SSO users.
    hashed_password = Column(String, nullable=True) 
    is_active = Column(Boolean, default=True)
    # 'Basic' or 'SSO'
    auth_method = Column(String, default="Basic", nullable=False)