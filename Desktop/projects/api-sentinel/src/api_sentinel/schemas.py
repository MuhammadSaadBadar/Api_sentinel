from pydantic import BaseModel, ConfigDict, HttpUrl, Field
from datetime import datetime
from typing import List, Dict, Any, Optional


# --- Endpoint Schemas ---
class EndpointCreate(BaseModel):
    name: str
    url: str
    method: str = "GET"
    headers: Dict[str, str] = Field(default_factory=dict)
    query_params: Dict[str, str] = Field(default_factory=dict)
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30
    expected_status_codes: List[int] = Field(default_factory=lambda: [200])
    response_format: str = "json"
    interval_seconds: int = 300

    model_config = ConfigDict(from_attributes=True)


class EndpointUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    auth_config: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = None
    expected_status_codes: Optional[List[int]] = None
    response_format: Optional[str] = None
    interval_seconds: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EndpointResponse(BaseModel):
    id: int
    name: str
    url: str
    method: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    auth_config: Dict[str, Any]
    timeout_seconds: int
    expected_status_codes: List[int]
    response_format: str
    interval_seconds: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Check Run Schemas ---
class CheckRunResponse(BaseModel):
    id: int
    endpoint_id: int
    baseline_version: Optional[int] = None
    status: str
    duration_ms: float
    findings_json: List[Dict[str, Any]]
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Finding Schemas ---
class FindingResponse(BaseModel):
    id: int
    check_run_id: int
    json_path: str
    change_type: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    severity: str
    review_status: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FindingUpdate(BaseModel):
    review_status: str

    model_config = ConfigDict(from_attributes=True)


# --- Baseline Schemas ---
class BaselineResponse(BaseModel):
    id: int
    endpoint_id: int
    contract_json: Dict[str, Any]
    version: int
    approved_at: datetime

    model_config = ConfigDict(from_attributes=True)