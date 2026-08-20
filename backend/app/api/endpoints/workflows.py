from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import (
    User, Workflow, Job, WorkflowDependency, Queue, Project, 
    JobStatus, WorkflowStatus
)
from app.schemas.schemas import WorkflowCreate, WorkflowResponse

router = APIRouter()

@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project
    project = db.query(Project).filter(
        Project.id == workflow_in.project_id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # 1. Create Workflow Record
        workflow = Workflow(
            project_id=workflow_in.project_id,
            name=workflow_in.name,
            description=workflow_in.description,
            status=WorkflowStatus.RUNNING
        )
        db.add(workflow)
        db.flush()

        # 2. Map of created jobs by index
        created_jobs: List[Job] = []

        # Find default policy or use None
        default_policy = db.query(Queue).filter(Queue.project_id == project.id).first()

        for idx, job_data in enumerate(workflow_in.jobs):
            # Find queue
            queue = db.query(Queue).filter(
                Queue.project_id == project.id,
                Queue.name == job_data.queue_name
            ).first()
            if not queue:
                queue = Queue(
                    project_id=project.id,
                    name=job_data.queue_name,
                    description=f"Auto-created queue for workflow {job_data.queue_name}",
                    priority=1,
                    max_concurrency=10
                )
                db.add(queue)
                db.flush()

            # Create Job, start blocked by default (will resolve in step 3)
            job = Job(
                project_id=project.id,
                queue_id=queue.id,
                workflow_id=workflow.id,
                task_name=job_data.task_name,
                payload=job_data.payload,
                priority=job_data.priority,
                status=JobStatus.BLOCKED
            )
            db.add(job)
            db.flush()
            created_jobs.append(job)

        # 3. Create dependencies & track child jobs
        children_indices = set()
        for dep_data in workflow_in.dependencies:
            p_idx = dep_data.parent_job_index
            c_idx = dep_data.child_job_index
            
            if p_idx >= len(created_jobs) or c_idx >= len(created_jobs):
                raise HTTPException(status_code=400, detail="Invalid job dependency indices")

            parent_job = created_jobs[p_idx]
            child_job = created_jobs[c_idx]

            dep = WorkflowDependency(
                workflow_id=workflow.id,
                parent_job_id=parent_job.id,
                child_job_id=child_job.id
            )
            db.add(dep)
            children_indices.add(c_idx)

        # 4. Unblock root jobs (jobs that are not children of any dependency)
        for idx, job in enumerate(created_jobs):
            if idx not in children_indices:
                job.status = JobStatus.QUEUED
                db.add(job)

        db.commit()
        db.refresh(workflow)
        
        # Populate response relations
        workflow.jobs = db.query(Job).filter(Job.workflow_id == workflow.id).all()
        workflow.dependencies = db.query(WorkflowDependency).filter(WorkflowDependency.workflow_id == workflow.id).all()
        
        return workflow

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {e}")

@router.get("", response_model=List[WorkflowResponse])
def get_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workflows = db.query(Workflow).join(Project).filter(
        Project.organization_id == current_user.organization_id
    ).all()
    
    for wf in workflows:
        wf.jobs = db.query(Job).filter(Job.workflow_id == wf.id).all()
        wf.dependencies = db.query(WorkflowDependency).filter(WorkflowDependency.workflow_id == wf.id).all()
        
    return workflows

@router.get("/{id}", response_model=WorkflowResponse)
def get_workflow(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workflow = db.query(Workflow).join(Project).filter(
        Workflow.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    workflow.jobs = db.query(Job).filter(Job.workflow_id == workflow.id).all()
    workflow.dependencies = db.query(WorkflowDependency).filter(WorkflowDependency.workflow_id == workflow.id).all()
    
    return workflow
