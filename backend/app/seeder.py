import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.models import (
    User, Organization, Project, Queue, Job, JobStatus, JobExecution, 
    JobLog, RetryPolicy, DeadLetterJob, Worker, WorkerStatus, 
    ScheduledJob, Workflow, WorkflowStatus, WorkflowDependency, 
    BackoffType, AIAnalysis
)
from app.services.ai_analyzer import analyze_job_failure

def seed_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if organization already exists to prevent duplication
        existing_org = db.query(Organization).filter(Organization.name == "SmartQueue Global").first()
        if existing_org:
            print("Database already seeded. Skipping seeder script to preserve data.")
            return

        print("Seeding database...")
        # 1. Create Organization
        org = Organization(name="SmartQueue Global")
        db.add(org)
        db.flush()

        # 2. Create User
        user = User(
            email="dev@smartqueue.ai",
            hashed_password=get_password_hash("admin123"),
            full_name="Alex Mercer (SRE)",
            organization_id=org.id
        )
        db.add(user)
        db.flush()

        # 3. Create 2 Projects
        proj_ops = Project(name="Ops Control Center", organization_id=org.id)
        proj_ml = Project(name="Machine Learning Labs", organization_id=org.id)
        db.add(proj_ops)
        db.add(proj_ml)
        db.flush()

        # 4. Create Queues
        q_default = Queue(project_id=proj_ops.id, name="default", description="Main transaction task flow", priority=1, max_concurrency=10)
        q_high = Queue(project_id=proj_ops.id, name="high-priority", description="Critical operations queues", priority=3, max_concurrency=15)
        q_low = Queue(project_id=proj_ops.id, name="low-priority", description="Bulk notifications and non-blocking tasks", priority=0, max_concurrency=5)
        q_ml = Queue(project_id=proj_ml.id, name="ml-pipeline", description="Heavy compute neural training queues", priority=2, max_concurrency=2)
        q_workflow = Queue(project_id=proj_ops.id, name="workflow-queue", description="Sequenced pipeline tasks", priority=1, max_concurrency=5)
        db.add(q_default)
        db.add(q_high)
        db.add(q_low)
        db.add(q_ml)
        db.add(q_workflow)
        db.flush()

        # 5. Create default retry policies
        policy_exp = RetryPolicy(name="Exp Backoff Policy", backoff_type=BackoffType.EXPONENTIAL, base_delay=5, max_retries=3)
        policy_fixed = RetryPolicy(name="Fixed Policy", backoff_type=BackoffType.FIXED, base_delay=5, max_retries=2)
        db.add(policy_exp)
        db.add(policy_fixed)
        db.flush()

        # 6. Create 3 Workers
        w1 = Worker(name="Worker-Alpha", status=WorkerStatus.IDLE, last_heartbeat=datetime.utcnow(), jobs_completed=142, jobs_failed=3, system_info={"cpu": 15, "memory": 35})
        w2 = Worker(name="Worker-Beta", status=WorkerStatus.IDLE, last_heartbeat=datetime.utcnow(), jobs_completed=98, jobs_failed=8, system_info={"cpu": 8, "memory": 40})
        w3 = Worker(name="Worker-Gamma", status=WorkerStatus.OFFLINE, last_heartbeat=datetime.utcnow() - timedelta(minutes=15), jobs_completed=20, jobs_failed=1, system_info={"cpu": 0, "memory": 0})
        db.add(w1)
        db.add(w2)
        db.add(w3)
        db.flush()

        # 7. Seed Successful Jobs history
        for i in range(1, 6):
            job = Job(
                project_id=proj_ops.id,
                queue_id=q_default.id,
                task_name="task_success",
                payload={"order_id": 1000 + i, "item": "book", "user_id": f"usr_{i}"},
                status=JobStatus.COMPLETED,
                priority=1,
                created_at=datetime.utcnow() - timedelta(hours=i),
                scheduled_at=datetime.utcnow() - timedelta(hours=i)
            )
            db.add(job)
            db.flush()

            # Create successful execution log
            exec_record = JobExecution(
                job_id=job.id,
                worker_id=w1.id,
                attempt_number=1,
                status="COMPLETED",
                started_at=job.created_at,
                ended_at=job.created_at + timedelta(seconds=1.2),
                duration=1.2
            )
            db.add(exec_record)
            db.flush()

            log1 = JobLog(job_id=job.id, execution_id=exec_record.id, log_level="INFO", message=f"Task claimed by {w1.name}", created_at=job.created_at)
            log2 = JobLog(job_id=job.id, execution_id=exec_record.id, log_level="INFO", message="Processing order details...", created_at=job.created_at + timedelta(seconds=0.5))
            log3 = JobLog(job_id=job.id, execution_id=exec_record.id, log_level="INFO", message="Order transaction finalized.", created_at=job.created_at + timedelta(seconds=1.2))
            db.add(log1)
            db.add(log2)
            db.add(log3)

        # 8. Seed Intentional Failing Jobs to display AI diagnostic panel
        # Failure 1: Network Timeout (will be analyzed as temporary -> backoff)
        job_fail1 = Job(
            project_id=proj_ops.id,
            queue_id=q_default.id,
            retry_policy_id=policy_exp.id,
            task_name="task_network_error",
            payload={"connection_target": "thirdparty-api.com"},
            status=JobStatus.QUEUED,
            priority=2,
            retry_count=1,
            max_retries=3,
            scheduled_at=datetime.utcnow() + timedelta(seconds=10),
            failure_reason="ConnectionTimeout: Failed to connect to api.github.com on port 443"
        )
        db.add(job_fail1)
        db.flush()

        exec_fail1 = JobExecution(
            job_id=job_fail1.id,
            worker_id=w2.id,
            attempt_number=1,
            status="FAILED",
            started_at=datetime.utcnow() - timedelta(minutes=5),
            ended_at=datetime.utcnow() - timedelta(minutes=5) + timedelta(seconds=2.1),
            duration=2.1,
            error_message="ConnectionTimeout: Failed to connect to thirdparty-api.com port 443. Connection Refused.",
            stack_trace="Traceback (most recent call last):\n  File \"/workspace/app/services/scheduler.py\", line 150, in run\n    result = task_fn(job.payload)\n  File \"/workspace/app/services/scheduler.py\", line 35, in task_network_error\n    raise Exception(\"ConnectionTimeout\")\nException: ConnectionTimeout"
        )
        db.add(exec_fail1)
        db.flush()

        log_f1 = JobLog(job_id=job_fail1.id, execution_id=exec_fail1.id, log_level="INFO", message="Attempting connecting to gateway...", created_at=exec_fail1.started_at)
        log_f2 = JobLog(job_id=job_fail1.id, execution_id=exec_fail1.id, log_level="ERROR", message="Connection Refused by server gateway. Timeout 2000ms.", created_at=exec_fail1.ended_at)
        db.add(log_f1)
        db.add(log_f2)
        db.flush()

        # Run AI analysis for fail 1
        analysis1 = analyze_job_failure(
            error_message=exec_fail1.error_message,
            stack_trace=exec_fail1.stack_trace,
            logs=f"[INFO] Claimed task\n[ERROR] Connection timeout",
            retry_count=0,
            duration=exec_fail1.duration
        )
        ai_an1 = AIAnalysis(
            execution_id=exec_fail1.id,
            failure_reason=analysis1["failure_reason"],
            severity=analysis1["severity"],
            suggested_solution=analysis1["suggested_solution"],
            is_temporary=analysis1["is_temporary"]
        )
        db.add(ai_an1)

        # Failure 2: Code Bug / Validation (analyzed as permanent -> straight to DLQ)
        job_fail2 = Job(
            project_id=proj_ops.id,
            queue_id=q_default.id,
            retry_policy_id=policy_fixed.id,
            task_name="task_validation_error",
            payload={"email": "bad_email_format"},
            status=JobStatus.DLQ, # Sent to DLQ
            priority=1,
            retry_count=1,
            max_retries=2,
            failure_reason="ValueError: The input data must contain non-null email field."
        )
        db.add(job_fail2)
        db.flush()

        exec_fail2 = JobExecution(
            job_id=job_fail2.id,
            worker_id=w2.id,
            attempt_number=1,
            status="FAILED",
            started_at=datetime.utcnow() - timedelta(minutes=10),
            ended_at=datetime.utcnow() - timedelta(minutes=10) + timedelta(seconds=0.4),
            duration=0.4,
            error_message="ValueError: invalid email address 'bad_email_format' provided in args.",
            stack_trace="Traceback (most recent call last):\n  File \"/workspace/app/services/scheduler.py\", line 150, in run\n    result = task_fn(job.payload)\n  File \"/workspace/app/services/scheduler.py\", line 40, in task_validation_error\n    raise ValueError(\"invalid email address\")\nValueError: invalid email address"
        )
        db.add(exec_fail2)
        db.flush()

        dlq_rec = DeadLetterJob(
            job_id=job_fail2.id,
            project_id=proj_ops.id,
            queue_id=q_default.id,
            execution_id=exec_fail2.id,
            task_name=job_fail2.task_name,
            payload=job_fail2.payload,
            failed_at=datetime.utcnow() - timedelta(minutes=10),
            failure_reason="Permanent input validation bug",
            error_message=exec_fail2.error_message,
            stack_trace=exec_fail2.stack_trace
        )
        db.add(dlq_rec)

        log_v1 = JobLog(job_id=job_fail2.id, execution_id=exec_fail2.id, log_level="INFO", message="Validating schema properties...", created_at=exec_fail2.started_at)
        log_v2 = JobLog(job_id=job_fail2.id, execution_id=exec_fail2.id, log_level="ERROR", message="Validation failed: email field lacks domain.", created_at=exec_fail2.ended_at)
        db.add(log_v1)
        db.add(log_v2)
        db.flush()

        analysis2 = analyze_job_failure(
            error_message=exec_fail2.error_message,
            stack_trace=exec_fail2.stack_trace,
            logs="[INFO] Start validation\n[ERROR] ValueError email invalid",
            retry_count=0,
            duration=exec_fail2.duration
        )
        ai_an2 = AIAnalysis(
            execution_id=exec_fail2.id,
            failure_reason=analysis2["failure_reason"],
            severity=analysis2["severity"],
            suggested_solution=analysis2["suggested_solution"],
            is_temporary=analysis2["is_temporary"]
        )
        db.add(ai_an2)

        # 9. Seed a Delayed Job
        job_delay = Job(
            project_id=proj_ops.id,
            queue_id=q_default.id,
            task_name="task_success",
            payload={"delayed_execution": True},
            status=JobStatus.QUEUED,
            priority=1,
            scheduled_at=datetime.utcnow() + timedelta(minutes=30)
        )
        db.add(job_delay)

        # 10. Seed a Recurring cron job
        cron_job = ScheduledJob(
            project_id=proj_ops.id,
            queue_id=q_low.id,
            retry_policy_id=policy_fixed.id,
            task_name="task_success",
            cron_expression="*/5 * * * *", # Every 5 minutes
            payload={"scheduled_cron": True},
            priority=0,
            is_active=True,
            next_run_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db.add(cron_job)
        db.flush()

        # 11. Seed a sequential workflow pipeline A -> B -> C -> D
        wf = Workflow(
            project_id=proj_ops.id,
            name="ML Model Deploy Pipeline",
            description="Sequenced stages to fetch dataset, clean, retrain AI model, and distribute operational reports.",
            status=WorkflowStatus.RUNNING
        )
        db.add(wf)
        db.flush()

        # Create the 4 jobs:
        # A: Fetch Data (COMPLETED)
        # B: Clean Dataset (RUNNING)
        # C: Train Model (BLOCKED)
        # D: Distribute Alert (BLOCKED)
        w_job_a = Job(project_id=proj_ops.id, queue_id=q_workflow.id, workflow_id=wf.id, task_name="task_workflow_step", payload={"step": "1. Extract Dataset logs"}, status=JobStatus.COMPLETED, priority=1)
        w_job_b = Job(project_id=proj_ops.id, queue_id=q_workflow.id, workflow_id=wf.id, task_name="task_workflow_step", payload={"step": "2. Clean Null Datasets"}, status=JobStatus.RUNNING, priority=1)
        w_job_c = Job(project_id=proj_ops.id, queue_id=q_workflow.id, workflow_id=wf.id, task_name="task_workflow_step", payload={"step": "3. Retrain Gemini-Small Classifier"}, status=JobStatus.BLOCKED, priority=1)
        w_job_d = Job(project_id=proj_ops.id, queue_id=q_workflow.id, workflow_id=wf.id, task_name="task_workflow_step", payload={"step": "4. Broadcast Slack reports"}, status=JobStatus.BLOCKED, priority=1)
        
        db.add(w_job_a)
        db.add(w_job_b)
        db.add(w_job_c)
        db.add(w_job_d)
        db.flush()

        # Create executions for A & B
        exec_a = JobExecution(job_id=w_job_a.id, worker_id=w1.id, attempt_number=1, status="COMPLETED", started_at=datetime.utcnow() - timedelta(minutes=2), ended_at=datetime.utcnow() - timedelta(minutes=2) + timedelta(seconds=1.4), duration=1.4)
        exec_b = JobExecution(job_id=w_job_b.id, worker_id=w2.id, attempt_number=1, status="RUNNING", started_at=datetime.utcnow() - timedelta(seconds=30))
        db.add(exec_a)
        db.add(exec_b)
        db.flush()

        # Create dependencies A -> B, B -> C, C -> D
        dep1 = WorkflowDependency(workflow_id=wf.id, parent_job_id=w_job_a.id, child_job_id=w_job_b.id)
        dep2 = WorkflowDependency(workflow_id=wf.id, parent_job_id=w_job_b.id, child_job_id=w_job_c.id)
        dep3 = WorkflowDependency(workflow_id=wf.id, parent_job_id=w_job_c.id, child_job_id=w_job_d.id)
        db.add(dep1)
        db.add(dep2)
        db.add(dep3)

        db.commit()
        print("Database seeded with demo scenario successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
