"""
Rate Limiting Module

Token bucket algorithm implementation for API rate limiting.
"""

import time
import os
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from threading import Lock
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


def is_test_mode() -> bool:
    """Check if running in test mode."""
    return os.environ.get("TEST_MODE", "false").lower() == "true"


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    
    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.monotonic()
        # Refill tokens based on elapsed time
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_retry_after(self, tokens: int = 1) -> int:
        """Get seconds until enough tokens are available."""
        if self.tokens >= tokens:
            return 0
        needed = tokens - self.tokens
        return int(needed / self.refill_rate) + 1


class InMemoryRateLimiter:
    """In-memory rate limiter with token bucket algorithm."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst: int = 10,
        exempt_paths: Optional[set] = None,
    ):
        self.requests_per_minute = requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.burst = burst
        self.exempt_paths = exempt_paths or {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}
        self.buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()
    
    def _get_client_key(self, request: Request) -> str:
        """Generate rate limit key from request."""
        # Use X-Forwarded-For if behind proxy, otherwise client host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        return f"{client_ip}:{request.url.path}"
    
    def is_exempt(self, request: Request) -> bool:
        """Check if request path is exempt from rate limiting."""
        path = request.url.path
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def check_rate_limit(self, request: Request) -> Tuple[bool, Optional[int], Dict[str, int]]:
        """
        Check if request is within rate limit.
        
        Returns:
            Tuple of (allowed, retry_after_seconds, rate_limit_headers)
        """
        # Skip rate limiting in test mode
        if is_test_mode():
            return True, None, {}
            
        if self.is_exempt(request):
            return True, None, {}
        
        key = self._get_client_key(request)
        
        with self._lock:
            if key not in self.buckets:
                self.buckets[key] = TokenBucket(
                    capacity=self.burst,
                    refill_rate=self.refill_rate,
                )
            
            bucket = self.buckets[key]
            allowed = bucket.consume(1)
            retry_after = bucket.get_retry_after(1) if not allowed else None
            
            headers = {
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": str(max(0, int(bucket.tokens))),
                "X-RateLimit-Reset": str(int(time.time()) + (retry_after or 0)),
            }
            
            if not allowed:
                headers["Retry-After"] = str(retry_after)
            
            return allowed, retry_after, headers
    
    def cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """Remove buckets that haven't been used recently."""
        now = time.monotonic()
        with self._lock:
            keys_to_remove = [
                key for key, bucket in self.buckets.items()
                if now - bucket.last_refill > max_age_seconds
            ]
            for key in keys_to_remove:
                del self.buckets[key]


# Global rate limiter instance
_rate_limiter: Optional[InMemoryRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        requests_per_minute = int(os.environ.get("RATE_LIMIT_RPM", "60"))
        burst = int(os.environ.get("RATE_LIMIT_BURST", "10"))
        _rate_limiter = InMemoryRateLimiter(
            requests_per_minute=requests_per_minute,
            burst=burst,
        )
    return _rate_limiter


def configure_rate_limiter(
    requests_per_minute: int = 60,
    burst: int = 10,
    exempt_paths: Optional[set] = None,
) -> InMemoryRateLimiter:
    """Configure the global rate limiter."""
    global _rate_limiter
    _rate_limiter = InMemoryRateLimiter(
        requests_per_minute=requests_per_minute,
        burst=burst,
        exempt_paths=exempt_paths,
    )
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst: int = 10,
        exempt_paths: Optional[set] = None,
    ):
        super().__init__(app)
        self.rate_limiter = configure_rate_limiter(
            requests_per_minute=requests_per_minute,
            burst=burst,
            exempt_paths=exempt_paths,
        )
    
    async def dispatch(self, request: Request, call_next):
        # Check rate limit
        allowed, retry_after, headers = self.rate_limiter.check_rate_limit(request)
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={
                    **headers,
                    "Retry-After": str(retry_after),
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response