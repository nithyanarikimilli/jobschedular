from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.models import BackoffType, JobStatus, WorkflowStatus, WorkerStatus

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str  # Creating user automatically creates an organization

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Project Schemas
class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Retry Policy Schemas
class RetryPolicyCreate(BaseModel):
    name: str
    backoff_type: BackoffType
    base_delay: int = 5
    max_retries: int = 3

class RetryPolicyResponse(BaseModel):
    id: UUID
    name: str
    backoff_type: BackoffType
    base_delay: int
    max_retries: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Queue Schemas
class QueueCreate(BaseModel):
    name: str
    project_id: UUID
    description: Optional[str] = None
    priority: int = 1
    max_concurrency: int = 10

class QueueUpdate(BaseModel):
    description: Optional[str] = None
    priority: Optional[int] = None
    max_concurrency: Optional[int] = None
    is_paused: Optional[bool] = None

class QueueResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    priority: int
    max_concurrency: int
    is_paused: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QueueStats(BaseModel):
    queue_name: str
    depth: int
    running_jobs: int
    waiting_jobs: int
    worker_capacity: int
    avg_execution_time: float
    failure_rate: float
    health_score: int
    is_overloaded: bool

# Worker Schemas
class WorkerResponse(BaseModel):
    id: UUID
    name: str
    status: WorkerStatus
    last_heartbeat: datetime
    jobs_completed: int
    jobs_failed: int
    system_info: Optional[Dict[str, Any]]
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)

# AI Analysis Schema
class AIAnalysisResponse(BaseModel):
    id: UUID
    execution_id: UUID
    failure_reason: str
    severity: str
    suggested_solution: str
    is_temporary: bool
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Job Schemas
class JobCreate(BaseModel):
    project_id: UUID
    queue_name: str
    task_name: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    scheduled_at: Optional[datetime] = None  # None means immediate
    retry_policy: Optional[RetryPolicyCreate] = None
    workflow_id: Optional[UUID] = None

class JobExecutionResponse(BaseModel):
    id: UUID
    job_id: UUID
    worker_id: Optional[UUID]
    attempt_number: int
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration: Optional[float]
    error_message: Optional[str]
    stack_trace: Optional[str]
    ai_analysis: Optional[AIAnalysisResponse] = None

    model_config = ConfigDict(from_attributes=True)

class JobLogResponse(BaseModel):
    id: UUID
    job_id: UUID
    log_level: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobResponse(BaseModel):
    id: UUID
    project_id: UUID
    queue_id: UUID
    workflow_id: Optional[UUID]
    retry_policy_id: Optional[UUID]
    task_name: str
    payload: Dict[str, Any]
    status: JobStatus
    priority: int
    retry_count: int
    max_retries: int
    scheduled_at: datetime
    next_retry_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    worker_id: Optional[UUID]
    failure_reason: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# Workflow Schemas
class WorkflowDependencyCreate(BaseModel):
    parent_job_index: int
    child_job_index: int

class WorkflowJobCreate(BaseModel):
    queue_name: str
    task_name: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1

class WorkflowCreate(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str] = None
    jobs: List[WorkflowJobCreate]
    dependencies: List[WorkflowDependencyCreate]

class WorkflowDependencyResponse(BaseModel):
    parent_job_id: UUID
    child_job_id: UUID

    model_config = ConfigDict(from_attributes=True)

class WorkflowResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    status: WorkflowStatus
    created_at: datetime
    jobs: List[JobResponse] = []
    dependencies: List[WorkflowDependencyResponse] = []

    model_config = ConfigDict(from_attributes=True)

# Dead Letter Queue Schema
class DeadLetterJobResponse(BaseModel):
    id: UUID
    job_id: UUID
    project_id: UUID
    queue_id: UUID
    execution_id: UUID
    task_name: str
    payload: Dict[str, Any]
    failed_at: datetime
    failure_reason: Optional[str]
    error_message: Optional[str]
    stack_trace: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# Dashboard Summary
class DashboardSummary(BaseModel):
    total_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    queue_depth: int
    active_workers: int
    success_rate: float
    system_health: str
