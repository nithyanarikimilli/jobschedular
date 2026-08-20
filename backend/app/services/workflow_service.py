from sqlalchemy.orm import Session
from app.models.models import Job, JobStatus, Workflow, WorkflowStatus, WorkflowDependency
from datetime import datetime
import logging

logger = logging.getLogger("smartqueue.workflow")

def evaluate_workflow_state(db: Session, workflow_id: str):
    """
    Evaluates the overall state of the workflow and updates its status.
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        return

    jobs = db.query(Job).filter(Job.workflow_id == workflow_id).all()
    if not jobs:
        return

    statuses = [j.status for j in jobs]

    if all(s == JobStatus.COMPLETED for s in statuses):
        workflow.status = WorkflowStatus.COMPLETED
    elif any(s in [JobStatus.FAILED, JobStatus.DLQ] for s in statuses):
        workflow.status = WorkflowStatus.FAILED
    elif any(s in [JobStatus.RUNNING, JobStatus.CLAIMED, JobStatus.QUEUED] for s in statuses):
        workflow.status = WorkflowStatus.RUNNING
    else:
        workflow.status = WorkflowStatus.PENDING

    db.add(workflow)
    db.commit()

def resolve_downstream_dependencies(db: Session, completed_job: Job):
    """
    Finds child jobs of a completed job, checks if all their parents are completed,
    and transitions them from BLOCKED to QUEUED.
    """
    if not completed_job.workflow_id:
        return

    # Find dependencies where this completed job is the parent
    deps = db.query(WorkflowDependency).filter(
        WorkflowDependency.parent_job_id == completed_job.id
    ).all()

    for dep in deps:
        child_job = db.query(Job).filter(Job.id == dep.child_job_id).first()
        if not child_job or child_job.status != JobStatus.BLOCKED:
            continue

        # Check if all parent dependencies of this child job are completed
        parent_deps = db.query(WorkflowDependency).filter(
            WorkflowDependency.child_job_id == child_job.id
        ).all()

        all_parents_completed = True
        for p_dep in parent_deps:
            parent_job = db.query(Job).filter(Job.id == p_dep.parent_job_id).first()
            if not parent_job or parent_job.status != JobStatus.COMPLETED:
                all_parents_completed = False
                break

        if all_parents_completed:
            child_job.status = JobStatus.QUEUED
            child_job.scheduled_at = datetime.utcnow()
            db.add(child_job)
            logger.info(f"Workflow Job {child_job.id} ({child_job.task_name}) unblocked and queued.")

    db.commit()
    evaluate_workflow_state(db, completed_job.workflow_id)
