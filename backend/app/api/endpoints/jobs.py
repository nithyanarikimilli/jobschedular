from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import (
    User, Job, Queue, Project, JobStatus, JobExecution, JobLog, 
    RetryPolicy, DeadLetterJob, BackoffType
)
from app.schemas.schemas import JobCreate, JobResponse, JobExecutionResponse, JobLogResponse
import logging

router = APIRouter()
logger = logging.getLogger("smartqueue.jobs")

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project belongs to user's org
    project = db.query(Project).filter(
        Project.id == job_in.project_id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find or create queue by name
    queue = db.query(Queue).filter(
        Queue.project_id == project.id,
        Queue.name == job_in.queue_name
    ).first()
    if not queue:
        queue = Queue(
            project_id=project.id,
            name=job_in.queue_name,
            description=f"Auto-created queue for {job_in.queue_name}",
            priority=1,
            max_concurrency=10
        )
        db.add(queue)
        db.flush()

    # Retry policy configuration
    retry_policy_id = None
    max_retries = 3
    if job_in.retry_policy:
        policy = RetryPolicy(
            name=job_in.retry_policy.name,
            backoff_type=job_in.retry_policy.backoff_type,
            base_delay=job_in.retry_policy.base_delay,
            max_retries=job_in.retry_policy.max_retries
        )
        db.add(policy)
        db.flush()
        retry_policy_id = policy.id
        max_retries = policy.max_retries
    else:
        # Link to first available policy or default
        default_policy = db.query(RetryPolicy).first()
        if default_policy:
            retry_policy_id = default_policy.id
            max_retries = default_policy.max_retries

    # Delay / Scheduled calculation
    scheduled_at = job_in.scheduled_at
    if not scheduled_at:
        # Check if delay is in payload
        delay = job_in.payload.get("delay")
        if isinstance(delay, (int, float)):
            scheduled_at = datetime.utcnow() + timedelta(seconds=delay)
        else:
            scheduled_at = datetime.utcnow()

    # Create job
    job = Job(
        project_id=project.id,
        queue_id=queue.id,
        workflow_id=job_in.workflow_id,
        retry_policy_id=retry_policy_id,
        task_name=job_in.task_name,
        payload=job_in.payload,
        status=JobStatus.BLOCKED if job_in.workflow_id else JobStatus.QUEUED,
        priority=job_in.priority,
        retry_count=0,
        max_retries=max_retries,
        scheduled_at=scheduled_at
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Initial log
    log = JobLog(
        job_id=job.id,
        log_level="INFO",
        message=f"Job created with status: {job.status.value}"
    )
    db.add(log)
    db.commit()

    return job

@router.get("", response_model=List[JobResponse])
def get_jobs(
    project_id: Optional[UUID] = None,
    queue_id: Optional[UUID] = None,
    status: Optional[JobStatus] = None,
    priority: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|priority|scheduled_at|status)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Job).join(Project).filter(Project.organization_id == current_user.organization_id)

    if project_id:
        query = query.filter(Job.project_id == project_id)
    if queue_id:
        query = query.filter(Job.queue_id == queue_id)
    if status:
        query = query.filter(Job.status == status)
    if priority is not None:
        query = query.filter(Job.priority == priority)
    if search:
        query = query.filter(Job.task_name.ilike(f"%{search}%"))

    # Sorting
    order_col = getattr(Job, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(order_col))

    return query.offset(offset).limit(limit).all()

@router.get("/{id}", response_model=JobResponse)
def get_job(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).join(Project).filter(
        Job.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{id}/retry", response_model=JobResponse)
def retry_job(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).join(Project).filter(
        Job.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Reset retry count and set back to QUEUED
    job.status = JobStatus.QUEUED
    job.retry_count = 0
    job.scheduled_at = datetime.utcnow()
    job.next_retry_at = None
    job.failure_reason = None
    db.add(job)

    # Clean Dead Letter record if present
    dlq_record = db.query(DeadLetterJob).filter(DeadLetterJob.job_id == job.id).first()
    if dlq_record:
        db.delete(dlq_record)

    # Log action
    log = JobLog(
        job_id=job.id,
        log_level="INFO",
        message="Manual job retry requested. Status reset to QUEUED."
    )
    db.add(log)
    db.commit()
    db.refresh(job)

    return job

@router.post("/{id}/cancel", response_model=JobResponse)
def cancel_job(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).join(Project).filter(
        Job.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DLQ]:
         raise HTTPException(status_code=400, detail="Cannot cancel a completed or failed job.")

    job.status = JobStatus.FAILED
    job.failure_reason = "Cancelled by user"
    db.add(job)

    # Log action
    log = JobLog(
        job_id=job.id,
        log_level="WARNING",
        message="Job cancelled by user request."
    )
    db.add(log)
    db.commit()
    db.refresh(job)

    return job

@router.get("/{id}/executions", response_model=List[JobExecutionResponse])
def get_job_executions(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify job access
    job = db.query(Job).join(Project).filter(
        Job.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    executions = db.query(JobExecution).filter(JobExecution.job_id == id).order_by(desc(JobExecution.started_at)).all()
    return executions

@router.get("/{id}/logs", response_model=List[JobLogResponse])
def get_job_logs(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify job access
    job = db.query(Job).join(Project).filter(
        Job.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logs = db.query(JobLog).filter(JobLog.job_id == id).order_by(asc(JobLog.created_at)).all()
    return logs
