from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .db import get_db, init_db, Endpoint, Baseline, CheckRun
from .schemas import EndpointCreate, EndpointResponse, CheckRunResponse, BaselineResponse
from .monitoring_service import run_monitoring_check

app = FastAPI(title="API Sentinel", description="Monitor API contracts for breaking changes")

@app.on_event("startup")
def on_startup():
    init_db() # Ensure tables exist when app starts

@app.post("/endpoints", response_model=EndpointResponse, status_code=201)
def create_endpoint(endpoint_in: EndpointCreate, db: Session = Depends(get_db)):
    """Register a new endpoint for monitoring."""
    # Check if it already exists
    existing = db.query(Endpoint).filter(Endpoint.url == endpoint_in.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Endpoint with this URL already exists")

    new_endpoint = Endpoint(
        name=endpoint_in.name,
        url=endpoint_in.url,
        interval_seconds=endpoint_in.interval_seconds
    )
    db.add(new_endpoint)
    db.commit()
    db.refresh(new_endpoint)
    return new_endpoint

@app.get("/endpoints", response_model=List[EndpointResponse])
def list_endpoints(db: Session = Depends(get_db)):
    """List all registered endpoints."""
    return db.query(Endpoint).all()

@app.post("/endpoints/{endpoint_id}/approve-baseline", response_model=BaselineResponse)
async def approve_baseline(endpoint_id: int, db: Session = Depends(get_db)):
    """
    Fetch the endpoint, infer a contract, and save it as the approved baseline.
    """
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    # Run a check without passing a contract to force inference
    result = await run_monitoring_check(endpoint.url)
    
    if result["status"] != "awaiting_approval":
        raise HTTPException(
            status_code=400, 
            detail=f"Could not infer contract. Status: {result['status']}. Message: {result['message']}"
        )
        
    # Determine new version number
    latest_baseline = db.query(Baseline).filter(
        Baseline.endpoint_id == endpoint.id
    ).order_by(Baseline.version.desc()).first()
    
    new_version = (latest_baseline.version + 1) if latest_baseline else 1

    # Save the new baseline
    new_baseline = Baseline(
        endpoint_id=endpoint.id,
        contract_json=result["contract"],
        version=new_version
    )
    db.add(new_baseline)
    db.commit()
    db.refresh(new_baseline)
    
    return new_baseline

@app.get("/endpoints/{endpoint_id}/checks", response_model=List[CheckRunResponse])
def get_endpoint_checks(endpoint_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """View the historical check runs for an endpoint."""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return db.query(CheckRun).filter(
        CheckRun.endpoint_id == endpoint_id
    ).order_by(CheckRun.checked_at.desc()).limit(limit).all()