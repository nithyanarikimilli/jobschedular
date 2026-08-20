from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, DeadLetterJob, Job, JobStatus, JobLog, Project
from app.schemas.schemas import DeadLetterJobResponse

router = APIRouter()

@router.get("", response_model=List[DeadLetterJobResponse])
def get_dlq_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dlq_jobs = db.query(DeadLetterJob).join(Project).filter(
        Project.organization_id == current_user.organization_id
    ).order_by(DeadLetterJob.failed_at.desc()).all()
    return dlq_jobs

@router.post("/{id}/retry")
def retry_dlq_job(
    id: UUID,  # This can be the DeadLetterJob id or Job id. Let's resolve both.
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Resolve DeadLetterJob
    dlq_job = db.query(DeadLetterJob).join(Project).filter(
        (DeadLetterJob.id == id) | (DeadLetterJob.job_id == id),
        Project.organization_id == current_user.organization_id
    ).first()
    
    if not dlq_job:
        raise HTTPException(status_code=404, detail="Dead Letter job not found")

    job = db.query(Job).filter(Job.id == dlq_job.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Underlying Job not found")

    # Reset job for execution
    job.status = JobStatus.QUEUED
    job.retry_count = 0
    job.scheduled_at = datetime.utcnow()
    job.next_retry_at = None
    job.failure_reason = None
    db.add(job)

    # Delete Dead Letter record
    db.delete(dlq_job)

    # Log action
    log = JobLog(
        job_id=job.id,
        log_level="INFO",
        message="Manual retry of job from Dead Letter Queue requested. Status reset to QUEUED."
    )
    db.add(log)
    db.commit()

    return {"message": "Job successfully queued for retry.", "job_id": job.id}
