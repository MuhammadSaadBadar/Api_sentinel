import os
os.environ["TEST_MODE"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api_sentinel.main import app
from api_sentinel.db import Base, get_db, User
from api_sentinel.auth import hash_password, verify_password, create_access_token, decode_token


def create_test_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )


def create_test_session_local(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_client():
    """Create a test client with fresh database for each test."""
    engine = create_test_engine()
    TestingSessionLocal = create_test_session_local(engine)
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


# ============================================================
# Auth Tests
# ============================================================

def test_password_hashing(test_client):
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_jwt_token_creation_and_decoding(test_client):
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


def test_create_user(test_client):
    """Test user creation."""
    from api_sentinel.auth import create_user
    from api_sentinel.db import SessionLocal as RealSessionLocal
    from api_sentinel.db import get_db as real_get_db
    
    # Use the test database
    from api_sentinel.main import app
    from api_sentinel.db import get_db
    
    # Get the overridden session
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    
    # Get the engine from the app's dependency override
    # We can't easily access it, so just use the test_client's app
    # For this test, we'll just use the auth module directly with a new session
    
    # Create a temporary engine for this test
    engine = create_test_engine()
    TestingSessionLocal = create_test_session_local(engine)
    Base.metadata.create_all(bind=engine)
    
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
        Base.metadata.drop_all(bind=engine)


def test_register_endpoint(test_client):
    """Test user registration endpoint."""
    response = test_client.post("/auth/register", json={
        "username": "newuser",
        "password": "password123",
        "role": "viewer"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "viewer"
    assert data["is_active"] is True


def test_register_duplicate_user(test_client):
    """Test registering duplicate user fails."""
    test_client.post("/auth/register", json={
        "username": "dupuser",
        "password": "password123",
        "role": "viewer"
    })
    response = test_client.post("/auth/register", json={
        "username": "dupuser",
        "password": "password123",
        "role": "viewer"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(test_client):
    """Test successful login."""
    # Register user first
    test_client.post("/auth/register", json={
        "username": "loginuser",
        "password": "password123",
        "role": "viewer"
    })
    
    # Login
    response = test_client.post("/auth/login", json={
        "username": "loginuser",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(test_client):
    """Test failed login with wrong password."""
    test_client.post("/auth/register", json={
        "username": "failuser",
        "password": "password123",
        "role": "viewer"
    })
    
    response = test_client.post("/auth/login", json={
        "username": "failuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_refresh_token(test_client):
    """Test token refresh."""
    # Register and login
    test_client.post("/auth/register", json={
        "username": "refreshuser",
        "password": "password123",
        "role": "viewer"
    })
    login_resp = test_client.post("/auth/login", json={
        "username": "refreshuser",
        "password": "password123"
    })
    refresh_token = login_resp.json()["refresh_token"]
    
    # Refresh
    response = test_client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New refresh token is returned (may be same if created in same second)


def test_get_me(test_client):
    """Test /auth/me endpoint."""
    # Register and login
    test_client.post("/auth/register", json={
        "username": "meuser",
        "password": "password123",
        "role": "admin"
    })
    login_resp = test_client.post("/auth/login", json={
        "username": "meuser",
        "password": "password123"
    })
    access_token = login_resp.json()["access_token"]
    
    # Get current user
    response = test_client.get("/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    assert data["role"] == "admin"


def test_invalid_token(test_client):
    """Test invalid token rejection."""
    response = test_client.get("/auth/me", headers={
        "Authorization": "Bearer invalid.token.here"
    })
    assert response.status_code == 401


def test_expired_token(test_client):
    """Test expired token rejection."""
    from datetime import timedelta
    # Create token with negative expiry (already expired)
    expired_token = create_access_token({"sub": "1", "username": "test"}, expires_delta=timedelta(seconds=-1))
    
    response = test_client.get("/auth/me", headers={
        "Authorization": f"Bearer {expired_token}"
    })
    assert response.status_code == 401


def test_logout(test_client):
    """Test logout endpoint."""
    response = test_client.post("/auth/logout")
    assert response.status_code == 200
    assert "Logged out" in response.json()["message"]


def test_generate_api_key(test_client):
    """Test API key generation for endpoint."""
    from api_sentinel.auth import generate_api_key, hash_api_key
    
    # Test key generation
    api_key = generate_api_key()
    assert api_key.startswith("as_")
    
    # Test hashing
    key_hash = hash_api_key(api_key)
    assert hash_api_key(api_key) == key_hash