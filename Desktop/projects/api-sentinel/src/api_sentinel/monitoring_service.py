from .http_client import fetch_endpoint
from .contract_inference import infer_contract
from .comparator import compare_with_contract

async def run_monitoring_check(url: str, approved_contract: dict = None) -> dict:
    """
    Orchestrates a single monitoring check for an endpoint.
    
    If no approved_contract is provided, it infers one and returns it for approval.
    If a contract is provided, it compares the response against it.
    """
    
    # 1. Fetch the endpoint
    result = await fetch_endpoint(url)
    
    # 2. Handle network or HTTP errors
    if not result["success"]:
        return {
            "status": "network_error",
            "message": result["json_error"],
            "duration_ms": result["duration_ms"],
            "findings": []
        }
        
    if result["status_code"] >= 400:
        return {
            "status": "http_error",
            "message": f"HTTP {result['status_code']}",
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