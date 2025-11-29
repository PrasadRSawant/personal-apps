# tests/test_api_auth.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.user import UserCreate

# Note: 'client' and 'test_db_session' are automatically provided by conftest.py

def test_register_user(client: TestClient, test_db_session: Session):
    """Test successful user registration."""
    user_data = {
        "email": "test@example.com",
        "password": "securepassword123"
    }
    
    # Send a POST request to the registration endpoint
    response = client.post("/auth/basic/register", json=user_data)
    
    assert response.status_code == 201
    assert "User registered successfully." in response.json()['message']
    
    # Verify the user exists in the test database
    db_user = test_db_session.query(User).filter(User.email == user_data['email']).first()
    assert db_user is not None
    assert db_user.auth_method == "Basic"

def test_basic_auth_login_for_access_token(client: TestClient):
    """Test token generation using Query Parameters (to match required client request)."""
    
    # Define credentials (these must match the user registered in a previous or setup step)
    username = "test@example.com"
    password = "securepassword123"
    
    # 1. --- Ensure User Exists (Registration Step) ---
    # This step is CRUCIAL because the test database resets after every function.
    register_data = {
        "email": username, 
        "password": password
    }
    register_response = client.post("/auth/basic/register", json=register_data)
    # Check that registration was successful before proceeding
    assert register_response.status_code in [200, 201], f"Setup Failed: Registration failed for user {username}"
    
    
    # 2. --- Perform Login using Query Parameters ---
    # Construct the URL with credentials in the query string (matching the curl command)
    # The URL must be properly encoded for special characters, but TestClient handles simple strings.
    login_url = f"/auth/basic/token?username={username}&password={password}"

    # Make the request as a POST with query parameters, no data/JSON body
    response = client.post(
        login_url,
        # The API is configured to ignore headers and body,
        # so we rely solely on the URL query string.
    )
    
    # 3. --- Assertions ---
    # Check the status code and response structure
    assert response.status_code == 200, f"Login Failed. Status: {response.status_code}, Detail: {response.json()}"
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_protected_route_unauthorized(client: TestClient):
    """Test accessing a protected route without a token."""
    # Assuming /tools/files/to-base64 is a protected route
    response = client.post("/tools/files/to-base64")
    
    # Must fail with 401 Unauthorized
    assert response.status_code == 401
    assert "Not authenticated" in response.json()['detail']