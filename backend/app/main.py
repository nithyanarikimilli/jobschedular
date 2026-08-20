from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.api.deps import get_current_user
from app.models.models import User, Job, JobStatus, Worker, WorkerStatus, Queue
from app.schemas.schemas import DashboardSummary
from app.api.endpoints import (
    auth, projects, queues, jobs, workers, dlq, workflows, ai
)
import logging
from contextlib import asynccontextmanager
from sqlalchemy import text
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("smartqueue.main")

def run_migrations(engine):
    logger.info("Running database migrations...")
    with engine.begin() as conn:
        db_type = conn.dialect.name
        logger.info(f"Database dialect: {db_type}")
        
        if db_type == "postgresql":
            # Check if index 'ix_queues_name' exists and is unique
            res = conn.execute(text("""
                SELECT indisunique 
                FROM pg_index i 
                JOIN pg_class c ON c.oid = i.indexrelid 
                WHERE c.relname = 'ix_queues_name';
            """)).first()
            
            is_unique = res[0] if res else False
            
            if is_unique:
                logger.info("Detected unique index ix_queues_name. Migrating to project-scoped unique index...")
                conn.execute(text("DROP INDEX IF EXISTS ix_queues_name;"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_queues_name ON queues (name);"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_queues_project_id_name ON queues (project_id, name);"))
                logger.info("Database migration completed successfully.")
            else:
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_queues_project_id_name ON queues (project_id, name);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_queues_name ON queues (name);"))
        else:
            try:
                conn.execute(text("DROP INDEX IF EXISTS ix_queues_name;"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_queues_name ON queues (name);"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_queues_project_id_name ON queues (project_id, name);"))
            except Exception as e:
                logger.warning(f"Non-postgresql migration warning: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify database connection and create tables
    logger.info("Verifying database connectivity...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # Database is available, create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created.")
        # Run migrations
        run_migrations(engine)
        logger.info("Database initialized and tables verified.")
    except Exception as e:
        logger.critical("==================================================")
        logger.critical("FATAL: Database connection failed.")
        logger.critical("Please check that PostgreSQL is running and credentials in .env are correct.")
        logger.critical(f"DATABASE_URL: {settings.DATABASE_URL}")
        logger.critical(f"Error details: {e}")
        logger.critical("==================================================")
        sys.exit(1)
    yield

app = FastAPI(
    title="SmartQueue REST API",
    description="Distributed job scheduler with atomic claiming, AI failure analysis, and dependency workflows.",
    version="1.0.0",
    lifespan=lifespan
)

# Set CORS permissions
cors_origins_str = settings.CORS_ORIGINS
if cors_origins_str:
    allow_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
else:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route mounting
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(queues.router, prefix="/queues", tags=["Queues"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(workers.router, prefix="/workers", tags=["Workers"])
app.include_router(dlq.router, prefix="/dlq", tags=["Dead Letter Queue"])
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
app.include_router(ai.router, prefix="/jobs", tags=["AI Failure Diagnostics"])

@app.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total jobs
    total_jobs = db.query(Job).join(User, User.organization_id == current_user.organization_id).count()

    # Running jobs (CLAIMED, RUNNING)
    running_jobs = db.query(Job).filter(
        Job.status.in_([JobStatus.CLAIMED, JobStatus.RUNNING])
    ).count()

    # Completed jobs
    completed_jobs = db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()

    # Failed jobs (FAILED, DLQ)
    failed_jobs = db.query(Job).filter(
        Job.status.in_([JobStatus.FAILED, JobStatus.DLQ])
    ).count()

    # Queue depth (QUEUED)
    queue_depth = db.query(Job).filter(
        Job.status == JobStatus.QUEUED
    ).count()

    # Active workers
    active_workers = db.query(Worker).filter(
        Worker.status != WorkerStatus.OFFLINE
    ).count()

    # Success rate
    total_finished = completed_jobs + failed_jobs
    success_rate = (completed_jobs / total_finished * 100.0) if total_finished > 0 else 100.0

    # System health (average health of queues)
    queues = db.query(Queue).all()
    if not queues:
        system_health = "HEALTHY"
    else:
        # Compute individual queue health and average
        tot_health = 0
        for q in queues:
            # DLQ count
            dlq_c = db.query(Job).filter(Job.queue_id == q.id, Job.status == JobStatus.DLQ).count()
            # failure rate
            day_ago = datetime.utcnow() - timedelta(days=1)
            execs_count = db.query(Job).filter(Job.queue_id == q.id, Job.updated_at >= day_ago).count()
            failed_c = db.query(Job).filter(Job.queue_id == q.id, Job.status == JobStatus.FAILED, Job.updated_at >= day_ago).count()
            fail_rate = (failed_c / execs_count) if execs_count > 0 else 0.0
            
            q_health = 100 - min(dlq_c * 10, 40) - min(int(fail_rate * 50), 40)
            tot_health += max(0, q_health)
        
        avg_health = tot_health / len(queues)
        if avg_health >= 80:
            system_health = "HEALTHY"
        elif avg_health >= 40:
            system_health = "WARNING"
        else:
            system_health = "CRITICAL"

    return {
        "total_jobs": total_jobs,
        "running_jobs": running_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "queue_depth": queue_depth,
        "active_workers": active_workers,
        "success_rate": round(success_rate, 2),
        "system_health": system_health
    }

import redis
from sqlalchemy import text

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/health/system")
def system_health(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        
    redis_ok = False
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        if r.ping():
            redis_ok = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    active_workers_count = db.query(Worker).filter(Worker.status != WorkerStatus.OFFLINE).count()
    scheduler_status = "active" if db_ok and redis_ok else "degraded"

    return {
        "database": "online" if db_ok else "offline",
        "redis": "online" if redis_ok else "offline",
        "worker_count": active_workers_count,
        "scheduler": scheduler_status
    }

