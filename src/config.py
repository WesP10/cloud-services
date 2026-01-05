"""Configuration management."""

import logging
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    environment: str = "development"

    # JWT
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # Device Tokens
    device_token_rpi_bridge_01: str = "dev-token-rpi-bridge-01"
    device_token_rpi_bridge_02: str = "dev-token-rpi-bridge-02"

    # CORS - can be string or list
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000"

    @field_validator('cors_origins', mode='after')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    def get_valid_device_tokens(self) -> dict[str, str]:
        """Get mapping of device tokens to hub IDs."""
        return {
            self.device_token_rpi_bridge_01: "rpi-bridge-01",
            self.device_token_rpi_bridge_02: "rpi-bridge-02",
        }


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
        logger.info(f"Settings loaded - device_token_rpi_bridge_01: {_settings.device_token_rpi_bridge_01}")
        logger.info(f"Valid device tokens: {_settings.get_valid_device_tokens()}")
    return _settings
