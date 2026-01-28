"""Pytest configuration and fixtures for cloud-services tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Ensure package imports work by adding project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the app as package module to allow relative imports inside src
from importlib import import_module
main = import_module('src.main')
app = main.app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Create mock settings for tests."""
    with patch('src.config.get_settings') as mock:
        settings = MagicMock()
        settings.SECRET_KEY = "test-secret-key-for-testing-only"
        settings.ALGORITHM = "HS256"
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock.return_value = settings
        yield mock
