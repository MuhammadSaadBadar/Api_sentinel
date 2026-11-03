from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .db import get_db, init_db, Endpoint, Baseline, CheckRun
from .schemas import EndpointCreate, EndpointUpdate, EndpointResponse, CheckRunResponse, BaselineResponse
from .monitoring_service import run_monitoring_check
from .scheduler import scheduler_lifespan, schedule_endpoint, unschedule_endpoint


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