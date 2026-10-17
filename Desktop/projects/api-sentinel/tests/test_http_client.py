import pytest
import httpx
import respx
from api_sentinel.http_client import fetch_endpoint

# Tell pytest to run these as async functions
pytestmark = pytest.mark.asyncio

async def test_successful_json_fetch():
    with respx.mock:
        respx.get("https://api.example.com/products").mock(
            return_value=httpx.Response(
                200, json={"id": 1, "name": "Keyboard"}
            )
        )
        
        result = await fetch_endpoint("https://api.example.com/products")
    
    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["body"] == {"id": 1, "name": "Keyboard"}
    assert result["json_error"] is None
    assert result["duration_ms"] >= 0

async def test_invalid_json_response():
    with respx.mock:
        respx.get("https://api.example.com/broken").mock(
            return_value=httpx.Response(200, text="<html>Not JSON</html>")
        )
        
        result = await fetch_endpoint("https://api.example.com/broken")
    
    assert result["success"] is True
    assert result["body"] is None
    assert result["json_error"] == "Response is not valid JSON"

async def test_network_timeout():
    with respx.mock:
        respx.get("https://api.example.com/slow").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        
        result = await fetch_endpoint("https://api.example.com/slow")
        
    assert result["success"] is False
    assert result["status_code"] is None
    assert "Network error" in result["json_error"]