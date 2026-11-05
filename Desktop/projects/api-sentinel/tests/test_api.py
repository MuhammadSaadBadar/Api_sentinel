import os
os.environ["TEST_MODE"] = "true"

import pytest
import httpx
import respx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api_sentinel.main import app
from api_sentinel.db import Base, get_db, Endpoint, Baseline

# Create a fresh engine for each test run
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
# Endpoint Tests
# ============================================================

def test_create_endpoint(test_client):
    response = test_client.post("/endpoints", json={
        "name": "Test API",
        "url": "https://api.example.com/test-create",
        "interval_seconds": 60
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test API"
    assert data["method"] == "GET"
    assert data["headers"] == {}
    assert data["query_params"] == {}
    assert data["timeout_seconds"] == 30

    # Try to create duplicate
    response = test_client.post("/endpoints", json={
        "name": "Test API",
        "url": "https://api.example.com/test-create",
        "interval_seconds": 60
    })
    assert response.status_code == 400


def test_create_endpoint_with_full_config(test_client):
    response = test_client.post("/endpoints", json={
        "name": "Full Config API",
        "url": "https://api.example.com/full-config",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "query_params": {"version": "v1"},
        "auth_config": {"type": "bearer", "token": "secret"},
        "timeout_seconds": 60,
        "expected_status_codes": [200, 201],
        "response_format": "json",
        "interval_seconds": 120
    })
    assert response.status_code == 201
    data = response.json()
    assert data["method"] == "POST"
    assert data["headers"] == {"Content-Type": "application/json"}
    assert data["query_params"] == {"version": "v1"}
    assert data["auth_config"] == {"type": "bearer", "token": "secret"}
    assert data["timeout_seconds"] == 60
    assert data["expected_status_codes"] == [200, 201]
    assert data["interval_seconds"] == 120


@respx.mock
def test_approve_baseline(test_client):
    # Register endpoint
    test_client.post("/endpoints", json={
        "name": "Test API",
        "url": "https://api.example.com/test-approve-1"
    })

    # Mock API response
    respx.get("https://api.example.com/test-approve-1").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )

    # Approve baseline
    response = test_client.post("/endpoints/1/approve-baseline")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["contract_json"]["properties"]["id"]["type"] == "number"

    # Approve again (should bump version to 2)
    response = test_client.post("/endpoints/1/approve-baseline")
    assert response.status_code == 200
    assert response.json()["version"] == 2


@respx.mock
def test_approve_baseline_with_full_config(test_client):
    test_client.post("/endpoints", json={
        "name": "Test API",
        "url": "https://api.example.com/test-approve-full-1",
        "method": "POST",
        "headers": {"X-Custom": "value"},
        "auth_config": {"type": "bearer", "token": "test-token"},
    })

    route = respx.post("https://api.example.com/test-approve-full-1").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )

    response = test_client.post("/endpoints/1/approve-baseline")
    assert response.status_code == 200

    # Verify the request was made with correct method and headers
    assert route.calls.last.request.method == "POST"
    assert route.calls.last.request.headers.get("X-Custom") == "value"
    assert route.calls.last.request.headers.get("Authorization") == "Bearer test-token"


def test_list_endpoints(test_client):
    test_client.post("/endpoints", json={"name": "API 1", "url": "https://api.example.com/list-1-1"})
    test_client.post("/endpoints", json={"name": "API 2", "url": "https://api.example.com/list-1-2"})

    response = test_client.get("/endpoints")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_endpoint(test_client):
    create_resp = test_client.post("/endpoints", json={"name": "Test API", "url": "https://api.example.com/get-test"})
    assert create_resp.status_code == 201
    endpoint_id = create_resp.json()["id"]

    response = test_client.get(f"/endpoints/{endpoint_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test API"


def test_update_endpoint(test_client):
    create_resp = test_client.post("/endpoints", json={"name": "Test API", "url": "https://api.example.com/update-test"})
    assert create_resp.status_code == 201
    endpoint_id = create_resp.json()["id"]

    response = test_client.patch(f"/endpoints/{endpoint_id}", json={
        "name": "Updated API",
        "interval_seconds": 120
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated API"
    assert data["interval_seconds"] == 120


def test_delete_endpoint(test_client):
    create_resp = test_client.post("/endpoints", json={"name": "Test API", "url": "https://api.example.com/delete-test"})
    assert create_resp.status_code == 201
    endpoint_id = create_resp.json()["id"]

    response = test_client.delete(f"/endpoints/{endpoint_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = test_client.get(f"/endpoints/{endpoint_id}")
    assert response.status_code == 404


def test_activate_deactivate_endpoint(test_client):
    create_resp = test_client.post("/endpoints", json={"name": "Test API", "url": "https://api.example.com/activate-test"})
    assert create_resp.status_code == 201
    endpoint_id = create_resp.json()["id"]

    # Deactivate
    response = test_client.post(f"/endpoints/{endpoint_id}/deactivate")
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Activate
    response = test_client.post(f"/endpoints/{endpoint_id}/activate")
    assert response.status_code == 200
    assert response.json()["is_active"] == True