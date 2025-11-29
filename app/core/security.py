# app/core/security.py

from datetime import datetime, timedelta, UTC
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.core.config import settings

# Password Hashing Setup
# 🚨 CHANGE: Switch from "bcrypt" to "argon2" 🚨
# Argon2 is a modern algorithm that handles long passwords without the 72-byte limit.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# ----------------------------------------------------
# ⚠️ REMOVE the _truncate_password helper function
# ----------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    
    # Argon2 handles the full length of plain_password
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password using Argon2.
    """
    
    # Argon2 handles the full length of the password
    return pwd_context.hash(password)

# JWT Token Functions (Remain the same)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None