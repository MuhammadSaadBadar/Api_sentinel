def get_json_type(value):
    """Return the JSON data type of a Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def compare_with_contract(contract, current_response):
    """
    Compare a new JSON response against an approved contract.
    Returns a list of findings (violations).
    """
    findings = []

    def compare_value(expected_contract, actual_value, path):
        # If the contract expects an object but we didn't get one
        if expected_contract["type"] == "object":
            if not isinstance(actual_value, dict):
                findings.append({
                    "path": path,
                    "change": "type_changed",
                    "expected": "object",
                    "actual": get_json_type(actual_value)
                })
                return

            expected_props = expected_contract.get("properties", {})
            
            # Check for missing fields
            for key in expected_props:
                if key not in actual_value:
                    findings.append({
                        "path": f"{path}.{key}",
                        "change": "field_missing",
                        "expected": "present",
                        "actual": "missing"
                    })
                else:
                    # Recursively check the fields that ARE present
                    compare_value(expected_props[key], actual_value[key], f"{path}.{key}")
            
            # Check for added fields (optional: we flag them but don't treat as breaking)
            for key in actual_value:
                if key not in expected_props:
                    findings.append({
                        "path": f"{path}.{key}",
                        "change": "field_added",
                        "expected": "missing",
                        "actual": "present"
                    })

        # If the contract expects a primitive type, check it strictly
        else:
            actual_type = get_json_type(actual_value)
            expected_type = expected_contract["type"]
            
            # Allow nulls if the contract inferred a null, otherwise strict check
            if expected_type != actual_type:
                findings.append({
                    "path": path,
                    "change": "type_changed",
                    "expected": expected_type,
                    "actual": actual_type
                })

    compare_value(contract, current_response, "$")
    return findings