from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Worker
from app.schemas.schemas import WorkerResponse

router = APIRouter()

@router.get("", response_model=List[WorkerResponse])
def get_workers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Workers are global in system but user must be authenticated
    workers = db.query(Worker).order_by(Worker.last_heartbeat.desc()).all()
    return workers

@router.get("/{id}", response_model=WorkerResponse)
def get_worker(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    worker = db.query(Worker).filter(Worker.id == id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker
