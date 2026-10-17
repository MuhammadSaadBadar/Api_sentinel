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


def infer_contract(response_json):
    """
    Infer a structural contract from a single JSON response.
    
    Returns a dictionary representing the expected types and structure.
    """
    
    def infer_value(value):
        json_type = get_json_type(value)
        
        # Base case: primitive types (string, number, boolean, null)
        if json_type != "object" and json_type != "array":
            return {"type": json_type}
            
        # Recursive case: nested objects
        if json_type == "object":
            properties = {}
            for key, val in value.items():
                properties[key] = infer_value(val)
                
            return {
                "type": "object",
                "properties": properties
            }
            
        # Recursive case: arrays (we inspect the first item to infer the item type)
        if json_type == "array":
            if not value:
                return {"type": "array", "items": None}
            
            # For this initial version, we assume array items are homogeneous
            # and we infer the contract based on the first item.
            first_item = value[0]
            return {
                "type": "array",
                "items": infer_value(first_item)
            }

    return infer_value(response_json)