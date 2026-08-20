import pytest
import time
import uuid
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.models import (
    User, Organization, Project, Queue, Job, JobStatus, 
    JobExecution, DeadLetterJob, Worker, WorkerStatus, 
    BackoffType, Workflow, WorkflowStatus, WorkflowDependency
)
from app.services.scheduler import (
    claim_jobs, calculate_backoff, handle_job_failure, WorkerRunner, 
    recover_failed_workers, process_recurring_jobs, TASK_REGISTRY
)
from app.services.workflow_service import resolve_downstream_dependencies

# ==================== AUTH & SETUP TESTS ====================

def test_user_registration_creates_sandbox(client: TestClient, db: Session):
    response = client.post("/auth/register", json={
        "email": "test@smartqueue.ai",
        "password": "securepassword",
        "full_name": "Test Engineer",
        "organization_name": "Test Lab"
    })
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token

    # Check database sandbox creation
    user = db.query(User).filter(User.email == "test@smartqueue.ai").first()
    assert user is not None
    assert user.full_name == "Test Engineer"

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    assert org is not None
    assert org.name == "Test Lab"

    project = db.query(Project).filter(Project.organization_id == org.id).first()
    assert project is not None
    assert project.name == "Main Project"

    queues = db.query(Queue).filter(Queue.project_id == project.id).all()
    assert len(queues) == 3
    queue_names = [q.name for q in queues]
    assert "default" in queue_names
    assert "high-priority" in queue_names

# ==================== QUEUE MANAGEMENT TESTS ====================

def test_queue_pause_resume_stats(client: TestClient, db: Session):
    # Setup test Org, User, Project
    org = Organization(name="Test Org")
    db.add(org)
    db.flush()
    project = Project(name="Demo Project", organization_id=org.id)
    db.add(project)
    db.flush()
    from app.core.security import get_password_hash
    user = User(email="t2@smartqueue.ai", hashed_password=get_password_hash("pw"), full_name="User", organization_id=org.id)
    db.add(user)
    db.commit()

    # Login
    response = client.post("/auth/login/json", json={"email": "t2@smartqueue.ai", "password": "pw"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Queue
    q_resp = client.post("/queues", json={
        "name": "testing-queue",
        "project_id": str(project.id),
        "description": "Test description",
        "priority": 5,
        "max_concurrency": 2
    }, headers=headers)
    assert q_resp.status_code == 201
    queue_id = q_resp.json()["id"]

    # 2. Pause Queue
    pause_resp = client.post(f"/queues/{queue_id}/pause", headers=headers)
    assert pause_resp.status_code == 200
    assert pause_resp.json()["is_paused"] is True

    # 3. Resume Queue
    resume_resp = client.post(f"/queues/{queue_id}/resume", headers=headers)
    assert resume_resp.status_code == 200
    assert resume_resp.json()["is_paused"] is False

    # 4. Get Queue Stats
    stats_resp = client.get(f"/queues/{queue_id}/stats", headers=headers)
    assert stats_resp.status_code == 200
    assert stats_resp.json()["queue_name"] == "testing-queue"
    assert stats_resp.json()["depth"] == 0

# ==================== JOB EXECUTION TESTS ====================

def test_immediate_job_execution(db: Session):
    # Setup Sandbox
    org = Organization(name="Sandbox")
    db.add(org)
    db.flush()
    project = Project(name="Proj", organization_id=org.id)
    db.add(project)
    db.flush()
    queue = Queue(name="immediate-q", project_id=project.id, max_concurrency=5)
    db.add(queue)
    db.commit()

    # Create Immediate Job
    job = Job(
        project_id=project.id,
        queue_id=queue.id,
        task_name="task_success",
        payload={"data": "test-execution"},
        status=JobStatus.QUEUED,
        priority=1,
        scheduled_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()

    # Simulate Worker Claim
    worker_id = uuid.uuid4()
    worker = Worker(id=worker_id, name="Test Worker", status=WorkerStatus.ACTIVE)
    db.add(worker)
    db.flush()
    claimed = claim_jobs(db, worker_id, limit=1)
    assert len(claimed) == 1
    assert claimed[0].status == JobStatus.CLAIMED
    assert claimed[0].worker_id == worker_id

    # Execute Job
    claimed_job = claimed[0]
    claimed_job.status = JobStatus.RUNNING
    execution = JobExecution(
        job_id=claimed_job.id,
        worker_id=worker_id,
        attempt_number=1,
        status="RUNNING",
        started_at=datetime.utcnow()
    )
    db.add(execution)
    db.commit()

    # Run actual task from registry
    task_fn = TASK_REGISTRY.get(claimed_job.task_name)
    result = task_fn(claimed_job.payload)
    assert result["status"] == "success"

    # Mark complete
    claimed_job.status = JobStatus.COMPLETED
    execution.status = "COMPLETED"
    execution.ended_at = datetime.utcnow()
    execution.duration = 1.0
    db.commit()

    assert db.query(Job).filter(Job.id == claimed_job.id).first().status == JobStatus.COMPLETED

# ==================== RETRY & EXPONENTIAL BACKOFF TESTS ====================

def test_backoff_calculations():
    # FIXED backoff
    assert calculate_backoff(BackoffType.FIXED, base_delay=5, retry_count=0) == 5
    assert calculate_backoff(BackoffType.FIXED, base_delay=5, retry_count=1) == 5

    # LINEAR backoff (base_delay * (retry_count + 1))
    assert calculate_backoff(BackoffType.LINEAR, base_delay=5, retry_count=0) == 5
    assert calculate_backoff(BackoffType.LINEAR, base_delay=5, retry_count=1) == 10
    assert calculate_backoff(BackoffType.LINEAR, base_delay=5, retry_count=2) == 15

    # EXPONENTIAL backoff (base_delay * (2 ** retry_count))
    assert calculate_backoff(BackoffType.EXPONENTIAL, base_delay=5, retry_count=0) == 5
    assert calculate_backoff(BackoffType.EXPONENTIAL, base_delay=5, retry_count=1) == 10
    assert calculate_backoff(BackoffType.EXPONENTIAL, base_delay=5, retry_count=2) == 20

def test_failed_job_moves_to_dlq(db: Session):
    # Setup Sandbox
    org = Organization(name="Sandbox")
    db.add(org)
    db.flush()
    project = Project(name="Proj", organization_id=org.id)
    db.add(project)
    db.flush()
    queue = Queue(name="failed-q", project_id=project.id, max_concurrency=2)
    db.add(queue)
    db.commit()

    # Create job that will fail
    job = Job(
        project_id=project.id,
        queue_id=queue.id,
        task_name="task_fail",
        payload={},
        status=JobStatus.QUEUED,
        max_retries=1, # Allow only 1 retry
        retry_count=0
    )
    db.add(job)
    db.commit()

    # Run attempt 1
    execution = JobExecution(job_id=job.id, attempt_number=1, status="RUNNING", started_at=datetime.utcnow())
    db.add(execution)
    db.commit()

    # Trigger failure handler (first attempt) -> Should retry
    handle_job_failure(db, job, execution, "Intentional failure", "traceback snippet")
    assert job.status == JobStatus.QUEUED
    assert job.retry_count == 1

    # Run attempt 2 (exceeding max_retries = 1)
    execution2 = JobExecution(job_id=job.id, attempt_number=2, status="RUNNING", started_at=datetime.utcnow())
    db.add(execution2)
    db.commit()

    # Trigger failure handler (second attempt) -> Should move to DLQ
    handle_job_failure(db, job, execution2, "Intentional failure 2", "traceback snippet 2")
    assert job.status == JobStatus.DLQ

    # Verify Dead Letter Record is populated
    dlq_record = db.query(DeadLetterJob).filter(DeadLetterJob.job_id == job.id).first()
    assert dlq_record is not None
    assert dlq_record.failure_reason is not None

# ==================== WORKFLOW DEPENDENCIES TESTS ====================

def test_workflow_dependency_execution(db: Session):
    # Setup
    org = Organization(name="Workflow Sandbox")
    db.add(org)
    db.flush()
    project = Project(name="Proj", organization_id=org.id)
    db.add(project)
    db.flush()
    queue = Queue(name="wf-q", project_id=project.id)
    db.add(queue)
    db.flush()

    workflow = Workflow(name="Seq Pipeline", project_id=project.id, status=WorkflowStatus.PENDING)
    db.add(workflow)
    db.flush()

    # Create Job A (Root) and Job B (Child)
    job_a = Job(project_id=project.id, queue_id=queue.id, workflow_id=workflow.id, task_name="task_success", status=JobStatus.QUEUED, payload={})
    job_b = Job(project_id=project.id, queue_id=queue.id, workflow_id=workflow.id, task_name="task_success", status=JobStatus.BLOCKED, payload={})
    db.add(job_a)
    db.add(job_b)
    db.flush()

    # Create dependency: A -> B
    dep = WorkflowDependency(workflow_id=workflow.id, parent_job_id=job_a.id, child_job_id=job_b.id)
    db.add(dep)
    db.commit()

    # Execute Job A
    job_a.status = JobStatus.COMPLETED
    db.add(job_a)
    db.commit()

    # Resolve dependencies
    resolve_downstream_dependencies(db, job_a)

    # Job B should now be unblocked (QUEUED)
    db.refresh(job_b)
    assert job_b.status == JobStatus.QUEUED

# ==================== WORKER HEARTBEAT & RECOVERY TESTS ====================

def test_worker_recovery_orphaned_jobs(db: Session):
    # Setup
    org = Organization(name="Recovery Sandbox")
    db.add(org)
    db.flush()
    project = Project(name="Proj", organization_id=org.id)
    db.add(project)
    db.flush()
    queue = Queue(name="rec-q", project_id=project.id)
    db.add(queue)
    db.flush()

    # Create worker with ancient last heartbeat
    worker = Worker(
        name="Dead Worker",
        status=WorkerStatus.BUSY,
        last_heartbeat=datetime.utcnow() - timedelta(seconds=45), # Dead
        registered_at=datetime.utcnow()
    )
    db.add(worker)
    db.flush()

    # Create job claimed by the dead worker
    job = Job(
        project_id=project.id,
        queue_id=queue.id,
        task_name="task_success",
        payload={},
        status=JobStatus.RUNNING,
        worker_id=worker.id
    )
    db.add(job)
    db.commit()

    # Recover workers
    recover_failed_workers(db)

    # Worker must be OFFLINE, Job must be re-queued (QUEUED) and unassigned
    db.refresh(worker)
    db.refresh(job)
    assert worker.status == WorkerStatus.OFFLINE
    assert job.status == JobStatus.QUEUED
    assert job.worker_id is None

# ==================== CONCURRENCY CLAIM LOCKING TEST ====================

def test_atomic_claiming_concurrency(db: Session):
    # Setup
    org = Organization(name="Concurrency Sandbox")
    db.add(org)
    db.flush()
    project = Project(name="Proj", organization_id=org.id)
    db.add(project)
    db.flush()
    queue = Queue(name="concur-q", project_id=project.id, max_concurrency=100)
    db.add(queue)
    db.flush()

    # Create 10 jobs
    job_ids = []
    for i in range(10):
        job = Job(
            project_id=project.id,
            queue_id=queue.id,
            task_name="task_success",
            payload={"id": i},
            status=JobStatus.QUEUED,
            priority=1,
            scheduled_at=datetime.utcnow()
        )
        db.add(job)
        db.flush()
        job_ids.append(job.id)
    db.commit()

    claimed_job_ids = []
    lock = threading.Lock()

    def worker_claim_thread(worker_num):
        # Create separate database session per thread to simulate distributed workers
        from app.core.database import SessionLocal
        local_db = SessionLocal()
        try:
            worker_uuid = uuid.uuid4()
            # Register worker first to avoid foreign key violation
            worker = Worker(id=worker_uuid, name=f"Thread-Worker-{worker_num}", status=WorkerStatus.ACTIVE)
            local_db.add(worker)
            local_db.flush()
            # Claim up to 3 jobs
            claimed = claim_jobs(local_db, worker_uuid, limit=3)
            with lock:
                for job in claimed:
                    claimed_job_ids.append(job.id)
        finally:
            local_db.close()

    # Start 5 concurrent threads attempting to claim the 10 jobs
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker_claim_thread, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify that no job was claimed twice. Unique claimed jobs must equal total claimed jobs.
    assert len(claimed_job_ids) == len(set(claimed_job_ids))
    assert len(claimed_job_ids) <= 10


# ==================== IDEMPOTENT REGISTRATION & PER-PROJECT QUEUES TESTS ====================

def test_workspace_registration_flow(client: TestClient, db: Session):
    # 1. First workspace registration
    email_a = f"engineer_a_{uuid.uuid4().hex[:6]}@smartqueue.ai"
    response_a = client.post("/auth/register", json={
        "email": email_a,
        "password": "securepassword123",
        "full_name": "Engineer Alpha",
        "organization_name": "Lab Alpha"
    })
    assert response_a.status_code == 200
    token_a = response_a.json()
    assert "access_token" in token_a

    # Verify database sandbox for user A
    user_a = db.query(User).filter(User.email == email_a).first()
    assert user_a is not None
    org_a = db.query(Organization).filter(Organization.id == user_a.organization_id).first()
    assert org_a is not None
    project_a = db.query(Project).filter(Project.organization_id == org_a.id).first()
    assert project_a is not None
    queues_a = db.query(Queue).filter(Queue.project_id == project_a.id).all()
    assert len(queues_a) == 3
    queue_names_a = [q.name for q in queues_a]
    assert "default" in queue_names_a
    assert "high-priority" in queue_names_a

    # 2. Second workspace registration
    email_b = f"engineer_b_{uuid.uuid4().hex[:6]}@smartqueue.ai"
    response_b = client.post("/auth/register", json={
        "email": email_b,
        "password": "securepassword456",
        "full_name": "Engineer Beta",
        "organization_name": "Lab Beta"
    })
    assert response_b.status_code == 200
    token_b = response_b.json()
    assert "access_token" in token_b

    # Verify database sandbox for user B
    user_b = db.query(User).filter(User.email == email_b).first()
    assert user_b is not None
    org_b = db.query(Organization).filter(Organization.id == user_b.organization_id).first()
    assert org_b is not None
    project_b = db.query(Project).filter(Project.organization_id == org_b.id).first()
    assert project_b is not None
    queues_b = db.query(Queue).filter(Queue.project_id == project_b.id).all()
    assert len(queues_b) == 3
    queue_names_b = [q.name for q in queues_b]
    assert "default" in queue_names_b
    assert "high-priority" in queue_names_b
    
    # Confirm multiple projects/workspaces queue isolation (they both have a "default" queue)
    assert project_a.id != project_b.id
    default_q_a = next(q for q in queues_a if q.name == "default")
    default_q_b = next(q for q in queues_b if q.name == "default")
    assert default_q_a.id != default_q_b.id

    # 3. Duplicate registration attempt (idempotence check)
    # Registering the same user with identical parameters should succeed and return the token
    response_dup = client.post("/auth/register", json={
        "email": email_a,
        "password": "securepassword123",
        "full_name": "Engineer Alpha",
        "organization_name": "Lab Alpha"
    })
    assert response_dup.status_code == 200
    token_dup = response_dup.json()
    assert "access_token" in token_dup

    # Verify no new users, orgs, or queues were created for user A
    users_a_count = db.query(User).filter(User.email == email_a).count()
    assert users_a_count == 1
    orgs_a_count = db.query(Organization).filter(Organization.name == "Lab Alpha").count()
    assert orgs_a_count == 1
    queues_a_count = db.query(Queue).filter(Queue.project_id == project_a.id).count()
    assert queues_a_count == 3

    # Registering same email with WRONG password should fail
    response_wrong = client.post("/auth/register", json={
        "email": email_a,
        "password": "wrongpassword",
        "full_name": "Engineer Alpha",
        "organization_name": "Lab Alpha"
    })
    assert response_wrong.status_code == 400

    # 4. Existing default queue (making queue creation idempotent)
    # Manually delete one default queue and re-run registration for user A
    # It should recreate the missing default queue without complaining about the other existing ones
    db.delete(default_q_a)
    db.commit()
    
    response_restore = client.post("/auth/register", json={
        "email": email_a,
        "password": "securepassword123",
        "full_name": "Engineer Alpha",
        "organization_name": "Lab Alpha"
    })
    assert response_restore.status_code == 200
    
    # Verify the "default" queue is restored and there are 3 queues again
    queues_restored = db.query(Queue).filter(Queue.project_id == project_a.id).all()
    assert len(queues_restored) == 3
    assert "default" in [q.name for q in queues_restored]


def test_queue_uniqueness_within_project(client: TestClient, db: Session):
    # Setup two projects
    org = Organization(name="Unique Org")
    db.add(org)
    db.flush()
    p1 = Project(name="Project One", organization_id=org.id)
    p2 = Project(name="Project Two", organization_id=org.id)
    db.add(p1)
    db.add(p2)
    db.flush()
    
    p1_id = p1.id
    p2_id = p2.id

    # Create default queue in project 1
    q1 = Queue(project_id=p1_id, name="default")
    db.add(q1)
    db.flush()

    # Attempt to create duplicate queue in project 1 (should fail constraint check) using a nested transaction (SAVEPOINT)
    nested = db.begin_nested()
    try:
        q2 = Queue(project_id=p1_id, name="default")
        db.add(q2)
        nested.commit()
        db.flush()
        assert False, "Should have raised unique constraint violation for duplicate name in p1"
    except Exception:
        nested.rollback()

    # Create default queue in project 2 (should succeed - scoped uniqueness)
    q3 = Queue(project_id=p2_id, name="default")
    db.add(q3)
    db.flush()
    
    db.commit()
    
    assert db.query(Queue).filter(Queue.project_id == p1_id, Queue.name == "default").count() == 1
    assert db.query(Queue).filter(Queue.project_id == p2_id, Queue.name == "default").count() == 1


def test_registration_transaction_rollback(client: TestClient, db: Session):
    email_fail = f"engineer_fail_{uuid.uuid4().hex[:6]}@smartqueue.ai"
    # Organization name too long to cause DB constraint error on insert
    org_name_too_long = "a" * 300
    response = client.post("/auth/register", json={
        "email": email_fail,
        "password": "securepassword",
        "full_name": "Fail Test",
        "organization_name": org_name_too_long
    })
    assert response.status_code == 500
    
    # Verify that the user was NOT created (rolled back completely)
    user = db.query(User).filter(User.email == email_fail).first()
    assert user is None

