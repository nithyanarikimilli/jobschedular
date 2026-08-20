import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum, JSON, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class BackoffType(str, enum.Enum):
    FIXED = "FIXED"
    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"

class JobStatus(str, enum.Enum):
    BLOCKED = "BLOCKED"
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DLQ = "DLQ"

class WorkflowStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class WorkerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="projects")
    queues = relationship("Queue", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    scheduled_jobs = relationship("ScheduledJob", back_populates="project", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="project", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="users")

class Queue(Base):
    __tablename__ = "queues"
    __table_args__ = (
        UniqueConstraint('project_id', 'name', name='uq_queues_project_id_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=1, nullable=False)  # Higher is higher priority
    max_concurrency = Column(Integer, default=10, nullable=False)
    is_paused = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="queues")
    jobs = relationship("Job", back_populates="queue")
    scheduled_jobs = relationship("ScheduledJob", back_populates="queue")

class RetryPolicy(Base):
    __tablename__ = "retry_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    backoff_type = Column(Enum(BackoffType), default=BackoffType.FIXED, nullable=False)
    base_delay = Column(Integer, default=5, nullable=False)  # in seconds
    max_retries = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    jobs = relationship("Job", back_populates="retry_policy")

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="workflows")
    jobs = relationship("Job", back_populates="workflow", cascade="all, delete-orphan")
    dependencies = relationship("WorkflowDependency", back_populates="workflow", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True)
    retry_policy_id = Column(UUID(as_uuid=True), ForeignKey("retry_policies.id", ondelete="SET NULL"), nullable=True)
    
    task_name = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, index=True, nullable=False)
    priority = Column(Integer, default=1, index=True, nullable=False)  # Higher is higher priority
    
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    scheduled_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    next_retry_at = Column(DateTime, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    failure_reason = Column(Text, nullable=True)

    project = relationship("Project", back_populates="jobs")
    queue = relationship("Queue", back_populates="jobs")
    workflow = relationship("Workflow", back_populates="jobs")
    retry_policy = relationship("RetryPolicy", back_populates="jobs")
    worker = relationship("Worker", foreign_keys=[worker_id], back_populates="claimed_jobs")
    
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    dlq_record = relationship("DeadLetterJob", uselist=False, back_populates="job", cascade="all, delete-orphan")

class WorkflowDependency(Base):
    __tablename__ = "workflow_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    parent_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    child_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    workflow = relationship("Workflow", back_populates="dependencies")
    parent_job = relationship("Job", foreign_keys=[parent_job_id])
    child_job = relationship("Job", foreign_keys=[child_job_id])

class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)  # RUNNING, COMPLETED, FAILED
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    job = relationship("Job", back_populates="executions")
    worker = relationship("Worker")
    ai_analysis = relationship("AIAnalysis", uselist=False, back_populates="execution", cascade="all, delete-orphan")

class JobLog(Base):
    __tablename__ = "job_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("job_executions.id", ondelete="CASCADE"), nullable=True)
    log_level = Column(String(50), default="INFO", nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("Job", back_populates="logs")

class Worker(Base):
    __tablename__ = "workers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    status = Column(Enum(WorkerStatus), default=WorkerStatus.ACTIVE, nullable=False)
    last_heartbeat = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    jobs_completed = Column(Integer, default=0, nullable=False)
    jobs_failed = Column(Integer, default=0, nullable=False)
    system_info = Column(JSON, nullable=True)  # cpu, memory, etc.
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    claimed_jobs = relationship("Job", foreign_keys=[Job.worker_id], back_populates="worker")
    heartbeats = relationship("WorkerHeartbeat", back_populates="worker", cascade="all, delete-orphan")

class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), nullable=False)
    system_info = Column(JSON, nullable=True)

    worker = relationship("Worker", back_populates="heartbeats")

class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    retry_policy_id = Column(UUID(as_uuid=True), ForeignKey("retry_policies.id", ondelete="SET NULL"), nullable=True)
    
    task_name = Column(String(255), nullable=False)
    cron_expression = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="scheduled_jobs")
    queue = relationship("Queue", back_populates="scheduled_jobs")

class DeadLetterJob(Base):
    __tablename__ = "dead_letter_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("job_executions.id", ondelete="CASCADE"), nullable=False)
    
    task_name = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    failed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    failure_reason = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    job = relationship("Job", back_populates="dlq_record")

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("job_executions.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    failure_reason = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    suggested_solution = Column(Text, nullable=False)
    is_temporary = Column(Boolean, nullable=False)
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    execution = relationship("JobExecution", back_populates="ai_analysis")
