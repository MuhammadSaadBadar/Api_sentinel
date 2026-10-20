import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 
from api_sentinel.db import Base, Endpoint, Baseline, CheckRun

# use an in-memory sqlite database
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    
def test_create_endpoint(db_session):
    endpoint = Endpoint(name = "Test API", url = "http://example.com/api")
    db_session.add(endpoint)
    db_session.commit()
    
    saved_endpoint = db_session.query(Endpoint).first()
    assert saved_endpoint.name == "Test API"
    assert saved_endpoint.url == "http://example.com/api"
    
def test_add_baseline_to_endpoint(db_session):
    endpoint = Endpoint(name = "Test API", url = "http://example.com/api")
    db_session.add(endpoint)
    db_session.commit()
   
    contract = {"type": "object", "properties": {"id": {"type": "number"}}}
    baseline = Baseline(endpoint_id = endpoint.id , contract_json = contract)
    db_session.add(baseline)
    db_session.commit()
    
    saved_baseline = db_session.query(Baseline).first()
    assert saved_baseline.contract_json == contract
    assert saved_baseline.endpoint.name == "Test API"
    
def test_add_check_run(db_session):
    endpoint = Endpoint(name="Test API", url="https://api.example.com")
    db_session.add(endpoint)
    db_session.commit()
    
    run = CheckRun(
        endpoint_id=endpoint.id,
        status="healthy",
        duration_ms=150.5,
        findings_json=[]
    )
    db_session.add(run)
    db_session.commit()
    
    saved_run = db_session.query(CheckRun).first()
    assert saved_run.status == "healthy"
    assert saved_run.duration_ms == 150.5
    