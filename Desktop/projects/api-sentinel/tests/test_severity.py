import pytest
from api_sentinel.severity import classify_finding, Severity, get_severity_priority, is_breaking_change


def test_classify_critical_required_field_missing():
    severity = classify_finding(
        change_type="field_missing",
        json_path="$.id",
        is_required_field=True,
    )
    assert severity == Severity.CRITICAL


def test_classify_critical_required_field_type_changed():
    severity = classify_finding(
        change_type="type_changed",
        json_path="$.price",
        is_required_field=True,
    )
    assert severity == Severity.CRITICAL


def test_classify_high_type_changed():
    severity = classify_finding(
        change_type="type_changed",
        json_path="$.price",
        is_required_field=False,
    )
    assert severity == Severity.HIGH


def test_classify_high_field_missing():
    severity = classify_finding(
        change_type="field_missing",
        json_path="$.name",
        is_required_field=False,
    )
    assert severity == Severity.HIGH


def test_classify_medium_field_added():
    severity = classify_finding(
        change_type="field_added",
        json_path="$.new_field",
    )
    assert severity == Severity.MEDIUM


def test_classify_low_value_changed():
    severity = classify_finding(
        change_type="value_changed",
        json_path="$.price",
    )
    assert severity == Severity.LOW


def test_classify_info_default():
    severity = classify_finding(
        change_type="unknown_change",
        json_path="$.something",
    )
    assert severity == Severity.INFO


def test_severity_priority_order():
    assert get_severity_priority(Severity.CRITICAL) == 5
    assert get_severity_priority(Severity.HIGH) == 4
    assert get_severity_priority(Severity.MEDIUM) == 3
    assert get_severity_priority(Severity.LOW) == 2
    assert get_severity_priority(Severity.INFO) == 1


def test_is_breaking_change():
    assert is_breaking_change(Severity.CRITICAL) is True
    assert is_breaking_change(Severity.HIGH) is True
    assert is_breaking_change(Severity.MEDIUM) is False
    assert is_breaking_change(Severity.LOW) is False
    assert is_breaking_change(Severity.INFO) is False


@pytest.mark.asyncio
async def test_finding_entity_persistence():
    """Test that Finding entity can be created and queried."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from api_sentinel.db import Base, Finding, CheckRun, Endpoint
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create endpoint and check run
        endpoint = Endpoint(name="Test", url="https://api.example.com", interval_seconds=60)
        session.add(endpoint)
        session.commit()
        
        check_run = CheckRun(endpoint_id=endpoint.id, status="healthy", duration_ms=100)
        session.add(check_run)
        session.commit()
        
        # Create findings
        finding1 = Finding(
            check_run_id=check_run.id,
            json_path="$.price",
            change_type="type_changed",
            expected="number",
            actual="string",
            severity="high",
            review_status="new",
        )
        finding2 = Finding(
            check_run_id=check_run.id,
            json_path="$.new_field",
            change_type="field_added",
            expected="missing",
            actual="present",
            severity="medium",
            review_status="new",
        )
        session.add_all([finding1, finding2])
        session.commit()
        
        # Query findings
        findings = session.query(Finding).filter(Finding.check_run_id == check_run.id).all()
        assert len(findings) == 2
        
        # Check relationship
        assert len(check_run.findings) == 2
        assert check_run.findings[0].severity in ("high", "medium")
        
        # Check indexes work
        high_findings = session.query(Finding).filter(Finding.severity == "high").all()
        assert len(high_findings) >= 1
        
    finally:
        session.close()