"""Pytest configuration and fixtures for cloud-services tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app
from config import get_settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Create mock settings for tests."""
    with patch('config.get_settings') as mock:
        settings = MagicMock()
        settings.SECRET_KEY = "test-secret-key-for-testing-only"
        settings.ALGORITHM = "HS256"
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock.return_value = settings
        yield mock
