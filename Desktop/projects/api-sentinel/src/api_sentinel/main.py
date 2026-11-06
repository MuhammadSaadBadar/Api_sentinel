import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Form, Query, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from .db import get_db, init_db, Endpoint, Baseline, CheckRun, User
from .schemas import EndpointCreate, EndpointUpdate, EndpointResponse, CheckRunResponse, BaselineResponse, UserCreate, UserResponse, Token, LoginRequest, RefreshRequest, APIKeyResponse
from .monitoring_service import run_monitoring_check
from .scheduler import scheduler_lifespan, schedule_endpoint, unschedule_endpoint
from .auth import (
    authenticate_user, create_user, create_access_token, create_refresh_token,
    get_current_user, get_current_user_from_token, require_admin, require_auth,
    generate_api_key, hash_api_key, set_auth_cookies, clear_auth_cookies,
    decode_token, get_user_by_id,
)
from .rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    async with scheduler_lifespan(app):
        yield


app = FastAPI(
    title="API Sentinel",
    description="Monitor API contracts for breaking changes",
    lifespan=lifespan,
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=int(os.environ.get("RATE_LIMIT_RPM", "60")),
    burst=int(os.environ.get("RATE_LIMIT_BURST", "10")),
    exempt_paths={
        "/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico", "/static",
        "/auth/register", "/auth/login", "/auth/refresh", "/auth/logout", "/auth/me",
        "/ui/login", "/ui/register",
    },
)

# Templates and static files
import json
import os
from jinja2 import Environment, FileSystemLoader

template_dir = os.path.join(os.path.dirname(__file__), "templates")
# Create custom Jinja2 environment with disabled cache
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    auto_reload=True,
    cache_size=0,  # Disable template caching
    enable_async=True,
)
app.mount("/static", StaticFiles(directory="src/api_sentinel/static"), name="static")


def json_dumps(value, indent=None) -> str:
    """JSON serialize for template."""
    if value is None:
        return "{}"
    return json.dumps(value, indent=indent)


# Custom template filters
def datetime_utc(value: datetime) -> str:
    """Format datetime as UTC string."""
    if value is None:
        return ""
    return value.strftime('%Y-%m-%d %H:%M:%S UTC')


jinja_env.filters["datetime_utc"] = datetime_utc
jinja_env.filters["tojson_safe"] = json_dumps


async def render_template(template_name: str, context: dict) -> HTMLResponse:
    """Render a Jinja2 template and return HTMLResponse."""
    template = jinja_env.get_template(template_name)
    content = await template.render_async(**context)
    return HTMLResponse(content=content)


def utc_now():
    """Helper to return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def get_latest_status(db: Session, endpoint: Endpoint) -> str:
    """Get the latest status for an endpoint."""
    latest_check = db.query(CheckRun).filter(CheckRun.endpoint_id == endpoint.id).order_by(CheckRun.checked_at.desc()).first()
    if latest_check:
        return latest_check.status
    # Check if there's a baseline
    baseline = db.query(Baseline).filter(Baseline.endpoint_id == endpoint.id).first()
    if baseline:
        return "awaiting_approval"
    return "unknown"


def get_latest_baseline(db: Session, endpoint: Endpoint):
    return db.query(Baseline).filter(Baseline.endpoint_id == endpoint.id).order_by(Baseline.version.desc()).first()


def get_latest_check(db: Session, endpoint: Endpoint):
    return db.query(CheckRun).filter(CheckRun.endpoint_id == endpoint.id).order_by(CheckRun.checked_at.desc()).first()


def get_all_baselines(db: Session, endpoint: Endpoint):
    return db.query(Baseline).filter(Baseline.endpoint_id == endpoint.id).order_by(Baseline.version.desc()).all()


def get_all_checks(db: Session, endpoint: Endpoint, limit: int = 50):
    return db.query(CheckRun).filter(CheckRun.endpoint_id == endpoint.id).order_by(CheckRun.checked_at.desc()).limit(limit).all()


def is_test_mode() -> bool:
    """Check if running in test mode."""
    return os.environ.get("TEST_MODE", "false").lower() == "true"


# ==================== UI ROUTES ====================

@app.get("/ui/", response_class=HTMLResponse)
async def ui_dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard overview - list all endpoints with status."""
    endpoints = db.query(Endpoint).all()
    
    # Enrich endpoints with latest status
    enriched_endpoints = []
    for ep in endpoints:
        enriched_endpoints.append({
            "id": ep.id,
            "name": ep.name,
            "url": ep.url,
            "method": ep.method,
            "interval_seconds": ep.interval_seconds,
            "is_active": ep.is_active,
            "latest_status": get_latest_status(db, ep),
            "latest_check": get_latest_check(db, ep),
            "latest_baseline": get_latest_baseline(db, ep),
        })
    
    return await render_template("dashboard.html", {
        "request": request,
        "endpoints": enriched_endpoints,
    })


@app.get("/ui/partials/endpoint-list", response_class=HTMLResponse)
async def ui_endpoint_list(request: Request, db: Session = Depends(get_db)):
    """Partial: endpoint table rows for HTMX refresh."""
    endpoints = db.query(Endpoint).all()
    
    enriched_endpoints = []
    for ep in endpoints:
        enriched_endpoints.append({
            "id": ep.id,
            "name": ep.name,
            "url": ep.url,
            "method": ep.method,
            "interval_seconds": ep.interval_seconds,
            "is_active": ep.is_active,
            "latest_status": get_latest_status(db, ep),
            "latest_check": get_latest_check(db, ep),
            "latest_baseline": get_latest_baseline(db, ep),
        })
    
    return await render_template("partials/endpoint_list.html", {
        "request": request,
        "endpoints": enriched_endpoints,
    })


@app.get("/ui/partials/endpoint-row/{endpoint_id}", response_class=HTMLResponse)
async def ui_endpoint_row(endpoint_id: int, request: Request, db: Session = Depends(get_db)):
    """Partial: single endpoint row for HTMX refresh."""
    ep = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not ep:
        return HTMLResponse("", status_code=404)
    
    enriched = {
        "id": ep.id,
        "name": ep.name,
        "url": ep.url,
        "method": ep.method,
        "interval_seconds": ep.interval_seconds,
        "is_active": ep.is_active,
        "latest_status": get_latest_status(db, ep),
        "latest_check": get_latest_check(db, ep),
        "latest_baseline": get_latest_baseline(db, ep),
    }
    
    return await render_template("partials/endpoint_list.html", {
        "request": request,
        "endpoints": [enriched],
    })


@app.get("/ui/endpoints/new", response_class=HTMLResponse)
async def ui_new_endpoint(request: Request):
    """New endpoint form."""
    return await render_template("endpoints/form.html", {
        "request": request,
        "endpoint": None,
        "action_url": "/endpoints",
        "method": "POST",
    })


@app.get("/ui/endpoints/{endpoint_id}", response_class=HTMLResponse)
async def ui_endpoint_detail(
    endpoint_id: int, 
    request: Request, 
    tab: str = Query("overview"),
    db: Session = Depends(get_db)
):
    """Endpoint detail page with tabs."""
    ep = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    latest_check = get_latest_check(db, ep)
    latest_baseline = get_latest_baseline(db, ep)
    baselines = get_all_baselines(db, ep)
    checks = get_all_checks(db, ep)
    
    return await render_template("endpoints/detail.html", {
        "request": request,
        "endpoint": ep,
        "latest_check": latest_check,
        "latest_baseline": latest_baseline,
        "baselines": baselines,
        "checks": checks,
        "latest_status": get_latest_status(db, ep),
        "active_tab": tab,
    })


@app.get("/ui/endpoints/{endpoint_id}/edit", response_class=HTMLResponse)
async def ui_edit_endpoint(endpoint_id: int, request: Request, db: Session = Depends(get_db)):
    """Edit endpoint form."""
    ep = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    return await render_template("endpoints/form.html", {
        "request": request,
        "endpoint": ep,
        "action_url": f"/endpoints/{endpoint_id}",
        "method": "PATCH",
    })


# ==================== API ROUTES ====================

@app.post("/endpoints", response_model=EndpointResponse, status_code=201)
def create_endpoint(endpoint_in: EndpointCreate, db: Session = Depends(get_db)):
    """Register a new endpoint for monitoring."""
    existing = db.query(Endpoint).filter(Endpoint.url == endpoint_in.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Endpoint with this URL already exists")

    new_endpoint = Endpoint(
        name=endpoint_in.name,
        url=endpoint_in.url,
        method=endpoint_in.method,
        headers=endpoint_in.headers,
        query_params=endpoint_in.query_params,
        auth_config=endpoint_in.auth_config,
        timeout_seconds=endpoint_in.timeout_seconds,
        expected_status_codes=endpoint_in.expected_status_codes,
        response_format=endpoint_in.response_format,
        interval_seconds=endpoint_in.interval_seconds,
    )
    db.add(new_endpoint)
    db.commit()
    db.refresh(new_endpoint)

    if new_endpoint.is_active:
        schedule_endpoint(new_endpoint.id, new_endpoint.interval_seconds)

    return new_endpoint


@app.get("/endpoints", response_model=List[EndpointResponse])
def list_endpoints(db: Session = Depends(get_db)):
    """List all registered endpoints."""
    return db.query(Endpoint).all()


@app.get("/endpoints/{endpoint_id}", response_model=EndpointResponse)
def get_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Get a single endpoint by ID."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return endpoint


@app.patch("/endpoints/{endpoint_id}", response_model=EndpointResponse)
def update_endpoint(endpoint_id: int, endpoint_in: EndpointUpdate, db: Session = Depends(get_db)):
    """Update an endpoint configuration."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    update_data = endpoint_in.model_dump(exclude_unset=True)

    # Check for URL conflict
    if "url" in update_data and update_data["url"] != endpoint.url:
        existing = db.query(Endpoint).filter(Endpoint.url == update_data["url"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Endpoint with this URL already exists")

    was_active = endpoint.is_active

    for field, value in update_data.items():
        setattr(endpoint, field, value)

    db.commit()
    db.refresh(endpoint)

    # Manage scheduler job if interval changed
    if endpoint.is_active:
        schedule_endpoint(endpoint.id, endpoint.interval_seconds)
    elif was_active:
        unschedule_endpoint(endpoint.id)

    return endpoint


@app.delete("/endpoints/{endpoint_id}", status_code=204)
def delete_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Delete an endpoint."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    unschedule_endpoint(endpoint_id)
    db.delete(endpoint)
    db.commit()


@app.post("/endpoints/{endpoint_id}/activate", response_model=EndpointResponse)
def activate_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Activate an endpoint for monitoring."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    endpoint.is_active = True
    db.commit()
    db.refresh(endpoint)

    schedule_endpoint(endpoint.id, endpoint.interval_seconds)
    return endpoint


@app.post("/endpoints/{endpoint_id}/deactivate", response_model=EndpointResponse)
def deactivate_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Deactivate an endpoint (pause monitoring)."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    endpoint.is_active = False
    db.commit()
    db.refresh(endpoint)

    unschedule_endpoint(endpoint.id)
    return endpoint


@app.post("/endpoints/{endpoint_id}/approve-baseline", response_model=BaselineResponse)
async def approve_baseline(endpoint_id: int, db: Session = Depends(get_db)):
    """
    Fetch the endpoint, infer a contract, and save it as the approved baseline.
    """
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    result = await run_monitoring_check(
        url=endpoint.url,
        method=endpoint.method,
        headers=endpoint.headers,
        query_params=endpoint.query_params,
        auth_config=endpoint.auth_config,
        timeout_seconds=endpoint.timeout_seconds,
        expected_status_codes=endpoint.expected_status_codes,
        test_mode=is_test_mode(),
    )

    if result["status"] != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Could not infer contract. Status: {result['status']}. Message: {result['message']}",
        )

    latest_baseline = (
        db.query(Baseline).filter(Baseline.endpoint_id == endpoint.id).order_by(Baseline.version.desc()).first()
    )

    new_version = (latest_baseline.version + 1) if latest_baseline else 1

    new_baseline = Baseline(endpoint_id=endpoint.id, contract_json=result["contract"], version=new_version)
    db.add(new_baseline)
    db.commit()
    db.refresh(new_baseline)

    return new_baseline


@app.get("/endpoints/{endpoint_id}/baselines", response_model=List[BaselineResponse])
def list_baselines(endpoint_id: int, db: Session = Depends(get_db)):
    """List all baseline versions for an endpoint."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return (
        db.query(Baseline).filter(Baseline.endpoint_id == endpoint_id).order_by(Baseline.version.desc()).all()
    )


@app.get("/endpoints/{endpoint_id}/checks", response_model=List[CheckRunResponse])
def get_endpoint_checks(endpoint_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """View the historical check runs for an endpoint."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return (
        db.query(CheckRun)
        .filter(CheckRun.endpoint_id == endpoint_id)
        .order_by(CheckRun.checked_at.desc())
        .limit(limit)
        .all()
    )


# --- Auth Routes ---

@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (admin only in production)."""
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = create_user(db, user_in.username, user_in.password, user_in.role)
    return user


@app.post("/auth/login", response_model=Token)
async def login(response: Response, login_in: LoginRequest, db: Session = Depends(get_db)):
    """Login with username and password, returns JWT tokens."""
    user = authenticate_user(db, login_in.username, login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = utc_now()
    db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    set_auth_cookies(response, access_token, refresh_token)
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@app.post("/auth/refresh", response_model=Token)
async def refresh_token(response: Response, refresh_in: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = decode_token(refresh_in.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    set_auth_cookies(response, access_token, new_refresh_token)
    
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@app.post("/auth/logout")
async def logout(response: Response):
    """Logout and clear cookies."""
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(user: User = Depends(get_current_user_from_token)):
    """Get current authenticated user info."""
    return user


# --- API Key Management ---

@app.post("/endpoints/{endpoint_id}/api-key", response_model=APIKeyResponse)
def generate_endpoint_api_key(endpoint_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Generate a new API key for an endpoint (admin only)."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    api_key = generate_api_key()
    endpoint.api_key_hash = hash_api_key(api_key)
    db.commit()
    db.refresh(endpoint)
    
    return APIKeyResponse(
        api_key=api_key,
        endpoint_id=endpoint.id,
        created_at=utc_now(),
    )


@app.delete("/endpoints/{endpoint_id}/api-key")
def revoke_endpoint_api_key(endpoint_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Revoke API key for an endpoint (admin only)."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    endpoint.api_key_hash = None
    db.commit()
    
    return {"message": "API key revoked"}


# --- UI Auth Routes ---

@app.get("/ui/login", response_class=HTMLResponse)
async def ui_login(request: Request):
    """Login page."""
    return await render_template("auth/login.html", {"request": request})


@app.get("/ui/register", response_class=HTMLResponse)
async def ui_register(request: Request):
    """Register page (admin only in production)."""
    return await render_template("auth/register.html", {"request": request})