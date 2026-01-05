"""Authentication API endpoints."""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from ..models import TokenResponse, UserInfo
from ..auth.auth_service import authenticate_user, create_access_token
from ..auth.dependencies import get_current_user
from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with username and password.
    
    Returns JWT access token.
    
    Use the 'Authorize' button in Swagger UI to test:
    - Username: admin
    - Password: admin123
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
