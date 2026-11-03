from .http_client import fetch_endpoint
from .contract_inference import infer_contract
from .comparator import compare_with_contract


async def run_monitoring_check(
    url: str,
    approved_contract: dict = None,
    method: str = "GET",
    headers: dict = None,
    query_params: dict = None,
    auth_config: dict = None,
    timeout_seconds: int = 30,
    expected_status_codes: list = None,
) -> dict:
    """
    Orchestrates a single monitoring check for an endpoint.
    
    If no approved_contract is provided, it infers one and returns it for approval.
    If a contract is provided, it compares the response against it.
    """
    
    # Merge auth headers into request headers
    request_headers = dict(headers) if headers else {}
    if auth_config:
        auth_type = auth_config.get("type", "").lower()
        if auth_type == "bearer":
            token = auth_config.get("token")
            if token:
                request_headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key":
            key = auth_config.get("key")
            header_name = auth_config.get("header_name", "X-API-Key")
            if key:
                request_headers[header_name] = key
        elif auth_type == "basic":
            username = auth_config.get("username")
            password = auth_config.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                request_headers["Authorization"] = f"Basic {credentials}"

    # 1. Fetch the endpoint with full configuration
    result = await fetch_endpoint(
        url=url,
        method=method,
        headers=request_headers,
        query_params=query_params,
        timeout_seconds=timeout_seconds,
        expected_status_codes=expected_status_codes,
    )
    
    # 2. Handle network or HTTP errors
    if not result["success"]:
        return {
            "status": "network_error" if result["status_code"] is None else "http_error",
            "message": result["json_error"],
            "duration_ms": result["duration_ms"],
            "findings": []
        }
        
    # 3. Handle invalid JSON
    if result["json_error"]:
        return {
            "status": "invalid_json",
            "message": result["json_error"],
            "duration_ms": result["duration_ms"],
            "findings": []
        }
        
    # 4. Infer new contract (if this is a new endpoint)
    if approved_contract is None:
        inferred = infer_contract(result["body"])
        return {
            "status": "awaiting_approval",
            "message": "Contract inferred successfully. Awaiting developer approval.",
            "duration_ms": result["duration_ms"],
            "contract": inferred,
            "findings": []
        }
        
    # 5. Compare with approved contract (if it exists)
    findings = compare_with_contract(approved_contract, result["body"])
    
    # Determine status based on findings
    if len(findings) == 0:
        status = "healthy"
        message = "No structural changes detected."
    else:
        status = "changes_detected"
        message = f"{len(findings)} structural change(s) detected."
        
    return {
        "status": status,
        "message": message,
        "duration_ms": result["duration_ms"],
        "findings": findings
    }