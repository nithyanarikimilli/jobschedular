import sys
import os
import time
import uuid
import logging
import traceback
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add workspace backend root to path to prevent import issues in docker/workers
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import (
    Job, JobStatus, JobExecution, JobLog, Queue, Worker, WorkerStatus, 
    WorkerHeartbeat, ScheduledJob, DeadLetterJob, AIAnalysis, BackoffType,
    WorkflowStatus
)
from app.services.workflow_service import resolve_downstream_dependencies, evaluate_workflow_state
from app.services.ai_analyzer import analyze_job_failure

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("smartqueue.scheduler")

# Dummy task functions matching task_name strings
def task_success(payload: dict) -> dict:
    logger.info(f"Executing task_success with payload: {payload}")
    time.sleep(1.0)
    return {"status": "success", "result": f"Processed {payload.get('data', 'no-data')}"}

def task_fail(payload: dict) -> dict:
    logger.info(f"Executing task_fail with payload: {payload}")
    time.sleep(0.5)
    raise Exception("ApplicationError: Intentional test failure triggered.")

def task_network_error(payload: dict) -> dict:
    logger.info(f"Executing task_network_error")
    time.sleep(0.5)
    raise Exception("ConnectionTimeout: Failed to connect to port 443 at backend.internal.net. Connection refused.")

def task_validation_error(payload: dict) -> dict:
    logger.info(f"Executing task_validation_error")
    time.sleep(0.5)
    raise ValueError("ValueError: The input data must contain non-null email field.")

def task_workflow_step(payload: dict) -> dict:
    logger.info(f"Executing workflow step: {payload.get('step', 'unknown')}")
    time.sleep(0.8)
    return {"status": "success", "step": payload.get("step")}

TASK_REGISTRY = {
    "task_success": task_success,
    "task_fail": task_fail,
    "task_network_error": task_network_error,
    "task_validation_error": task_validation_error,
    "task_workflow_step": task_workflow_step
}

def calculate_backoff(backoff_type: BackoffType, base_delay: int, retry_count: int) -> int:
    """
    Computes retry delays using the configured strategy:
    - FIXED: delay is base_delay
    - LINEAR: base_delay * retry_count
    - EXPONENTIAL: base_delay * (2 ** retry_count)
    """
    if backoff_type == BackoffType.LINEAR:
        return base_delay * (retry_count + 1)
    elif backoff_type == BackoffType.EXPONENTIAL:
        return base_delay * (2 ** retry_count)
    return base_delay  # Fixed default

def claim_jobs(db: Session, worker_id: uuid.UUID, limit: int = 1) -> List[Job]:
    """
    Claims jobs atomically using SELECT FOR UPDATE SKIP LOCKED, respecting queue concurrency limits.
    """
    # 1. Fetch active, non-paused queues
    queues = db.query(Queue).filter(Queue.is_paused == False).all()
    claimed_jobs = []

    for queue in queues:
        # Check active slots for this queue
        active_count = db.query(Job).filter(
            Job.queue_id == queue.id,
            Job.status.in_([JobStatus.CLAIMED, JobStatus.RUNNING])
        ).count()

        slots_available = queue.max_concurrency - active_count
        if slots_available <= 0:
            continue

        claim_limit = min(limit - len(claimed_jobs), slots_available)
        if claim_limit <= 0:
            break

        # Acquire lock and claim jobs for this queue
        q_query = db.query(Job).filter(
            Job.queue_id == queue.id,
            Job.status == JobStatus.QUEUED,
            Job.scheduled_at <= datetime.utcnow()
        ).order_by(
            Job.priority.desc(),
            Job.created_at.asc()
        ).limit(claim_limit)

        if db.bind.dialect.name == "sqlite":
            jobs = q_query.all()
        else:
            jobs = q_query.with_for_update(skip_locked=True).all()

        for job in jobs:
            job.status = JobStatus.CLAIMED
            job.worker_id = worker_id
            db.add(job)
            claimed_jobs.append(job)

    if claimed_jobs:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error committing claimed jobs transaction: {e}")
            return []

    return claimed_jobs

def handle_job_failure(db: Session, job: Job, execution: JobExecution, error_msg: str, trace_str: str):
    """
    Processes job failure, executing retries or routing to DLQ with AI diagnostics.
    """
    job.retry_count += 1
    job.failure_reason = error_msg
    
    execution.status = "FAILED"
    execution.ended_at = datetime.utcnow()
    execution.duration = (execution.ended_at - execution.started_at).total_seconds()
    execution.error_message = error_msg
    execution.stack_trace = trace_str
    db.add(execution)
    db.commit() # save execution so we have its ID for analysis

    # Collect logs for AI failure analysis
    logs = db.query(JobLog).filter(JobLog.job_id == job.id).order_by(JobLog.created_at.desc()).limit(10).all()
    logs_str = "\n".join([f"[{l.log_level}] {l.message}" for l in reversed(logs)])

    # Analyze failure
    analysis_result = analyze_job_failure(
        error_message=error_msg,
        stack_trace=trace_str,
        logs=logs_str,
        retry_count=job.retry_count - 1,
        duration=execution.duration
    )

    # Save AI diagnostics
    ai_analysis = AIAnalysis(
        execution_id=execution.id,
        failure_reason=analysis_result["failure_reason"],
        severity=analysis_result["severity"],
        suggested_solution=analysis_result["suggested_solution"],
        is_temporary=analysis_result["is_temporary"]
    )
    db.add(ai_analysis)

    # Retry calculation
    should_retry = (job.retry_count <= job.max_retries) and analysis_result["is_temporary"]

    if should_retry:
        # Determine delay
        delay_sec = 5
        if job.retry_policy:
            delay_sec = calculate_backoff(
                backoff_type=job.retry_policy.backoff_type,
                base_delay=job.retry_policy.base_delay,
                retry_count=job.retry_count - 1
            )
        
        job.status = JobStatus.QUEUED
        job.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_sec)
        job.scheduled_at = job.next_retry_at  # Update schedule for worker claim
        
        # Log retry intention
        log_entry = JobLog(
            job_id=job.id,
            execution_id=execution.id,
            log_level="WARNING",
            message=f"Attempt failed. Retrying in {delay_sec} seconds (Attempt {job.retry_count}/{job.max_retries})"
        )
        db.add(log_entry)
        logger.info(f"Job {job.id} failed. Retrying in {delay_sec}s.")
    else:
        # Move to Dead Letter Queue (DLQ)
        job.status = JobStatus.DLQ
        dlq_job = DeadLetterJob(
            job_id=job.id,
            project_id=job.project_id,
            queue_id=job.queue_id,
            execution_id=execution.id,
            task_name=job.task_name,
            payload=job.payload,
            failed_at=datetime.utcnow(),
            failure_reason=analysis_result["failure_reason"],
            error_message=error_msg,
            stack_trace=trace_str
        )
        db.add(dlq_job)

        log_entry = JobLog(
            job_id=job.id,
            execution_id=execution.id,
            log_level="ERROR",
            message=f"Job failed permanently. Sent to Dead Letter Queue. Reason: {analysis_result['failure_reason']}"
        )
        db.add(log_entry)
        logger.error(f"Job {job.id} failed permanently and sent to Dead Letter Queue.")
        
        # If job is part of a workflow, we must update the workflow status to FAILED
        if job.workflow_id:
            evaluate_workflow_state(db, job.workflow_id)

    db.add(job)
    db.commit()

class WorkerRunner:
    def __init__(self, name: str = None):
        self.worker_id = uuid.uuid4()
        self.name = name or f"Worker-{self.worker_id.hex[:6]}"
        self.is_running = False
        self.thread = None

    def start(self):
        self.is_running = True
        # Register worker in DB
        db = SessionLocal()
        worker = Worker(
            id=self.worker_id,
            name=self.name,
            status=WorkerStatus.IDLE,
            last_heartbeat=datetime.utcnow(),
            jobs_completed=0,
            jobs_failed=0,
            system_info={"cpu": 5, "memory": 20}
        )
        db.add(worker)
        db.commit()
        db.close()
        
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Worker {self.name} registered and started execution loop.")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        # Update status to OFFLINE
        db = SessionLocal()
        worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
        if worker:
            worker.status = WorkerStatus.OFFLINE
            db.commit()
        db.close()
        logger.info(f"Worker {self.name} shut down gracefully.")

    def _send_heartbeat(self):
        db = SessionLocal()
        worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
        if worker:
            worker.last_heartbeat = datetime.utcnow()
            heartbeat = WorkerHeartbeat(
                worker_id=self.worker_id,
                status=worker.status.value,
                system_info={"cpu": 12, "memory": 45}  # Simulated
            )
            db.add(heartbeat)
            db.commit()
        db.close()

    def _run_loop(self):
        last_hb = 0
        while self.is_running:
            # 1. Heartbeat check (every 5 seconds)
            now = time.time()
            if now - last_hb >= 5:
                self._send_heartbeat()
                last_hb = now

            # 2. Claim next job
            db = SessionLocal()
            jobs = claim_jobs(db, self.worker_id, limit=1)
            if not jobs:
                db.close()
                time.sleep(1.0)
                continue

            job = jobs[0]
            worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
            if worker:
                worker.status = WorkerStatus.BUSY
                db.commit()

            # 3. Create execution and execute
            job.status = JobStatus.RUNNING
            execution = JobExecution(
                job_id=job.id,
                worker_id=self.worker_id,
                attempt_number=job.retry_count + 1,
                status="RUNNING",
                started_at=datetime.utcnow()
            )
            db.add(job)
            db.add(execution)
            db.commit()

            # Log execution start
            log_start = JobLog(
                job_id=job.id,
                execution_id=execution.id,
                log_level="INFO",
                message=f"Starting job execution: {job.task_name} (Attempt {job.retry_count + 1})"
            )
            db.add(log_start)
            db.commit()

            # Execute actual task
            task_fn = TASK_REGISTRY.get(job.task_name)
            success = False
            error_msg = ""
            trace_str = ""

            try:
                if not task_fn:
                    raise NotImplementedError(f"Task type {job.task_name} is not registered in this worker.")
                
                # Run the task function
                result = task_fn(job.payload)
                success = True
                
                # Log success
                log_success = JobLog(
                    job_id=job.id,
                    execution_id=execution.id,
                    log_level="INFO",
                    message=f"Job completed successfully. Output: {result}"
                )
                db.add(log_success)
                
            except Exception as e:
                success = False
                error_msg = str(e)
                trace_str = traceback.format_exc()
                log_error = JobLog(
                    job_id=job.id,
                    execution_id=execution.id,
                    log_level="ERROR",
                    message=f"Job failed with error: {error_msg}"
                )
                db.add(log_error)
                db.commit()

            if success:
                # Update status to completed
                job.status = JobStatus.COMPLETED
                execution.status = "COMPLETED"
                execution.ended_at = datetime.utcnow()
                execution.duration = (execution.ended_at - execution.started_at).total_seconds()
                
                worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
                if worker:
                    worker.jobs_completed += 1
                db.commit()
                
                # Workflow dependency triggers
                resolve_downstream_dependencies(db, job)
            else:
                worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
                if worker:
                    worker.jobs_failed += 1
                db.commit()
                
                # Handle failure (Retries vs DLQ)
                handle_job_failure(db, job, execution, error_msg, trace_str)

            # Set worker status back to IDLE
            worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
            if worker:
                worker.status = WorkerStatus.IDLE
            db.commit()
            db.close()

def recover_failed_workers(db: Session):
    """
    Recover orphaned jobs from workers that missed heartbeats.
    """
    cutoff = datetime.utcnow() - timedelta(seconds=30)
    offline_workers = db.query(Worker).filter(
        Worker.status != WorkerStatus.OFFLINE,
        Worker.last_heartbeat < cutoff
    ).all()

    for worker in offline_workers:
        worker.status = WorkerStatus.OFFLINE
        db.add(worker)
        logger.warning(f"Worker {worker.id} ({worker.name}) went OFFLINE. Recovering jobs.")

        running_jobs = db.query(Job).filter(
            Job.worker_id == worker.id,
            Job.status.in_([JobStatus.CLAIMED, JobStatus.RUNNING])
        ).all()

        for job in running_jobs:
            job.status = JobStatus.QUEUED
            job.worker_id = None
            job.failure_reason = f"Worker {worker.name} disconnected"
            
            execution = JobExecution(
                job_id=job.id,
                worker_id=worker.id,
                attempt_number=job.retry_count + 1,
                status="FAILED",
                started_at=datetime.utcnow(),
                ended_at=datetime.utcnow(),
                duration=0.0,
                error_message="Worker disconnected",
                stack_trace="Orphaned job recovered due to worker heartbeat failure"
            )
            db.add(execution)
            db.add(job)
            logger.info(f"Re-queued orphaned job {job.id} from worker {worker.name}")

    db.commit()

def process_recurring_jobs(db: Session):
    """
    Evaluate recurring cron schedules and inject jobs when due.
    """
    from croniter import croniter
    now = datetime.utcnow()
    scheduled = db.query(ScheduledJob).filter(ScheduledJob.is_active == True).all()

    for s_job in scheduled:
        if not s_job.next_run_at:
            cron = croniter(s_job.cron_expression, now)
            s_job.next_run_at = cron.get_next(datetime)
            db.add(s_job)
            continue

        if s_job.next_run_at <= now:
            # Trigger job instance
            new_job = Job(
                project_id=s_job.project_id,
                queue_id=s_job.queue_id,
                retry_policy_id=s_job.retry_policy_id,
                task_name=s_job.task_name,
                payload=s_job.payload,
                priority=s_job.priority,
                status=JobStatus.QUEUED,
                scheduled_at=now
            )
            db.add(new_job)

            s_job.last_run_at = now
            cron = croniter(s_job.cron_expression, now)
            s_job.next_run_at = cron.get_next(datetime)
            db.add(s_job)
            logger.info(f"Injected recurring cron job instance: {s_job.task_name}")

    db.commit()

def run_scheduler_daemon(stop_event: threading.Event = None):
    """
    Background loop managing workers status and recurring cron injection.
    """
    logger.info("Scheduler daemon started.")
    while stop_event is None or not stop_event.is_set():
        db = SessionLocal()
        try:
            recover_failed_workers(db)
            process_recurring_jobs(db)
        except Exception as e:
            logger.error(f"Scheduler daemon cycle error: {e}")
        finally:
            db.close()
        time.sleep(5)
    logger.info("Scheduler daemon stopped.")

if __name__ == "__main__":
    worker_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Initialize Database Tables first
    from app.core.database import Base, engine
    Base.metadata.create_all(bind=engine)
    
    # Start Scheduler Daemon in background
    stop_event = threading.Event()
    daemon_thread = threading.Thread(target=run_scheduler_daemon, args=(stop_event,), daemon=True)
    daemon_thread.start()

    worker = WorkerRunner(name=worker_name)
    worker.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received.")
        worker.stop()
        stop_event.set()
        daemon_thread.join()
