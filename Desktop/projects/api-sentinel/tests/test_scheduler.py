import pytest
import httpx
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api_sentinel.db import Base, Endpoint, Baseline, CheckRun
from api_sentinel.scheduler import (
    run_check_for_endpoint,
    schedule_endpoint,
    unschedule_endpoint,
    load_active_endpoints,
    start_scheduler,
    shutdown_scheduler,
    _get_job_id,
    scheduler,
)


@pytest.fixture
def test_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    import api_sentinel.scheduler as scheduler_module

    monkeypatch.setattr(scheduler_module, "SessionLocal", Session)
    yield session
    session.close()


@pytest.fixture(autouse=True)
def clean_scheduler():
    """Ensure scheduler is stopped before and after each test."""
    shutdown_scheduler(wait=False)
    yield
    shutdown_scheduler(wait=False)


@pytest.mark.asyncio
async def test_run_check_for_endpoint(test_db):
    endpoint = Endpoint(name="Test API", url="https://api.example.com/products")
    test_db.add(endpoint)
    test_db.commit()

    contract = {"type": "object", "properties": {"id": {"type": "number"}}}
    baseline = Baseline(endpoint_id=endpoint.id, contract_json=contract)
    test_db.add(baseline)
    test_db.commit()

    with respx.mock:
        respx.get("https://api.example.com/products").mock(
            return_value=httpx.Response(200, json={"id": 1})
        )

        await run_check_for_endpoint(endpoint.id)

    saved_run = test_db.query(CheckRun).first()
    assert saved_run is not None
    assert saved_run.status == "healthy"
    assert saved_run.duration_ms > 0
    assert saved_run.findings_json == []


@pytest.mark.asyncio
async def test_run_check_saves_breaking_change(test_db):
    endpoint = Endpoint(name="Test API", url="https://api.example.com/products")
    test_db.add(endpoint)
    test_db.commit()

    contract = {"type": "object", "properties": {"price": {"type": "number"}}}
    baseline = Baseline(endpoint_id=endpoint.id, contract_json=contract)
    test_db.add(baseline)
    test_db.commit()

    with respx.mock:
        respx.get("https://api.example.com/products").mock(
            return_value=httpx.Response(200, json={"price": "4500"})
        )

        await run_check_for_endpoint(endpoint.id)

    saved_run = test_db.query(CheckRun).first()
    assert saved_run is not None
    assert saved_run.status == "changes_detected"
    assert len(saved_run.findings_json) == 1
    assert saved_run.findings_json[0]["change"] == "type_changed"


@pytest.mark.asyncio
async def test_schedule_and_unschedule_endpoint(test_db):
    start_scheduler()

    try:
        endpoint = Endpoint(name="Test API", url="https://api.example.com/test", interval_seconds=60)
        test_db.add(endpoint)
        test_db.commit()

        schedule_endpoint(endpoint.id, 60)

        job = scheduler.get_job(_get_job_id(endpoint.id))
        assert job is not None
        assert job.trigger.interval.total_seconds() == 60

        unschedule_endpoint(endpoint.id)

        job = scheduler.get_job(_get_job_id(endpoint.id))
        assert job is None
    finally:
        shutdown_scheduler(wait=False)


@pytest.mark.asyncio
async def test_load_active_endpoints(test_db):
    start_scheduler()

    try:
        endpoint1 = Endpoint(name="API 1", url="https://api.example.com/1", interval_seconds=60, is_active=True)
        endpoint2 = Endpoint(name="API 2", url="https://api.example.com/2", interval_seconds=120, is_active=True)
        endpoint3 = Endpoint(name="API 3", url="https://api.example.com/3", interval_seconds=30, is_active=False)
        test_db.add_all([endpoint1, endpoint2, endpoint3])
        test_db.commit()

        load_active_endpoints()

        job1 = scheduler.get_job(_get_job_id(endpoint1.id))
        job2 = scheduler.get_job(_get_job_id(endpoint2.id))
        job3 = scheduler.get_job(_get_job_id(endpoint3.id))

        assert job1 is not None
        assert job1.trigger.interval.total_seconds() == 60
        assert job2 is not None
        assert job2.trigger.interval.total_seconds() == 120
        assert job3 is None
    finally:
        shutdown_scheduler(wait=False)


@pytest.mark.asyncio
async def test_schedule_endpoint_updates_existing_job(test_db):
    start_scheduler()

    try:
        endpoint = Endpoint(name="Test API", url="https://api.example.com/test", interval_seconds=60)
        test_db.add(endpoint)
        test_db.commit()

        schedule_endpoint(endpoint.id, 60)
        job = scheduler.get_job(_get_job_id(endpoint.id))
        assert job.trigger.interval.total_seconds() == 60

        schedule_endpoint(endpoint.id, 30)
        job = scheduler.get_job(_get_job_id(endpoint.id))
        assert job.trigger.interval.total_seconds() == 30
    finally:
        shutdown_scheduler(wait=False)


@pytest.mark.asyncio
async def test_job_defaults_prevent_overlap(test_db):
    """Test that job defaults (coalesce=True, max_instances=1) are set."""
    start_scheduler()

    try:
        endpoint = Endpoint(name="Test API", url="https://api.example.com/test", interval_seconds=60)
        test_db.add(endpoint)
        test_db.commit()

        schedule_endpoint(endpoint.id, 60)
        job = scheduler.get_job(_get_job_id(endpoint.id))

        assert job.max_instances == 1
        assert job.coalesce is True
    finally:
        shutdown_scheduler(wait=False)