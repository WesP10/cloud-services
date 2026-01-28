"""Authentication API endpoints."""

import logging
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status, Request

from ..models import TokenResponse, UserInfo
from ..auth.auth_service import authenticate_user, create_access_token
from ..auth.dependencies import get_current_user
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: Request):
    """
    Login with username and password.

    Accepts either JSON {"username": "..", "password": ".."} or form data (x-www-form-urlencoded).

    Returns JWT access token.
    """
    # Try parsing JSON payload first
    username = None
    password = None

    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
    else:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

    logger.info(f"[LOGIN] Received login request for username: {username}")

    if not username or not password:
        logger.error("[LOGIN] Missing username or password in request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )

    user = authenticate_user(username, password)

    if not user:
        logger.error(f"[LOGIN] Authentication failed for username: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"[LOGIN] Authentication successful for username: {username}")

    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    """
    return UserInfo(
        username=current_user["username"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
    )
