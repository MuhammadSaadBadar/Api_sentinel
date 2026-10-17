from api_sentinel.comparator import compare_with_contract

def test_no_changes_with_valid_response():
    contract = {
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "name": {"type": "string"}
        }
    }
    current_response = {"id": 1, "name": "Keyboard"}
    
    findings = compare_with_contract(contract, current_response)
    assert findings == []

def test_detects_missing_field():
    contract = {
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "in_stock": {"type": "boolean"}
        }
    }
    # in_stock is missing
    current_response = {"id": 1}
    
    findings = compare_with_contract(contract, current_response)
    assert findings == [
        {
            "path": "$.in_stock",
            "change": "field_missing",
            "expected": "present",
            "actual": "missing"
        }
    ]

def test_detects_type_change():
    contract = {
        "type": "object",
        "properties": {
            "price": {"type": "number"}
        }
    }
    # price is a string instead of a number
    current_response = {"price": "4500.0"}
    
    findings = compare_with_contract(contract, current_response)
    assert findings == [
        {
            "path": "$.price",
            "change": "type_changed",
            "expected": "number",
            "actual": "string"
        }
    ]

def test_detects_added_field():
    contract = {
        "type": "object",
        "properties": {
            "id": {"type": "number"}
        }
    }
    # description is new
    current_response = {"id": 1, "description": "A keyboard"}
    
    findings = compare_with_contract(contract, current_response)
    assert findings == [
        {
            "path": "$.description",
            "change": "field_added",
            "expected": "missing",
            "actual": "present"
        }
    ]

def test_detects_nested_missing_field():
    contract = {
        "type": "object",
        "properties": {
            "category": {
                "type": "object",
                "properties": {
                    "id": {"type": "number"},
                    "name": {"type": "string"}
                }
            }
        }
    }
    # nested "name" is missing
    current_response = {
        "category": {"id": 5}
    }
    
    findings = compare_with_contract(contract, current_response)
    assert findings == [
        {
            "path": "$.category.name",
            "change": "field_missing",
            "expected": "present",
            "actual": "missing"
        }
    ]