# SmartQueue — Intelligent Distributed Job Scheduler

SmartQueue is an intelligent distributed background job scheduling platform designed for high reliability, atomic task claiming, and real-time execution visibility. It integrates AI-powered error analysis using Gemini (with robust rule-based fallbacks) and provides automated retry handling, queue concurrency limits, dead letter queue management, and workflow pipeline execution.

---

## System Architecture

```
                       +---------------------------------------+
                       |          React (Vite) Dashboard       |
                       |       (Real-time HTTP Polling / UI)   |
                       +------------------+--------------------+
                                          |
                                          | REST API Requests
                                          v
                       +---------------------------------------+
                       |            FastAPI REST API           |
                       |      (Auth, CRUD, Dash Statistics)    |
                       +---------+-------------------+---------+
                                 |                   |
                    SQLAlchemy   |                   | Pub/Sub / Locks
                    Transactions v                   v
                       +-------------------+   +---------------+
                       |    PostgreSQL     |   |     Redis     |
                       | (Atomic database) |   | (Coordination)|
                       +---------+---------+   +---------------+
                                 ^
                                 | FOR UPDATE SKIP LOCKED
                                 | (Atomic Claiming)
              +------------------+------------------+
              |                  |                  |
       +------+------+    +------+------+    +------+------+
       |   Worker 1  |    |   Worker 2  |    |   Worker 3  |
       |  Executor   |    |  Executor   |    |  Executor   |
       +------+------+    +------+------+    +------+------+
              |                  |                  |
              +------------------+------------------+
                                 |
                                 v AI Failure Analyzer
                       +-------------------+
                       | Gemini AI Engine  | <---+ (Rule-Based Fallback)
                       | (Diagnostic SRE)  |
                       +-------------------+
```

---

## Entity Relationship (ER) Diagram

```
[organizations] 1 ----- * [users]
       1
       |
       *
  [projects] 1 ----- * [queues] 1 ----- * [jobs]
       1                                    |
       |                                    + 1 ----- * [job_executions] 1 ----- 1 [ai_analyses]
       |                                    |
       +------------------------------------+ 1 ----- * [job_logs]
       |                                    |
       *                                    + 1 ----- 0..1 [dead_letter_jobs]
  [workflows] 1 ---- * [workflow_dependencies]
```

- **`organizations`**: Workspace tenant container.
- **`users`**: Platform administrators.
- **`projects`**: Context boundary grouping queues and workflows.
- **`queues`**: Flow controller with strict custom priorities and `max_concurrency` limit parameters.
- **`jobs`**: The atomic task containing task name, payload args, status enums, retry stats, and timers.
- **`job_executions`**: Audits every single execution attempt, collecting duration, worker ID, error string, and stack trace.
- **`ai_analyses`**: Rich SRE diagnostics generated per crash, caching root-causes, severities, remediations, and transient flags.
- **`dead_letter_jobs`**: Hard failed jobs that exhausted retries or failed on permanent parameters.
- **`workflows`**: Tracks visual multi-step pipeline status.
- **`workflow_dependencies`**: Graph table linking parent/child job index keys.
- **`workers`**: Live grid containing registered heartbeats and resource allocations.

---

## Core Technologies

- **Frontend**: React v18, Vite, Tailwind CSS v3, Recharts, Lucide Icons
- **Backend API**: Python v3.11, FastAPI, SQLAlchemy ORM, Pydantic v2
- **Database**: PostgreSQL v15
- **Message Broker & Cache**: Redis v7
- **AI Diagnostics**: Google Gemini API SDK (`google-generativeai`)

---

## Configuration & Environment Variables

Create a `.env` file at the root of the workspace. A template is provided in `.env.example` containing empty placeholders. For local development, copy `.env.example` to `.env` and fill in the values:

- `DATABASE_URL`: Connection string for PostgreSQL database (e.g. `postgresql://postgres:password@localhost:5432/smartqueue`).
- `REDIS_URL`: Connection URL for Redis instances (e.g. `redis://localhost:6379/0`).
- `JWT_SECRET`: Random 256-bit string to encrypt JWT session tokens.
- `GEMINI_API_KEY`: Google Gemini Flash API Key (for intelligent SRE failure classification).
- `CORS_ORIGINS`: Comma-separated list of origins allowed by CORS (e.g. your Vercel frontend URL).
- `VITE_API_URL`: Frontend API URL pointing to the deployed backend (e.g. `http://localhost:8000`).

---

## Docker Compose Quickstart (Windows & Multi-platform)

The easiest way to boot the complete stack (Database, Redis, API Backend, Frontend dashboard, and Workers) is via Docker Compose.

1. **Spin up the stack**:
   Open a PowerShell or Command Prompt in the project root:
   ```bash
   docker compose up --build
   ```
   *Note: This automatically initializes the schema, runs the seed script, and sets up a sandbox demo organization.*

2. **Scale Workers dynamically**:
   To demonstrate atomic claiming and concurrent execution under heavy loads:
   ```bash
   docker compose up --build --scale worker=3
   ```

3. **Stop the stack**:
   To stop the running containers:
   ```bash
   docker compose down
   ```

4. **Complete Reset (Delete Volumes)**:
   If you need to perform a clean start and reset the database and Redis cache storage:
   ```bash
   docker compose down -v
   ```
   > [!CAUTION]
   > Running `docker compose down -v` will permanently delete all persistent Docker volumes, dropping all saved telemetry, execution history, and seeded organization data.

5. **Access Services**:
   - **Frontend UI Dashboard**: [http://localhost:3000](http://localhost:3000)
   - **FastAPI OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Backend API Health endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Local Development Execution

If you prefer to run services individually for inspection:

### 1. Database & Redis Setup
Ensure you have local instances of Postgres and Redis running. Update your `.env` connection variables accordingly.

### 2. Backend API Server Setup
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database seeder (Optional, seeds a fresh sandboxed demo without dropping user data)
python seed.py
```

# Start API dev server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Worker Execution
You can start multiple independent terminal worker processes. They will register under unique IDs:
```bash
# Start worker 1
python -m workers.worker Worker-Alpha

# Start worker 2 (in a separate terminal)
python -m workers.worker Worker-Beta
```

### 4. Frontend Dashboard Setup
```bash
# Navigate to frontend
cd frontend

# Install package dependencies
npm install

# Run the Vite React server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Running Automated Tests

A comprehensive Pytest suite is provided. It verifies JWT credentials validation, atomic claimed locks, retry backoffs, DLQ routing, worker failure recovery sweeps, and workflow unblocking hooks.

```bash
# Navigate to backend
cd backend

# Execute Pytest
pytest -v
```

---

## Key Design Decisions & Reliability Approach

### 1. Safe Atomic Job Claiming
To prevent race conditions where multiple workers try to execute the same job, SmartQueue leverages PostgreSQL transactional row locking:
```sql
SELECT ... FROM jobs WHERE status = 'QUEUED' FOR UPDATE SKIP LOCKED LIMIT 1;
```
Combined with checking target queues' `max_concurrency` limit *inside the same database transaction*, this guarantees that:
- Workers only claim jobs they are allowed to.
- Jobs are never double-executed.
- Workers skip locked jobs and claim the next available job, maximizing processing efficiency.

### 2. Worker Heartbeats & Failure Recovery
Workers write a heartbeat status timestamp to the DB every 5 seconds. The scheduler background daemon executes an orphan-recovery process every 5 seconds. If a worker goes offline (missing heartbeats for >30 seconds):
- Its status is marked `OFFLINE`.
- Any jobs that were marked `RUNNING` or `CLAIMED` by that worker are immediately re-queued (`status = 'QUEUED'`), ensuring tasks are eventually processed.

### 3. Workflow Dependencies
Workflows are built as directed acyclic graphs (DAGs). Downstream dependent jobs are marked `BLOCKED` on creation. When an upstream parent job transitions to `COMPLETED`:
- The workflow processor inspects all downstream children.
- If all parent dependencies of a child job are `COMPLETED`, that child job transitions to `QUEUED`, making it instantly claimable by any active worker.

### 4. Gemini AI Diagnostics & Fallback
On task failure, execution telemetry is gathered.
- If `GEMINI_API_KEY` is configured: the stack trace and execution logs are processed by Gemini Flash, generating a structured diagnostics report (Root cause, severity, remediation, and transient categorization).
- If key is missing or API fails: a local regex-based analyzer executes, mapping database locking, connections, timeout exceptions, and validation failures to their safe counterparts.
- If the analyzer flags an issue as "permanent" (like validation bugs or bad email formats), the scheduler suspends retries and routes the job straight to the Dead Letter Queue (DLQ), saving computing capacity.

---

## API Examples

### 1. User Registration (`POST /auth/register`)
**Payload**:
```json
{
  "email": "dev@smartqueue.ai",
  "password": "admin123",
  "full_name": "SRE Administrator",
  "organization_name": "ACME global"
}
```

### 2. Dispatch a Job (`POST /jobs`)
**Payload**:
```json
{
  "project_id": "8fa21e86-1df2-4ce0-9883-fae4313f8aa5",
  "queue_name": "default",
  "task_name": "task_success",
  "payload": {
    "data": "sample job metadata parameters"
  },
  "priority": 3
}
```

### 3. Retrieve Failure Analysis (`GET /jobs/{id}/failure-analysis`)
**Response**:
```json
{
  "id": "e9fb841b-c741-4541-baee-1c39c84e1bfa",
  "execution_id": "4da29b4e-28b9-4a0b-9ef1-fb918a28e93c",
  "failure_reason": "Database connectivity or locking conflict",
  "severity": "MEDIUM",
  "suggested_solution": "Retry the job. Verify PostgreSQL connections count and CPU usage.",
  "is_temporary": true,
  "analyzed_at": "2026-08-19T20:45:00"
}
```

---

## Production Deployment

This project is prepared for single-click blueprint deployment to Render and Vercel.

### 1. Backend, Worker, Database, and Redis (Render)
A [`render.yaml`](file:///c:/Users/HEMA%20NITHYA/Desktop/jobschedular/render.yaml) configuration is provided in the workspace root.
1. Connect your GitHub repository to **Render**.
2. Click **Blueprints** -> **New Blueprint Instance**.
3. Select this repository.
4. Render will automatically provision:
   - **PostgreSQL Database** (`smartqueue-db`)
   - **Redis Cache/Broker** (`smartqueue-redis`)
   - **FastAPI REST API Service** (`smartqueue-backend`)
   - **Background Worker Process** (`smartqueue-worker`)
5. Configure `GEMINI_API_KEY` on Render's dashboard for the backend and worker if desired.

### 2. Frontend React Dashboard (Vercel)
1. Import the `frontend/` directory into **Vercel**.
2. Set the environment variable:
   - `VITE_API_URL`: Point this to your deployed Render backend web service URL (e.g. `https://smartqueue-backend.onrender.com`).
3. Set the build command to `npm run build` and output directory to `dist`.
4. Deploy the application.
5. In your Render backend env vars, update `CORS_ORIGINS` to match your newly deployed Vercel frontend URL to secure the endpoints.

---

## Screenshots

*(Screenshots of the live React dashboard, jobs explorer, Dead Letter Queue diagnostics, and workflow dependencies can be added here.)*

