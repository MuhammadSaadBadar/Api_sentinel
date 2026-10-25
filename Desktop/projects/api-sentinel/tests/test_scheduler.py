import pytest
import httpx
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api_sentinel.db import Base,Endpoint,Baseline,CheckRun
from api_sentinel.scheduler import run_check_for_endpoint


@pytest.fixture
def test_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    #patch the sessionmake to use test
    import api_sentinel.scheduler as scheduler_module
    monkeypatch.setattr(scheduler_module, "SessionLocal", Session)
    yield session
    session.close()
    
@pytest.mark.asyncio
async def test_run_check_for_endpoint(test_db):
    #1
    endpoint = Endpoint(name="Test API", url="https://api.example.com/products" )
    test_db.add(endpoint)
    test_db.commit()
    

    contract = {"type": "object", "properties": {"id": {"type": "number"}}}
    baseline = Baseline(endpoint_id=endpoint.id, contract_json=contract)
    test_db.add(baseline)
    test_db.commit()
    
    #2
    with respx.mock:
        respx.get("https://api.example.com/products").mock(
            return_value=httpx.Response(200, json={"id": 1})
        )
        
        # 3. Run the background task
        await run_check_for_endpoint(endpoint.id)

    # 4. Verify the result was saved to the database
    saved_run = test_db.query(CheckRun).first()
    assert saved_run is not None
    assert saved_run.status == "healthy"
    assert saved_run.duration_ms > 0
    assert saved_run.findings_json == []

@pytest.mark.asyncio
async def test_run_check_saves_breaking_change(test_db):
    # 1. Setup Endpoint and Baseline
    endpoint = Endpoint(name="Test API", url="https://api.example.com/products")
    test_db.add(endpoint)
    test_db.commit()
    
    contract = {"type": "object", "properties": {"price": {"type": "number"}}}
    baseline = Baseline(endpoint_id=endpoint.id, contract_json=contract)
    test_db.add(baseline)
    test_db.commit()

    # 2. Mock HTTP request that breaks the contract
    with respx.mock:
        respx.get("https://api.example.com/products").mock(
            return_value=httpx.Response(200, json={"price": "4500"})
        )
        
        # 3. Run the background task
        await run_check_for_endpoint(endpoint.id)

    # 4. Verify the finding was saved
    saved_run = test_db.query(CheckRun).first()
    assert saved_run is not None
    assert saved_run.status == "changes_detected"
    assert len(saved_run.findings_json) == 1
    assert saved_run.findings_json[0]["change"] == "type_changed"