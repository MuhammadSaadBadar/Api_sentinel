import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["TEST_MODE"] = "true"

from api_sentinel.main import app
from api_sentinel.db import Base, get_db, User
from api_sentinel.auth import hash_password, verify_password, create_access_token, decode_token

# Create a shared in-memory DB for tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the DB dependency in the app
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_jwt_token_creation_and_decoding():
    """Test JWT token creation and decoding."""
    data = {"sub": "1", "username": "testuser", "role": "admin"}
    token = create_access_token(data)
    
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["username"] == "testuser"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_user():
    """Test user creation."""
    from api_sentinel.auth import create_user
    from api_sentinel.db import SessionLocal
    
    db = TestingSessionLocal()
    try:
        user = create_user(db, "testuser", "password123", "viewer")
        assert user.id is not None
        assert user.username == "testuser"
        assert user.role == "viewer"
        assert user.is_active is True
        assert verify_password("password123", user.password_hash)
    finally:
        db.close()


def test_register_endpoint():
    """Test user registration endpoint."""
    response = client.post("/auth/register", json={
        "username": "newuser",
        "password": "password123",
        "role": "viewer"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "viewer"
    assert data["is_active"] is True


def test_register_duplicate_user():
    """Test registering duplicate user fails."""
    client.post("/auth/register", json={
        "username": "dupuser",
        "password": "password123",
        "role": "viewer"
    })
    response = client.post("/auth/register", json={
        "username": "dupuser",
        "password": "password123",
        "role": "viewer"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success():
    """Test successful login."""
    # Register user first
    client.post("/auth/register", json={
        "username": "loginuser",
        "password": "password123",
        "role": "viewer"
    })
    
    # Login
    response = client.post("/auth/login", json={
        "username": "loginuser",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure():
    """Test failed login with wrong password."""
    client.post("/auth/register", json={
        "username": "failuser",
        "password": "password123",
        "role": "viewer"
    })
    
    response = client.post("/auth/login", json={
        "username": "failuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_refresh_token():
    """Test token refresh."""
    # Register and login
    client.post("/auth/register", json={
        "username": "refreshuser",
        "password": "password123",
        "role": "viewer"
    })
    login_resp = client.post("/auth/login", json={
        "username": "refreshuser",
        "password": "password123"
    })
    refresh_token = login_resp.json()["refresh_token"]
    
    # Refresh
    response = client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New refresh token is returned (may be same if created in same second)


def test_get_me():
    """Test /auth/me endpoint."""
    # Register and login
    client.post("/auth/register", json={
        "username": "meuser",
        "password": "password123",
        "role": "admin"
    })
    login_resp = client.post("/auth/login", json={
        "username": "meuser",
        "password": "password123"
    })
    access_token = login_resp.json()["access_token"]
    
    # Get current user
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    assert data["role"] == "admin"


def test_invalid_token():
    """Test invalid token rejection."""
    response = client.get("/auth/me", headers={
        "Authorization": "Bearer invalid.token.here"
    })
    assert response.status_code == 401


def test_expired_token():
    """Test expired token rejection."""
    from datetime import timedelta
    # Create token with negative expiry (already expired)
    expired_token = create_access_token({"sub": "1", "username": "test"}, expires_delta=timedelta(seconds=-1))
    
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {expired_token}"
    })
    assert response.status_code == 401


def test_logout():
    """Test logout endpoint."""
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert "Logged out" in response.json()["message"]


def test_generate_api_key():
    """Test API key generation for endpoint."""
    from api_sentinel.auth import generate_api_key, hash_api_key
    from api_sentinel.db import Endpoint
    from api_sentinel.db import SessionLocal
    
    db = TestingSessionLocal()
    try:
        # Create endpoint with unique URL
        ep = Endpoint(name="Test API Key", url="https://api.example.com/test-api-key-gen", interval_seconds=60)
        db.add(ep)
        db.commit()
        
        # Generate API key
        from api_sentinel.auth import generate_api_key as gen_key
        api_key = gen_key()
        assert api_key.startswith("as_")
        
        # Hash it
        key_hash = hash_api_key(api_key)
        ep.api_key_hash = key_hash
        db.commit()
        
        # Verify
        assert hash_api_key(api_key) == ep.api_key_hash
    finally:
        db.close()