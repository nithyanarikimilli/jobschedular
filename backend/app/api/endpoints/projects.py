from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Project
from app.schemas.schemas import ProjectCreate, ProjectResponse

router = APIRouter()

@router.get("", response_model=List[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = db.query(Project).filter(Project.organization_id == current_user.organization_id).all()
    return projects

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = Project(
        name=project_in.name,
        organization_id=current_user.organization_id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{id}", response_model=ProjectResponse)
def get_project(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == current_user.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
