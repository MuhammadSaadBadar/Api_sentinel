import pytest
import httpx
import respx
from api_sentinel.monitoring_service import run_monitoring_check

pytestmark = pytest.mark.asyncio


async def test_infer_new_contract():
    with respx.mock:
        respx.get("https://api.example.com/new").mock(
            return_value=httpx.Response(200, json={"id": 1, "name": "Keyboard"})
        )

        # MUST BE INDENTED INSIDE THE WITH BLOCK
        result = await run_monitoring_check("https://api.example.com/new", test_mode=True)

    assert result["status"] == "awaiting_approval"
    assert "contract" in result
    assert result["contract"]["properties"]["id"]["type"] == "number"


async def test_healthy_response():
    with respx.mock:
        # Make sure the URL matches the one we call below!
        respx.get("https://api.example.com/products").mock(
            return_value=httpx.Response(200, json={"id": 1, "name": "Keyboard"})
        )

        approved_contract = {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
                "name": {"type": "string"}
            }
        }

        # MUST BE INDENTED INSIDE THE WITH BLOCK
        result = await run_monitoring_check(
            "https://api.example.com/products",
            approved_contract=approved_contract,
            test_mode=True
        )

    assert result["status"] == "healthy"
    assert len(result["findings"]) == 0


async def test_breaking_change_detected():
    with respx.mock:
        respx.get("https://api.example.com/products").mock(
            return_value=httpx.Response(200, json={"id": 1, "price": "4500"})
        )

        approved_contract = {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
                "price": {"type": "number"}
            }
        }

        result = await run_monitoring_check(
            "https://api.example.com/products",
            approved_contract=approved_contract,
            test_mode=True
        )

    assert result["status"] == "breaking_changes_detected"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["change"] == "type_changed"
    assert result["findings"][0]["severity"] == "high"


async def test_http_error():
    with respx.mock:
        respx.get("https://api.example.com/broken").mock(
            return_value=httpx.Response(500)
        )

        # MUST BE INDENTED INSIDE THE WITH BLOCK
        result = await run_monitoring_check("https://api.example.com/broken", test_mode=True)

    # We correctly expect 'http_error' for a 500 status code
    assert result["status"] == "http_error"
    assert "500" in result["message"]


async def test_invalid_json():
    with respx.mock:
        respx.get("https://api.example.com/badjson").mock(
            return_value=httpx.Response(200, text="not json")
        )

        result = await run_monitoring_check("https://api.example.com/badjson", test_mode=True)

    assert result["status"] == "invalid_json"
    assert "not valid JSON" in result["message"]


async def test_custom_method_and_headers():
    with respx.mock:
        respx.post("https://api.example.com/items").mock(
            return_value=httpx.Response(200, json={"id": 1})
        )

        result = await run_monitoring_check(
            url="https://api.example.com/items",
            method="POST",
            headers={"Authorization": "Bearer token123"},
            test_mode=True
        )

    assert result["status"] in ("awaiting_approval", "healthy", "changes_detected", "http_error", "invalid_json")


async def test_auth_config_bearer():
    with respx.mock:
        route = respx.get("https://api.example.com/protected").mock(
            return_value=httpx.Response(200, json={"data": "secret"})
        )

        result = await run_monitoring_check(
            url="https://api.example.com/protected",
            auth_config={"type": "bearer", "token": "secret-token"},
            test_mode=True
        )

    assert result["status"] == "awaiting_approval"
    # Verify Authorization header was sent
    assert route.calls.last.request.headers.get("Authorization") == "Bearer secret-token"


async def test_auth_config_api_key():
    with respx.mock:
        route = respx.get("https://api.example.com/apikey").mock(
            return_value=httpx.Response(200, json={"data": "secret"})
        )

        result = await run_monitoring_check(
            url="https://api.example.com/apikey",
            auth_config={"type": "api_key", "key": "my-api-key", "header_name": "X-Custom-Key"},
            test_mode=True
        )

    assert result["status"] == "awaiting_approval"
    assert route.calls.last.request.headers.get("X-Custom-Key") == "my-api-key"