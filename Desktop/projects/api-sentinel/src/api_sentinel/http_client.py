import time
import ipaddress
import logging
from typing import Mapping, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB
SENSITIVE_HEADER_KEYS = {"authorization", "api-key", "apikey", "x-api-key", "token", "secret", "password"}


def is_safe_url(url: str, allow_hostnames: bool = True) -> bool:
    """Validate URL to prevent SSRF attacks."""
    try:
        parsed = urlparse(url)
        
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ("http", "https"):
            return False
            
        # Resolve hostname to IP
        hostname = parsed.hostname
        if not hostname:
            return False
            
        try:
            ip = ipaddress.ip_address(hostname)
        except ValueError:
            # Hostname is not an IP
            if not allow_hostnames:
                logger.warning(f"Blocked URL with hostname (not IP): {url}")
                return False
            logger.warning(f"URL uses hostname (not IP): {url}. Consider using IP addresses for better security.")
            return True
            
        # Block private, loopback, link-local, multicast, reserved
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            logger.warning(f"Blocked unsafe URL (private/reserved IP): {url}")
            return False
            
        # Block cloud metadata endpoints (common SSRF targets)
        if ip == ipaddress.ip_address("169.254.169.254"):  # AWS/GCP/Azure metadata
            logger.warning(f"Blocked cloud metadata URL: {url}")
            return False
            
        return True
    except Exception as e:
        logger.warning(f"URL validation failed for {url}: {e}")
        return False


def mask_sensitive_headers(headers: Mapping[str, str]) -> dict:
    """Mask sensitive header values for logging."""
    masked = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADER_KEYS:
            masked[key] = "***MASKED***"
        else:
            masked[key] = value
    return masked


async def fetch_endpoint(
    url: str,
    method: str = "GET",
    headers: Optional[Mapping[str, str]] = None,
    query_params: Optional[Mapping[str, str]] = None,
    timeout_seconds: int = 30,
    expected_status_codes: Optional[list[int]] = None,
    max_response_size: int = DEFAULT_MAX_RESPONSE_SIZE,
    allow_hostnames: bool = True,
) -> dict:
    """
    Fetch an endpoint and return its response metadata.
    
    Args:
        url: The URL to fetch
        method: HTTP method (GET, POST, etc.)
        headers: Request headers
        query_params: Query parameters
        timeout_seconds: Request timeout
        expected_status_codes: List of acceptable status codes
        max_response_size: Maximum response body size in bytes
        allow_hostnames: Allow hostnames (not just IPs) - for testing
        
    Returns:
        Dict with response metadata
    """
    if not is_safe_url(url, allow_hostnames=allow_hostnames):
        return {
            "success": False,
            "status_code": None,
            "duration_ms": 0,
            "body": None,
            "json_error": "URL blocked by security policy (SSRF protection)",
            "headers": {},
        }

    if expected_status_codes is None:
        expected_status_codes = [200]

    start_time = time.perf_counter()
    safe_headers = dict(headers) if headers else {}
    
    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=True,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    ) as client:
        try:
            # Build request
            request = client.build_request(
                method=method,
                url=url,
                headers=safe_headers,
                params=query_params,
            )
            
            # Send request
            response = await client.send(request, stream=True)
            
            # Read response with size limit
            content = b""
            async for chunk in response.aiter_bytes():
                content += chunk
                if len(content) > max_response_size:
                    await response.aclose()
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                        "body": None,
                        "json_error": f"Response size exceeds limit ({max_response_size} bytes)",
                        "headers": mask_sensitive_headers(response.headers),
                    }
            
            # Now read the content properly
            response._content = content
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Check status code
            if response.status_code not in expected_status_codes:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "body": None,
                    "json_error": f"Unexpected status code: {response.status_code} (expected: {expected_status_codes})",
                    "headers": mask_sensitive_headers(response.headers),
                }
            
            # Attempt to parse JSON
            try:
                body = response.json()
                json_error = None
            except ValueError:
                body = None
                json_error = "Response is not valid JSON"
            
            return {
                "success": True,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "body": body,
                "json_error": json_error,
                "headers": mask_sensitive_headers(response.headers),
            }
            
        except httpx.TimeoutException as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Timeout fetching {url}: {exc}")
            return {
                "success": False,
                "status_code": None,
                "duration_ms": round(duration_ms, 2),
                "body": None,
                "json_error": f"Network error: {str(exc)}",
                "headers": {},
            }
        except httpx.RequestError as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Network error fetching {url}: {exc}")
            return {
                "success": False,
                "status_code": None,
                "duration_ms": round(duration_ms, 2),
                "body": None,
                "json_error": f"Network error: {str(exc)}",
                "headers": {},
            }
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Unexpected error fetching {url}: {exc}")
            return {
                "success": False,
                "status_code": None,
                "duration_ms": round(duration_ms, 2),
                "body": None,
                "json_error": f"Network error: {str(exc)}",
                "headers": {},
            }