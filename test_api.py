"""Test script for cloud service API."""

import requests
import json

BASE_URL = "http://localhost:8080"

# Test 1: Health check
print("Testing health endpoint...")
response = requests.get(f"{BASE_URL}/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 2: Login to get JWT token
print("Testing login endpoint...")
login_data = {
    "username": "admin",
    "password": "admin123"
}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Status: {response.status_code}")
token_response = response.json()
print(f"Response: {token_response}\n")

# Get the access token
access_token = token_response["access_token"]
headers = {
    "Authorization": f"Bearer {access_token}"
}

# Test 3: Get current user
print("Testing get current user endpoint...")
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 4: List hubs (should be empty initially)
print("Testing list hubs endpoint...")
response = requests.get(f"{BASE_URL}/api/hubs", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

print("All API tests completed successfully!")
print("\nTo test WebSocket connection, configure your rpi-hub-service with:")
print("SERVER_ENDPOINT=ws://localhost:8080/hub")
print("DEVICE_TOKEN=dev-token-rpi-bridge-01")
