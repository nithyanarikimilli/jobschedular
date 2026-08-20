from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Job, JobExecution, AIAnalysis, Project
from app.schemas.schemas import AIAnalysisResponse

router = APIRouter()

@router.get("/{id}/failure-analysis", response_model=AIAnalysisResponse)
def get_job_failure_analysis(
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

    # Find latest execution
    latest_exec = db.query(JobExecution).filter(
        JobExecution.job_id == id
    ).order_by(JobExecution.attempt_number.desc()).first()
    
    if not latest_exec:
        raise HTTPException(status_code=404, detail="No executions found for this job")

    # Find AI analysis
    analysis = db.query(AIAnalysis).filter(
        AIAnalysis.execution_id == latest_exec.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="No AI analysis found for the latest execution")

    return analysis
