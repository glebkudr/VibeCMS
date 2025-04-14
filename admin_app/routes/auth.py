from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from admin_app.core.auth import Token, authenticate_user, create_access_token, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token, tags=["Auth"], summary="Login and get JWT token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return a JWT access token.
    Credentials are checked against environment variables.
    """
    if not authenticate_user(form_data.username, form_data.password):
        logger.info(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    logger.info(f"User '{form_data.username}' logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer"} 