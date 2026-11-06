"""
Security Headers Middleware

Adds security-related HTTP headers to all responses.
"""

import os
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - Content-Security-Policy (CSP)
    - Strict-Transport-Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - Referrer-Policy
    - Permissions-Policy
    - Cross-Origin-Opener-Policy
    - Cross-Origin-Resource-Policy
    """
    
    def __init__(
        self,
        app,
        csp_policy: str = None,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str = None,
        coep_policy: str = "same-origin",
        coop_policy: str = "same-origin",
    ):
        super().__init__(app)
        
        # Content Security Policy
        # Allow Pico.css and HTMX from CDN, inline styles/scripts for HTMX
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # HSTS
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        
        # Other headers
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy or (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        self.coep_policy = coep_policy
        self.coop_policy = coop_policy
        
        # Check if we should enforce HTTPS (production)
        self.enforce_https = os.environ.get("ENFORCE_HTTPS", "false").lower() == "true"
    
    def _build_hsts_header(self) -> str:
        """Build HSTS header value."""
        parts = [f"max-age={self.hsts_max_age}"]
        if self.hsts_include_subdomains:
            parts.append("includeSubDomains")
        if self.hsts_preload:
            parts.append("preload")
        return "; ".join(parts)
    
    async def dispatch(self, request: Request, call_next):
        # Skip security headers in test mode
        test_mode = os.environ.get("TEST_MODE", "false").lower() == "true"
        
        response = await call_next(request)
        
        if test_mode:
            return response
        
        # Add security headers
        response.headers["Content-Security-Policy"] = self.csp_policy
        response.headers["Strict-Transport-Security"] = self._build_hsts_header()
        response.headers["X-Frame-Options"] = self.frame_options
        response.headers["X-Content-Type-Options"] = self.content_type_options
        response.headers["Referrer-Policy"] = self.referrer_policy
        response.headers["Permissions-Policy"] = self.permissions_policy
        response.headers["Cross-Origin-Opener-Policy"] = self.coop_policy
        response.headers["Cross-Origin-Resource-Policy"] = self.coep_policy
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


def add_security_headers_middleware(app):
    """Add security headers middleware to FastAPI app."""
    app.add_middleware(SecurityHeadersMiddleware)