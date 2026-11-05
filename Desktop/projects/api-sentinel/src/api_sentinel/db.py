from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///sentinel.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utc_now():
    """Helper to return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    method = Column(String, default="GET")
    headers = Column(JSON, default=dict)
    query_params = Column(JSON, default=dict)
    auth_config = Column(JSON, default=dict)
    timeout_seconds = Column(Integer, default=30)
    expected_status_codes = Column(JSON, default=lambda: [200])
    response_format = Column(String, default="json")
    interval_seconds = Column(Integer, default=300)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    baselines = relationship("Baseline", back_populates="endpoint", cascade="all, delete-orphan")
    check_runs = relationship("CheckRun", back_populates="endpoint", cascade="all, delete-orphan")


class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"))
    contract_json = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    approved_at = Column(DateTime(timezone=True), default=utc_now)

    endpoint = relationship("Endpoint", back_populates="baselines")


class CheckRun(Base):
    __tablename__ = "check_runs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"))
    baseline_version = Column(Integer, nullable=True)
    status = Column(String, nullable=False)
    duration_ms = Column(Float)
    findings_json = Column(JSON, default=list)
    checked_at = Column(DateTime(timezone=True), default=utc_now)

    endpoint = relationship("Endpoint", back_populates="check_runs")
    findings = relationship("Finding", back_populates="check_run", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    check_run_id = Column(Integer, ForeignKey("check_runs.id"), nullable=False)
    json_path = Column(String, nullable=False)
    change_type = Column(String, nullable=False)
    expected = Column(String, nullable=True)
    actual = Column(String, nullable=True)
    severity = Column(String, nullable=False, default="info")
    review_status = Column(String, nullable=False, default="new")
    detected_at = Column(DateTime(timezone=True), default=utc_now)

    check_run = relationship("CheckRun", back_populates="findings")

    __table_args__ = (
        Index("ix_findings_check_run_id", "check_run_id"),
        Index("ix_findings_severity", "severity"),
        Index("ix_findings_review_status", "review_status"),
    )


def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI later, but useful for testing now."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()