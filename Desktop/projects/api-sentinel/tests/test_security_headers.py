"""
Tests for Security Headers Middleware
"""

import os
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api_sentinel.security_headers import SecurityHeadersMiddleware


@pytest.fixture(autouse=True)
def disable_test_mode():
    """Disable TEST_MODE for security headers tests."""
    old_value = os.environ.get("TEST_MODE")
    os.environ["TEST_MODE"] = "false"
    yield
    if old_value is not None:
        os.environ["TEST_MODE"] = old_value
    else:
        os.environ.pop("TEST_MODE", None)


def create_test_app():
    """Create a test app with security headers middleware."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}
    
    app.add_middleware(SecurityHeadersMiddleware)
    return app


@pytest.fixture
def client():
    app = create_test_app()
    return TestClient(app)


def test_csp_header_present(client):
    """Test Content-Security-Policy header is present."""
    response = client.get("/test")
    assert response.status_code == 200
    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "style-src" in csp
    assert "script-src" in csp
    # Check CDN domains allowed
    assert "cdn.jsdelivr.net" in csp
    assert "unpkg.com" in csp


def test_hsts_header_present(client):
    """Test Strict-Transport-Security header is present."""
    response = client.get("/test")
    assert response.status_code == 200
    assert "Strict-Transport-Security" in response.headers
    hsts = response.headers["Strict-Transport-Security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
    assert "preload" in hsts


def test_x_frame_options(client):
    """Test X-Frame-Options header."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"


def test_x_content_type_options(client):
    """Test X-Content-Type-Options header."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_referrer_policy(client):
    """Test Referrer-Policy header."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_permissions_policy(client):
    """Test Permissions-Policy header."""
    response = client.get("/test")
    assert response.status_code == 200
    assert "Permissions-Policy" in response.headers
    policy = response.headers["Permissions-Policy"]
    assert "accelerometer=()" in policy
    assert "camera=()" in policy
    assert "geolocation=()" in policy


def test_cross_origin_policies(client):
    """Test Cross-Origin headers."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"


def test_server_header_removed(client):
    """Test Server header is removed."""
    response = client.get("/test")
    assert response.status_code == 200
    assert "server" not in response.headers
    assert "Server" not in response.headers


def test_csp_allows_cdn_domains(client):
    """Test CSP allows required CDN domains."""
    response = client.get("/test")
    csp = response.headers["Content-Security-Policy"]
    # Pico.css CDN
    assert "cdn.jsdelivr.net" in csp
    # HTMX CDN
    assert "unpkg.com" in csp
    # Allow inline styles/scripts for HTMX
    assert "'unsafe-inline'" in csp


def test_hsts_includes_subdomains_and_preload(client):
    """Test HSTS includes subdomains and preload."""
    response = client.get("/test")
    hsts = response.headers["Strict-Transport-Security"]
    assert "includeSubDomains" in hsts
    assert "preload" in hsts


def test_frame_options_deny(client):
    """Test X-Frame-Options is DENY."""
    response = client.get("/test")
    assert response.headers["X-Frame-Options"] == "DENY"


def test_content_type_options_nosniff(client):
    """Test X-Content-Type-Options is nosniff."""
    response = client.get("/test")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_referrer_policy_strict_origin(client):
    """Test Referrer-Policy is strict-origin-when-cross-origin."""
    response = client.get("/test")
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_permissions_policy_blocks_sensitive_features(client):
    """Test Permissions-Policy blocks sensitive features."""
    response = client.get("/test")
    policy = response.headers["Permissions-Policy"]
    sensitive = ["accelerometer", "camera", "geolocation", "gyroscope", 
                 "magnetometer", "microphone", "payment", "usb"]
    for feature in sensitive:
        assert f"{feature}=()" in policy


def test_cross_origin_opener_policy(client):
    """Test Cross-Origin-Opener-Policy is same-origin."""
    response = client.get("/test")
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"


def test_cross_origin_resource_policy(client):
    """Test Cross-Origin-Resource-Policy is same-origin."""
    response = client.get("/test")
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"