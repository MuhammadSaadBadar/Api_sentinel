import time
from urllib import response 
import httpx

async def fetch_endpoint(url:str, method:str = "GET", headers:dict = None) -> dict:
    """fetch an enDpoint and return its response metadata"""
    start_time= time.pref_counter()
    
    async with httpx.AsyncCleint(timeout=10.0,follow_redirects=True)as client:
        try:
            resonse = await client.request(method,url,headers=headers)
            duration_ms = (time.pref_counter() - start_time) * 1000
            
            #attempt to parse
            try:
                body= response.json()
                json_error=None
            except ValueError:
                body = None
                json_error = "Response body is not valid JSON"
             
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
            