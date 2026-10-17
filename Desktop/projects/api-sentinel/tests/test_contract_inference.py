from api_sentinel.contract_inference import infer_contract

def test_infer_primitive_types():
    assert infer_contract("hello") == {"type": "string"}
    assert infer_contract(42) == {"type": "number"}
    assert infer_contract(42.5) == {"type": "number"}
    assert infer_contract(True) == {"type": "boolean"}
    assert infer_contract(None) == {"type": "null"}

def test_infer_simple_object():
    data = {
        "id": 101,
        "name": "Keyboard",
        "in_stock": True
    }
    expected = {
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "name": {"type": "string"},
            "in_stock": {"type": "boolean"}
        }
    }
    assert infer_contract(data) == expected

def test_infer_nested_object():
    data = {
        "id": 101,
        "category": {
            "id": 5,
            "name": "Electronics"
        }
    }
    expected = {
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "category": {
                "type": "object",
                "properties": {
                    "id": {"type": "number"},
                    "name": {"type": "string"}
                }
            }
        }
    }
    assert infer_contract(data) == expected

def test_infer_array():
    data = {
        "tags": ["electronics", "accessories"],
        "variants": [{"id": 1, "color": "black"}]
    }
    expected = {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            },
            "variants": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "number"},
                        "color": {"type": "string"}
                    }
                }
            }
        }
    }
    assert infer_contract(data) == expected

def test_infer_empty_array():
    data = {"items": []}
    expected = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": None
            }
        }
    }
    assert infer_contract(data) == expected

def test_infer_boolean_is_not_number():
    # Strict JSON type checking (Python treats bool as subclass of int)
    data = {"active": True}
    contract = infer_contract(data)
    assert contract["properties"]["active"]["type"] == "boolean"