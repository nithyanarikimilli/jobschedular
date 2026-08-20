from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Queue, Job, JobStatus, JobExecution, Project
from app.schemas.schemas import QueueCreate, QueueUpdate, QueueResponse, QueueStats

router = APIRouter()

@router.get("", response_model=List[QueueResponse])
def get_queues(
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Queue).join(Project).filter(Project.organization_id == current_user.organization_id)
    if project_id:
        query = query.filter(Queue.project_id == project_id)
    return query.all()

@router.post("", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
def create_queue(
    queue_in: QueueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project exists and belongs to organization
    project = db.query(Project).filter(
        Project.id == queue_in.project_id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if queue name already exists in this project
    existing = db.query(Queue).filter(
        Queue.project_id == queue_in.project_id,
        Queue.name == queue_in.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Queue name already exists in this project")

    queue = Queue(
        project_id=queue_in.project_id,
        name=queue_in.name,
        description=queue_in.description,
        priority=queue_in.priority,
        max_concurrency=queue_in.max_concurrency
    )
    db.add(queue)
    db.commit()
    db.refresh(queue)
    return queue

@router.get("/{id}", response_model=QueueResponse)
def get_queue(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    queue = db.query(Queue).join(Project).filter(
        Queue.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    return queue

@router.put("/{id}", response_model=QueueResponse)
def update_queue(
    id: UUID,
    queue_in: QueueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    queue = db.query(Queue).join(Project).filter(
        Queue.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    if queue_in.description is not None:
        queue.description = queue_in.description
    if queue_in.priority is not None:
        queue.priority = queue_in.priority
    if queue_in.max_concurrency is not None:
        queue.max_concurrency = queue_in.max_concurrency
    if queue_in.is_paused is not None:
        queue.is_paused = queue_in.is_paused

    db.add(queue)
    db.commit()
    db.refresh(queue)
    return queue

@router.post("/{id}/pause", response_model=QueueResponse)
def pause_queue(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    queue = db.query(Queue).join(Project).filter(
        Queue.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    queue.is_paused = True
    db.commit()
    return queue

@router.post("/{id}/resume", response_model=QueueResponse)
def resume_queue(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    queue = db.query(Queue).join(Project).filter(
        Queue.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    queue.is_paused = False
    db.commit()
    return queue

@router.get("/{id}/stats", response_model=QueueStats)
def get_queue_stats(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    queue = db.query(Queue).join(Project).filter(
        Queue.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    # Queue depth (jobs QUEUED with scheduled_at <= now)
    depth = db.query(Job).filter(
        Job.queue_id == queue.id,
        Job.status == JobStatus.QUEUED,
        Job.scheduled_at <= datetime.utcnow()
    ).count()

    # Running jobs (CLAIMED or RUNNING)
    running_jobs = db.query(Job).filter(
        Job.queue_id == queue.id,
        Job.status.in_([JobStatus.CLAIMED, JobStatus.RUNNING])
    ).count()

    # Waiting jobs (scheduled in the future)
    waiting_jobs = db.query(Job).filter(
        Job.queue_id == queue.id,
        Job.status == JobStatus.QUEUED,
        Job.scheduled_at > datetime.utcnow()
    ).count()

    # Executions in the last 24h
    day_ago = datetime.utcnow() - timedelta(days=1)
    executions = db.query(JobExecution).join(Job).filter(
        Job.queue_id == queue.id,
        JobExecution.started_at >= day_ago
    ).all()

    total_execs = len(executions)
    failed_execs = sum(1 for e in executions if e.status == "FAILED")
    success_execs = sum(1 for e in executions if e.status == "COMPLETED")
    
    avg_execution_time = 0.0
    if success_execs > 0:
        durations = [e.duration for e in executions if e.status == "COMPLETED" and e.duration is not None]
        avg_execution_time = sum(durations) / len(durations) if durations else 0.0

    failure_rate = (failed_execs / total_execs) if total_execs > 0 else 0.0

    # DLQ count
    dlq_count = db.query(Job).filter(
        Job.queue_id == queue.id,
        Job.status == JobStatus.DLQ
    ).count()

    # Health score calculation
    # Base is 100
    health_score = 100
    # deduct for DLQ jobs
    if dlq_count > 0:
        health_score -= min(dlq_count * 10, 40)
    # deduct for failure rate
    if failure_rate > 0:
        health_score -= min(int(failure_rate * 50), 40)
    # deduct for recent failures
    recent_failed_jobs = db.query(Job).filter(
        Job.queue_id == queue.id,
        Job.status == JobStatus.FAILED
    ).count()
    if recent_failed_jobs > 0:
        health_score -= min(recent_failed_jobs * 5, 20)

    health_score = max(0, health_score)

    # Overload warnings
    is_overloaded = False
    if (depth + running_jobs) >= (queue.max_concurrency * 1.5) or depth > 20:
        is_overloaded = True

    return {
        "queue_name": queue.name,
        "depth": depth,
        "running_jobs": running_jobs,
        "waiting_jobs": waiting_jobs,
        "worker_capacity": queue.max_concurrency,
        "avg_execution_time": round(avg_execution_time, 2),
        "failure_rate": round(failure_rate, 2),
        "health_score": health_score,
        "is_overloaded": is_overloaded
    }
