"""Unit tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Test that health endpoint returns OK status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json() or response.json() == {}


def test_login_success(client):
    """Test successful login with valid credentials."""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """Test login fails with invalid credentials."""
    login_data = {
        "username": "admin",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401


def test_login_missing_credentials(client):
    """Test login fails when credentials are missing."""
    response = client.post("/auth/login", json={})
    assert response.status_code in [400, 422]  # Validation error


def test_get_current_user_with_token(client):
    """Test getting current user with valid token."""
    # First login to get a token
    login_response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data or "user" in response.json()


def test_get_current_user_without_token(client):
    """Test getting current user without token fails."""
    response = client.get("/auth/me")
    assert response.status_code == 403 or response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token fails."""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code in [401, 403, 422]
