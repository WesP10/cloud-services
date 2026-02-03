"""Authentication service with JWT and mock users."""

from datetime import datetime, timedelta
from typing import Optional
import logging
import jwt
import bcrypt
import json
from pathlib import Path
from fastapi import HTTPException, status

from ..config import get_settings

logger = logging.getLogger(__name__)


# User database loaded from JSON file
# Fallback demo users for development if file not found
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": "$2b$12$Bsq66/d3TpJAm88m7pUDjOKt9d.zDWL//Ndo.M75MB8U.HUnf28Ue",  # admin123
    },
    "developer": {
        "username": "developer",
        "email": "dev@example.com",
        "full_name": "Developer User",
        "hashed_password": "$2b$12$3zeCNtJ3l7jPngfCu0ehsOEpr0.0nk2eInMVIXZNfVA5YVmRG5xG.",  # dev123
    },
}

_users_cache = None

def load_users() -> dict:
    """Load users from JSON file or return demo users."""
    global _users_cache
    
    if _users_cache is not None:
        return _users_cache
    
    settings = get_settings()
    users_file = Path(settings.users_file_path)
    
    if users_file.exists():
        try:
            logger.info(f"Loading users from {users_file}")
            with open(users_file, 'r') as f:
                data = json.load(f)
                # Handle both raw dict and wrapped format from generator
                if "MOCK_USERS" in data:
                    _users_cache = data["MOCK_USERS"]
                else:
                    _users_cache = data
                logger.info(f"Loaded {len(_users_cache)} users from file")
                return _users_cache
        except Exception as e:
            logger.error(f"Error loading users from {users_file}: {e}")
            logger.warning("Falling back to demo users")
            _users_cache = DEMO_USERS
            return _users_cache
    else:
        logger.warning(f"Users file not found at {users_file}")
        logger.warning("Using demo users (admin/developer)")
        _users_cache = DEMO_USERS
        return _users_cache


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    logger.debug("[VERIFY] Verifying password")
    
    # Truncate password to 72 bytes to comply with bcrypt limitations
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    
    try:
        result = bcrypt.checkpw(password_bytes, hashed_bytes)
        logger.info(f"[VERIFY] Verification {'success' if result else 'failure'}")
        return result
    except Exception as e:
        logger.error(f"[VERIFY] Verification error: {e}")
        return False


def get_user(username: str) -> Optional[dict]:
    """Get user from database."""
    users = load_users()
    return users.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with username and password."""
    logger.info(f"[AUTH] Authenticating user: {username}")
    
    user = get_user(username)
    if not user:
        logger.error(f"[AUTH] User not found: {username}")
        users = load_users()
        logger.info(f"[AUTH] Available users: {list(users.keys())}")
        return None
    
    logger.info(f"[AUTH] User found: {username}")
    logger.debug("[AUTH] Stored password hash present")
    
    if not verify_password(password, user["hashed_password"]):
        logger.error(f"[AUTH] Password verification failed for user: {username}")
        return None
    
    logger.info(f"[AUTH] Password verified successfully for user: {username}")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and verify JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def verify_device_token(device_token: str) -> Optional[str]:
    """Verify device token and return hub ID."""
    settings = get_settings()
    valid_tokens = settings.get_valid_device_tokens()
    
    # Debug logging
    logger.info(f"Verifying device token: {device_token[:10]}...")
    logger.info(f"Valid tokens: {list(valid_tokens.keys())}")
    
    hub_id = valid_tokens.get(device_token)
    if hub_id:
        logger.info(f"Token verified successfully for hub: {hub_id}")
    else:
        logger.warning(f"Token verification failed. Token not found in valid_tokens")
    
    return hub_id
