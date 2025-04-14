import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from jose import JWTError, jwt
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Environment variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-very-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# OAuth2 scheme for Swagger UI ("Authorize" button)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

class Token(BaseModel):
    """Response model for JWT token."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Data extracted from JWT token."""
    username: Optional[str] = None

class LoginRequest(BaseModel):
    """Request model for login endpoint."""
    username: str
    password: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, expected_password: str) -> bool:
    """
    Simple password check (no hashing for now).
    """
    return plain_password == expected_password

def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate user against environment credentials.
    """
    if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD):
        return True
    return False

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependency to get current user from JWT token.
    Raises HTTP 401 if token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("JWT token missing 'sub' claim.")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise credentials_exception
    if token_data.username != ADMIN_USERNAME:
        logger.warning("JWT token username does not match admin username.")
        raise credentials_exception
    return token_data.username 