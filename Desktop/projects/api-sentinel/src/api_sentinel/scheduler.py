import logging
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from .db import SessionLocal, Endpoint, Baseline, CheckRun, Finding
from .monitoring_service import run_monitoring_check

logger = logging.getLogger(__name__)

jobstores = {"default": MemoryJobStore()}
executors = {"default": AsyncIOExecutor()}
job_defaults = {"coalesce": True, "max_instances": 1}

scheduler = AsyncIOScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)


async def run_check_for_endpoint(endpoint_id: int, test_mode: bool = False):
    """Background task: run a check for a specific endpoint."""
    db = SessionLocal()
    try:
        endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
        if not endpoint or not endpoint.is_active:
            logger.warning(f"Endpoint {endpoint_id} not found or inactive.")
            return

        baseline = (
            db.query(Baseline)
            .filter(Baseline.endpoint_id == endpoint_id)
            .order_by(Baseline.version.desc())
            .first()
        )

        contract = baseline.contract_json if baseline else None

        logger.info(f"Running check for endpoint {endpoint.name} ({endpoint.url})")
        result = await run_monitoring_check(
            url=endpoint.url,
            approved_contract=contract,
            method=endpoint.method,
            headers=endpoint.headers,
            query_params=endpoint.query_params,
            auth_config=endpoint.auth_config,
            timeout_seconds=endpoint.timeout_seconds,
            expected_status_codes=endpoint.expected_status_codes,
            test_mode=test_mode,
        )

        if result["status"] != "awaiting_approval":
            check_run = CheckRun(
                endpoint_id=endpoint.id,
                baseline_version=baseline.version if baseline else None,
                status=result["status"],
                duration_ms=result["duration_ms"],
                findings_json=result["findings"],
            )
            db.add(check_run)
            db.flush()  # Get the check_run.id

            # Save individual findings to Finding table
            for finding in result["findings"]:
                finding_obj = Finding(
                    check_run_id=check_run.id,
                    json_path=finding["path"],
                    change_type=finding["change"],
                    expected=str(finding.get("expected", "")),
                    actual=str(finding.get("actual", "")),
                    severity=finding.get("severity", "info"),
                    review_status="new",
                )
                db.add(finding_obj)

            db.commit()

    except Exception as e:
        logger.error(f"Error running check for endpoint {endpoint_id}: {e}")
        db.rollback()
    finally:
        db.close()


def _get_job_id(endpoint_id: int) -> str:
    """Generate consistent job ID for an endpoint."""
    return f"endpoint_{endpoint_id}"


def schedule_endpoint(endpoint_id: int, interval_seconds: int):
    """Add or update a scheduled job for an endpoint."""
    job_id = _get_job_id(endpoint_id)
    existing_job = scheduler.get_job(job_id)

    if existing_job:
        existing_job.reschedule(trigger=IntervalTrigger(seconds=interval_seconds))
        logger.info(f"Updated schedule for endpoint {endpoint_id} to {interval_seconds}s")
    else:
        scheduler.add_job(
            run_check_for_endpoint,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id=job_id,
            args=[endpoint_id],
            name=f"Monitor endpoint {endpoint_id}",
        )
        logger.info(f"Scheduled endpoint {endpoint_id} every {interval_seconds}s")


def unschedule_endpoint(endpoint_id: int):
    """Remove a scheduled job for an endpoint."""
    job_id = _get_job_id(endpoint_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Unscheduled endpoint {endpoint_id}")


def load_active_endpoints():
    """Load all active endpoints from database and schedule them."""
    db = SessionLocal()
    try:
        endpoints = db.query(Endpoint).filter(Endpoint.is_active == True).all()
        for endpoint in endpoints:
            schedule_endpoint(endpoint.id, endpoint.interval_seconds)
        logger.info(f"Loaded {len(endpoints)} active endpoints into scheduler")
    finally:
        db.close()


def start_scheduler():
    """Initialize and start the background scheduler."""
    if scheduler.running:
        logger.warning("Scheduler already running")
        return scheduler

    scheduler.start()
    load_active_endpoints()
    logger.info("Background scheduler started.")
    return scheduler


def shutdown_scheduler(wait: bool = True):
    """Gracefully shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=wait)
        logger.info("Background scheduler stopped.")


@asynccontextmanager
async def scheduler_lifespan(app):
    """FastAPI lifespan handler for scheduler."""
    start_scheduler()
    yield
    shutdown_scheduler(wait=True)