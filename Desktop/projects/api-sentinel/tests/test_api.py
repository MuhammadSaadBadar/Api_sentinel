import pytest
import httpx
import respx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api_sentinel.main import app
from api_sentinel.db import Base, get_db, Endpoint, Baseline

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

@pytest.fixture(autouse=True)
def clean_db():
    """Wipe the DB before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_create_endpoint():
    response = client.post("/endpoints", json={
        "name": "Test API",
        "url": "https://api.example.com/test",
        "interval_seconds": 60
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Test API"

    # Try to create duplicate
    response = client.post("/endpoints", json={
        "name": "Test API",
        "url": "https://api.example.com/test",
        "interval_seconds": 60
    })
    assert response.status_code == 400

@respx.mock
def test_approve_baseline():
    # Register endpoint
    client.post("/endpoints", json={
        "name": "Test API",
        "url": "https://api.example.com/test"
    })
    
    # Mock API response
    respx.get("https://api.example.com/test").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    
    # Approve baseline
    response = client.post("/endpoints/1/approve-baseline")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["contract_json"]["properties"]["id"]["type"] == "number"

    # Approve again (should bump version to 2)
    response = client.post("/endpoints/1/approve-baseline")
    assert response.status_code == 200
    assert response.json()["version"] == 2