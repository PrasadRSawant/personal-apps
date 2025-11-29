# app/core/dependencies.py (Revised get_current_user)

from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.core.security import decode_access_token
from app.db.models import User
from app.core.redis_client import redis_client as global_redis_client
import redis.asyncio as redis 
from app.core.config import settings
# Dependency to get the database session (keeping it here for context)
def get_db() -> Generator:
    """Provides a database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis_client() -> redis.Redis:
    """
    Dependency to access the global, initialized Redis client.
    Raises 500 if the client was not initialized during startup.
    """
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    ) 
    if redis_client is None:
        # This shouldn't happen if startup was successful, but is a safe guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Redis client not initialized."
        )
    return redis_client

# Note: If your DB dependency uses a 'yield' (Generator) pattern, 
# you should also use a yield pattern here, but for Redis client access, 
# simply returning the global instance is often sufficient.

# Dependency for JWT/Bearer token authentication
security_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db) # Inject the database session
) -> User:
    """Verifies the JWT and returns the User model object."""
    
    token = credentials.credentials 
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # NEW: Fetch the user object from the database using the email (username)
    user = db.query(User).filter(User.email == username).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user # Return the full User object