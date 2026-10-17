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
        result = await run_monitoring_check("https://api.example.com/new")
        
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
            approved_contract=approved_contract
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
            approved_contract=approved_contract
        )
        
    assert result["status"] == "changes_detected"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["change"] == "type_changed"

async def test_http_error():
    with respx.mock:
        respx.get("https://api.example.com/broken").mock(
            return_value=httpx.Response(500)
        )
        
        # MUST BE INDENTED INSIDE THE WITH BLOCK
        result = await run_monitoring_check("https://api.example.com/broken")
        
    # We correctly expect 'http_error' for a 500 status code
    assert result["status"] == "http_error"
    assert "HTTP 500" in result["message"]