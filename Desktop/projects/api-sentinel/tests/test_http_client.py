import pytest
import httpx
import respx
from api_sentinel.http_client import fetch_endpoint, is_safe_url


@pytest.mark.asyncio
async def test_successful_json_fetch():
    with respx.mock:
        respx.get("https://api.example.com/products").mock(
            return_value=httpx.Response(
                200, json={"id": 1, "name": "Keyboard"}
            )
        )

        result = await fetch_endpoint("https://api.example.com/products", test_mode=True)

    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["body"] == {"id": 1, "name": "Keyboard"}
    assert result["json_error"] is None
    assert result["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_invalid_json_response():
    with respx.mock:
        respx.get("https://api.example.com/broken").mock(
            return_value=httpx.Response(200, text="<html>Not JSON</html>")
        )

        result = await fetch_endpoint("https://api.example.com/broken", test_mode=True)

    assert result["success"] is True
    assert result["body"] is None
    assert result["json_error"] == "Response is not valid JSON"


@pytest.mark.asyncio
async def test_network_timeout():
    with respx.mock:
        respx.get("https://api.example.com/slow").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        result = await fetch_endpoint("https://api.example.com/slow", test_mode=True)

    assert result["success"] is False
    assert result["status_code"] is None
    assert "Network error" in result["json_error"]


@pytest.mark.asyncio
async def test_post_request_with_headers_and_query_params():
    with respx.mock:
        # Use a more flexible mock that matches any request to this URL
        respx.post("https://api.example.com/items").mock(
            return_value=httpx.Response(201, json={"id": 2})
        )

        result = await fetch_endpoint(
            url="https://api.example.com/items",
            method="POST",
            headers={"Content-Type": "application/json", "X-Custom": "value"},
            query_params={"filter": "active"},
            expected_status_codes=[200, 201],
            test_mode=True,
        )

    assert result["success"] is True
    assert result["status_code"] == 201


@pytest.mark.asyncio
async def test_unexpected_status_code():
    with respx.mock:
        respx.get("https://api.example.com/error").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )

        result = await fetch_endpoint(
            "https://api.example.com/error",
            expected_status_codes=[200],
            test_mode=True,
        )

    assert result["success"] is False
    assert result["status_code"] == 404
    assert "Unexpected status code: 404" in result["json_error"]


@pytest.mark.asyncio
async def test_custom_expected_status_codes():
    with respx.mock:
        respx.get("https://api.example.com/ok").mock(
            return_value=httpx.Response(201, json={"created": True})
        )

        result = await fetch_endpoint(
            "https://api.example.com/ok",
            expected_status_codes=[200, 201],
            test_mode=True,
        )

    assert result["success"] is True
    assert result["status_code"] == 201


def test_is_safe_url_blocks_private_ips():
    assert is_safe_url("http://127.0.0.1/test") is False
    assert is_safe_url("http://192.168.1.1/test") is False
    assert is_safe_url("http://10.0.0.1/test") is False
    assert is_safe_url("http://169.254.169.254/test") is False  # Cloud metadata


def test_is_safe_url_allows_public_ips():
    assert is_safe_url("https://8.8.8.8/test") is True
    assert is_safe_url("https://1.1.1.1/test") is True


def test_is_safe_url_allows_hostnames():
    # With default allow_hostnames=True
    assert is_safe_url("https://api.example.com/test") is True
    assert is_safe_url("https://google.com/test") is True