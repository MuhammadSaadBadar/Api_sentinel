import time
from typing import Mapping

import httpx

async def fetch_endpoint(
    url: str,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
) -> dict:
    """fetch an enDpoint and return its response metadata"""
    start_time= time.perf_counter()
    
    async with httpx.AsyncClient(timeout=10.0,follow_redirects=True)as client:
        try:
            response = await client.request(method, url, headers=headers)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            #attempt to parse
            try:
                body= response.json()
                json_error=None
            except ValueError:
                body = None
                json_error = "Response is not valid JSON"
             
            return{
                "success": True,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms,2),
                "body": body,
                "json_error": json_error,
                "headers": dict(response.headers)
            }   
            
        except httpx.RequestError as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "status_code": None,
                "duration_ms": round(duration_ms, 2),
                "body": None,
                "json_error": f"Network error : {str(exc)}",
                "headers": {}
            }
            