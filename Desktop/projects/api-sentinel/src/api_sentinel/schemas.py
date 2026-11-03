from pydantic import BaseModel, ConfigDict, HttpUrl
from datetime import datetime
from typing import List, Dict, Any, Optional

# --- Endpoint Schemas ---
class EndpointCreate(BaseModel):
    name: str
    url: str
    interval_seconds: int = 300

    model_config = ConfigDict(from_attributes=True)


class EndpointUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    interval_seconds: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EndpointResponse(BaseModel):
    id: int
    name: str
    url: str
    interval_seconds: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Check Run Schemas ---
class CheckRunResponse(BaseModel):
    id: int
    endpoint_id: int
    status: str
    duration_ms: float
    findings_json: List[Dict[str, Any]]
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Baseline Schemas ---
class BaselineResponse(BaseModel):
    id: int
    endpoint_id: int
    contract_json: Dict[str, Any]
    version: int
    approved_at: datetime

    model_config = ConfigDict(from_attributes=True)