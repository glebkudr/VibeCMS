from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from admin_app.core.auth import Token, create_access_token, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from admin_app.core.admin_password import verify_admin_password, change_admin_password
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token, tags=["Auth"], summary="Login and get JWT token")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return a JWT access token.
    Credentials are checked against DB hash or environment variables.
    """
    db = request.app.state.mongo_db
    if not db:
        logger.error("Database connection not available for login")
        raise HTTPException(status_code=503, detail="Database not available")
    if form_data.username != "admin" or not await verify_admin_password(db, form_data.password):
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

@router.post("/change-password", tags=["Auth"], summary="Change admin password")
async def change_password(request: Request, data: dict = Body(...)):
    """
    Change admin password. Requires current and new password.
    """
    db = request.app.state.mongo_db
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Both current_password and new_password are required")
    ok = await change_admin_password(db, current_password, new_password)
    if not ok:
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    return {"success": True, "message": "Password changed successfully"} 