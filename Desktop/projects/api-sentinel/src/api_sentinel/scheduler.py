import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .db import SessionLocal, Endpoint, Baseline, CheckRun
from .monitoring_service import run_monitoring_check
logger = logging.getLogger(__name__)

async def run_check_for_endpoint(endpoint_id:int):
    """background tak , run a check for a specific endpoint"""
    
    db = SessionLocal()
    try:
        endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
        if not endpoint or not endpoint.is_active:
            logger.warning(f"Endpoint {endpoint_id} not found or inactive.")
            return
        
        #2
        baseline = db.query(Baseline).filter(Baseline.endpoint_id == endpoint_id).order_by(Baseline.version.desc()).first()
        
        contract = baseline.contract_json if baseline else None
        
        #3
        logger.info(f"Running check for endpoint {endpoint.name} ({endpoint.url})")
        result = await run_monitoring_check(endpoint.url,approved_contract= contract)
        
        
        #4
        if result["status"] != "awaiting_approval":
            check_run = CheckRun(
                endpoint_id = endpoint.id,
                status = result["status"],
                duration_ms = result["duration_ms"],
                findings_json = result["findings"]
            )
            db.add(check_run)
            db.commit()
            
    except Exception as e:
        logger.error(f"Error running check for endpoint {endpoint_id}: {e}")
        db.rollback()
    finally:
        db.close()
        
def start_scheduler():
    """initialize and start the backgorund scheduler for periodic checks"""
    scheduler = AsyncIOScheduler()
    
    scheduler.start()
    logger.info("backGRound Scheduler started.")
    return scheduler
