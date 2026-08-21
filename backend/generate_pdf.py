import os
import sys
from fpdf import FPDF

class SmartQueuePDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.set_x(18)
            self.cell(174, 10, "SmartQueue - Intelligent Distributed Job Scheduler | Technical Report", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(18, 15, 192, 15)
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.line(18, 280, 192, 280)
            self.set_x(18)
            self.cell(174, 10, f"Page {self.page_no()}", align="C")

def draw_row(pdf, col_widths, texts, line_height=5, border=1, is_header=False, start_x=18, table_headers=None):
    max_nb = 1
    for i, text in enumerate(texts):
        w = col_widths[i]
        try:
            lines = pdf.multi_cell(w, line_height, text, split_only=True)
            nb = len(lines)
        except Exception:
            max_chars = max(1, int(w / 1.5))
            nb = (len(text) + max_chars - 1) // max_chars
        if nb > max_nb:
            max_nb = nb
            
    h = max_nb * line_height
    
    # Page break check
    if pdf.get_y() + h > 265:
        pdf.add_page()
        # Draw header row on new page
        if table_headers:
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(26, 54, 93)
            draw_row(pdf, col_widths, table_headers, line_height=6, border=1, is_header=True, start_x=start_x)
            # Restore normal body font
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(45, 55, 72)
            
    curr_y = pdf.get_y()
    curr_x = start_x
    
    for i, text in enumerate(texts):
        w = col_widths[i]
        pdf.set_xy(curr_x, curr_y)
        # Draw cell background/border
        pdf.cell(w, h, "", border=border)
        pdf.set_xy(curr_x, curr_y)
        # Center headers, left-align body text
        align = "C" if is_header else "L"
        if is_header:
            pdf.set_font("Helvetica", "B", 8.5)
        else:
            pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(w, line_height, text, border=0, align=align)
        curr_x += w
        
    pdf.set_xy(start_x, curr_y + h)

def create_report():
    pdf = SmartQueuePDF()
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    
    # ------------------ COVER PAGE ------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(26, 54, 93) # Deep Blue
    pdf.ln(35)
    pdf.cell(0, 15, "SmartQueue", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 15)
    pdf.set_text_color(74, 85, 104) # Slate Grey
    pdf.cell(0, 10, "Intelligent Distributed Job Scheduler & Orchestration Engine", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Draw a line separator
    pdf.set_draw_color(49, 130, 206) # Blue separator
    pdf.set_line_width(1.5)
    pdf.line(30, 85, 180, 85)
    pdf.ln(20)
    
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(45, 55, 72)
    pdf.cell(0, 10, "Codity.AI Intern Assignment Submission", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    
    # Student Details Table
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(45, 55, 72)
    
    details = [
        ("Candidate Name:", "Hema Nithya Narikimilli"),
        ("Registration Number:", "227003096"),
        ("Degree & Stream:", "B.Tech Computer Science and Engineering"),
        ("Institution:", "SASTRA Deemed University"),
        ("Live Demo Portal:", "https://nithyanarikimilli.github.io/jobschedular/"),
        ("GitHub Repository:", "https://github.com/nithyanarikimilli/jobschedular")
    ]
    
    col_width_a = 55
    col_width_b = 119
    for label, val in details:
        pdf.set_x(25)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(45, 55, 72)
        pdf.cell(col_width_a, 7.5, label)
        pdf.set_font("Helvetica", "", 10.5)
        if label in ["Live Demo Portal:", "GitHub Repository:"]:
            pdf.set_text_color(49, 130, 206) # Link blue
        else:
            pdf.set_text_color(74, 85, 104)
        pdf.cell(col_width_b, 7.5, val, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(35)
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.set_text_color(113, 128, 150)
    pdf.cell(0, 10, "Document Version: 1.0.0 | August 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    # ------------------ TABLE OF CONTENTS ------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 54, 93)
    pdf.set_x(18)
    pdf.cell(174, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    toc_items = [
        ("1. Project Overview", 3),
        ("2. Objectives & Assignment Requirements", 3),
        ("3. System Architecture Blueprint", 4),
        ("4. Database Design & Entity Relationships", 5),
        ("5. Job Lifecycle & State Machine Transitions", 7),
        ("6. Concurrency Control & Atomic Claiming", 8),
        ("7. Retry Strategies & Backoff Calculations", 8),
        ("8. Worker Daemon Service Architecture", 9),
        ("9. REST API Endpoint Specifications", 10),
        ("10. React Frontend Dashboard Interface", 11),
        ("11. Intelligent AI Failure Analysis Integration", 11),
        ("12. Automated Testing Suite & Test Verification", 12),
        ("13. Architecture Trade-offs & Design Decisions", 13),
        ("14. Local Development and Cloud Deployment Config", 13),
        ("15. Frontend Visual Layout & UI wireframes", 15),
        ("16. Project Workspace Directory Structure", 16),
        ("17. Conclusion", 17),
        ("18. Final submission & Live Links", 17)
    ]
    
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(45, 55, 72)
    for title, page in toc_items:
        pdf.set_x(18)
        dots = "." * (80 - len(title))
        pdf.cell(150, 8.5, f"{title} {dots}")
        pdf.cell(24, 8.5, str(page), align="R", new_x="LMARGIN", new_y="NEXT")

    # Helper function for headings
    def add_heading(text, num_str):
        pdf.ln(6)
        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 13.5)
        pdf.set_text_color(26, 54, 93)
        pdf.cell(174, 10, f"{num_str}. {text}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(226, 232, 240)
        pdf.line(18, pdf.get_y(), 192, pdf.get_y())
        pdf.ln(3.5)

    # Helper function for text paragraphs (Justified alignment)
    def add_p(text):
        pdf.set_x(18)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(45, 55, 72)
        pdf.multi_cell(174, 5.5, text, align="J")
        pdf.ln(3.5)

    # Helper function for subheadings
    def add_subheading(text):
        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(45, 55, 72)
        pdf.cell(174, 8, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # ------------------ 1. PROJECT OVERVIEW ------------------
    pdf.add_page()
    add_heading("Project Overview", "1")
    add_p(
        "SmartQueue is a production-ready, highly reliable distributed background job scheduler designed "
        "to decouple resource-intensive, long-running processes (e.g. data ingestion, workflow pipeline steps, "
        "network calls, and validation logic) from the primary HTTP application request-response thread loop. "
        "In modern multi-tenant web applications, executing heavy computations synchronously inside HTTP requests "
        "causes socket timeouts, spikes in memory usage, and degraded user experience. Decoupling these processes "
        "ensures high availability, fault-tolerance, and scalable operations."
    )
    add_p(
        "The primary engineering problem solved by SmartQueue is the coordination of multiple worker daemons executing "
        "jobs concurrently from a shared, multi-tenant database. It prevents double-execution or race conditions "
        "during task claiming, respects dynamic queue-level concurrency limits, and tracks the exact state of "
        "workers and jobs. Additionally, SmartQueue integrates automated failure diagnostics via Google Gemini Flash "
        "API to analyze stack traces and decide whether failed jobs should be retried or quarantined in the Dead Letter Queue (DLQ)."
    )

    # ------------------ 2. OBJECTIVES ------------------
    add_heading("Objectives & Assignment Requirements", "2")
    add_p(
        "To satisfy the Codity.AI internship specifications, the system implements a series of functional "
        "and non-functional criteria aimed at building a high-grade background execution platform:"
    )
    
    objectives = [
        ("Multi-tenant Authentication", "Provides user registration and login, generating project-isolated sandbox environments (projects, default queues) automatically."),
        ("Dynamic Priority Queues", "Enables projects to establish separate queues (e.g. default, high-priority, low-priority) with unique priorities and custom concurrency caps."),
        ("Immediate & Scheduled Jobs", "Supports immediate execution, delayed tasks (with target delay in seconds), and recurring cron jobs injected automatically by a daemon loop."),
        ("Atomic Task Claiming", "Ensures that worker executors claim jobs concurrently without race conditions using transaction-level row locks."),
        ("Worker Heartbeats & Sweeper", "Workers send telemetry heartbeats every 5 seconds. A background sweep daemon marks inactive workers as offline and re-queues orphaned tasks."),
        ("Error Backoff Strategies", "Implements Fixed delay, Linear backoff, and Exponential backoff retry policies to handle transient execution issues."),
        ("Dead Letter Queue (DLQ)", "Isolates permanently failed tasks or those exceeding maximum retry thresholds into a quarantined table to avoid resource wastage."),
        ("AI Diagnostics SRE Helper", "Uses Gemini Flash API to perform automated log audits, diagnosing root cause, severity, and transience with safe local regex fallback loops.")
    ]
    
    for title, desc in objectives:
        draw_row(pdf, [45, 129], [title, desc], line_height=5.5, border=0, start_x=18)
    pdf.ln(5)

    # ------------------ 3. SYSTEM ARCHITECTURE ------------------
    pdf.add_page()
    add_heading("System Architecture Blueprint", "3")
    add_p(
        "SmartQueue employs a decoupled microservices-based system architecture where the web client, the API backend, "
        "and background worker daemons communicate asynchronously via shared PostgreSQL and Redis storage. "
        "This design supports horizontal scaling of both web API containers and worker executors."
    )
    
    # Draw vector architecture diagram
    # Page width is 210, margins are 18. Printable width = 174.
    # Center is X = 105.
    
    # Helper functions for drawing
    def draw_box(x, y, w, h, text, bg_color=(237, 242, 249), text_color=(45, 55, 72)):
        pdf.set_fill_color(*bg_color)
        pdf.set_draw_color(79, 128, 194)
        pdf.set_line_width(0.4)
        pdf.rect(x, y, w, h, style="DF")
        pdf.set_xy(x, y + (h - 4) / 2) # Center text vertically
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*text_color)
        pdf.cell(w, 4, text, align="C")

    def draw_arrow(x1, y1, x2, y2, direction="down"):
        pdf.set_draw_color(74, 85, 104)
        pdf.set_line_width(0.3)
        pdf.line(x1, y1, x2, y2)
        if direction == "down":
            pdf.line(x2, y2, x2 - 1.5, y2 - 2.5)
            pdf.line(x2, y2, x2 + 1.5, y2 - 2.5)
        elif direction == "up":
            pdf.line(x2, y2, x2 - 1.5, y2 + 2.5)
            pdf.line(x2, y2, x2 + 1.5, y2 + 2.5)
        elif direction == "right":
            pdf.line(x2, y2, x2 - 2.5, y2 - 1.5)
            pdf.line(x2, y2, x2 - 2.5, y2 + 1.5)
        elif direction == "left":
            pdf.line(x2, y2, x2 + 2.5, y2 - 1.5)
            pdf.line(x2, y2, x2 + 2.5, y2 + 1.5)

    start_y = pdf.get_y() + 5
    
    # 1. React Box
    draw_box(65, start_y, 80, 10, "React (Vite) Dashboard Portal")
    
    # Arrow 1: React -> FastAPI
    draw_arrow(105, start_y + 10, 105, start_y + 25, "down")
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(105 - 50, start_y + 14)
    pdf.cell(100, 4, "REST API Calls (HTTP JSON / Bearer JWT)", align="C")
    
    # 2. FastAPI Box
    draw_box(65, start_y + 25, 80, 10, "FastAPI REST API Backend Service")
    
    # Arrow 2: FastAPI -> Postgres
    draw_arrow(105, start_y + 35, 105, start_y + 50, "down")
    pdf.set_xy(105 - 50, start_y + 39)
    pdf.cell(100, 4, "SQLAlchemy ORM Transactions", align="C")
    
    # Arrow 2b (horizontal-down-L-shape to Redis)
    pdf.set_draw_color(74, 85, 104)
    pdf.line(145, start_y + 30, 172.5, start_y + 30)
    draw_arrow(172.5, start_y + 30, 172.5, start_y + 50, "down")
    pdf.set_xy(145, start_y + 26)
    pdf.cell(30, 4, "Pub/Sub", align="C")
    
    # 3. Postgres Box
    draw_box(65, start_y + 50, 80, 10, "PostgreSQL Database Layer (Neon)")
    
    # 3b. Redis Box
    draw_box(150, start_y + 50, 45, 10, "Redis Cache (Upstash)")
    
    # Double-headed arrow between Postgres and Redis
    pdf.line(145, start_y + 55, 150, start_y + 55)
    draw_arrow(145, start_y + 55, 145, start_y + 55, "left")
    draw_arrow(150, start_y + 55, 150, start_y + 55, "right")
    pdf.set_xy(141, start_y + 51)
    pdf.cell(13, 4, "Sync", align="C")
    
    # Arrow 3: Postgres -> Workers
    draw_arrow(105, start_y + 60, 105, start_y + 75, "down")
    pdf.set_xy(105 - 50, start_y + 64)
    pdf.cell(100, 4, "FOR UPDATE SKIP LOCKED Row Locking", align="C")
    
    # Heartbeats from workers back to Redis (L-shape up)
    pdf.line(145, start_y + 80, 172.5, start_y + 80)
    draw_arrow(172.5, start_y + 80, 172.5, start_y + 60, "up")
    pdf.set_xy(145, start_y + 81)
    pdf.cell(30, 4, "Worker Telemetry", align="C")
    
    # 4. Workers Box
    draw_box(65, start_y + 75, 80, 10, "Background Worker Daemons")
    
    # Arrow 4: Workers -> Gemini
    draw_arrow(105, start_y + 85, 105, start_y + 100, "down")
    pdf.set_xy(105 - 50, start_y + 89)
    pdf.cell(100, 4, "Diagnostics & SRE Sizing Analysis", align="C")
    
    # 5. Gemini Box
    draw_box(65, start_y + 100, 80, 10, "Google Gemini AI Engine")
    
    # Arrow 5: Gemini -> Fallback
    draw_arrow(145, start_y + 105, 150, start_y + 105, "right")
    pdf.set_xy(145, start_y + 101)
    pdf.cell(30, 4, "Fallback Regex", align="C")
    
    # 5b. Fallback Box
    draw_box(150, start_y + 100, 45, 10, "Fallback Regex Heuristics")
    
    # Caption below diagram
    pdf.set_xy(18, start_y + 115)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(174, 5, "Figure 3.1: Centered System Architecture Diagram & Data Communication Flows", align="C")
    
    pdf.set_xy(18, start_y + 124)
    pdf.ln(5)
    
    add_subheading("Communication Flows")
    
    flows = [
        ("React Client -> FastAPI:", "Dispatches job payloads, fetches real-time queue states, and views diagnostics."),
        ("FastAPI -> PostgreSQL:", "Writes job registration records, structures tenant organizations, and updates metadata."),
        ("Workers -> PostgreSQL:", "Locks and claims queued tasks atomically using transactional query loops and updates heartbeat statistics."),
        ("Workers -> Redis:", "Coordinates node health checks and synchronization states.")
    ]
    
    for i, (title, desc) in enumerate(flows):
        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(45, 55, 72)
        pdf.multi_cell(174, 5, f"{i+1}. {title}", align="L")
        pdf.set_x(18)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(74, 85, 104)
        pdf.multi_cell(174, 5, f"   {desc}", align="L")
        pdf.ln(2.5)

    # ------------------ 4. DATABASE DESIGN ------------------
    pdf.add_page()
    add_heading("Database Design & Entity Relationships", "4")
    add_p(
        "The relational database schema is designed to enforce strict transaction-level consistency (ACID compliance) "
        "and maintain reference integrity. The database is provisioned in PostgreSQL and mapped in python using SQLAlchemy ORM. "
        "The complete schema consists of the following 15 distinct tables:"
    )
    
    tables_list = [
        ("organizations", "Holds tenant boundaries. PK: id (UUID). Fields: name (VARCHAR), created_at (DATETIME)."),
        ("users", "Admin accounts. PK: id (UUID). FK: organization_id. Unique index: ix_users_email. Fields: hashed_password, full_name."),
        ("projects", "Namespace boundaries. PK: id (UUID). FK: organization_id. Groups queues, workflows, and jobs."),
        ("queues", "Task dispatch channels. PK: id (UUID). FK: project_id. Composite unique index: uq_queues_project_id_name. Priority (INT), max_concurrency (INT)."),
        ("jobs", "Core tasks. PK: id (UUID). FKs: project_id, queue_id, workflow_id, retry_policy_id, worker_id. Status Enum, retry_count, scheduled_at."),
        ("job_executions", "Tracks attempts. PK: id (UUID). FKs: job_id, worker_id. attempt_number, status, started_at, ended_at, duration, error_message, stack_trace."),
        ("job_logs", "Task terminal outputs. PK: id (UUID). FKs: job_id, execution_id. log_level, message, created_at."),
        ("retry_policies", "Backoff profiles. PK: id (UUID). backoff_type Enum (FIXED, LINEAR, EXPONENTIAL), base_delay, max_retries."),
        ("workflows", "DAG pipelines. PK: id (UUID). FK: project_id. status Enum (PENDING, RUNNING, COMPLETED, FAILED), name, description."),
        ("workflow_dependencies", "Links DAG steps. PK: id (UUID). FKs: workflow_id, parent_job_id, child_job_id."),
        ("workers", "Executors. PK: id (UUID). name, status Enum (ACTIVE, IDLE, BUSY, OFFLINE), last_heartbeat, jobs_completed, jobs_failed, system_info."),
        ("worker_heartbeats", "Telemetry logs. PK: id (UUID). FK: worker_id. timestamp, status, system_info (JSON)."),
        ("scheduled_jobs", "Cron templates. PK: id (UUID). FKs: project_id, queue_id, retry_policy_id. cron_expression, payload, next_run_at, is_active."),
        ("dead_letter_jobs", "Quarantined failures. PK: id (UUID). FKs: job_id (Unique), project_id, queue_id, execution_id. failed_at, failure_reason."),
        ("ai_analyses", "Gemini SRE diagnostics. PK: id (UUID). FK: execution_id (Unique). failure_reason, severity, suggested_solution, is_temporary.")
    ]

    # Render schema list
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(26, 54, 93)
    draw_row(pdf, [42, 132], ["Table Name", "Schema Design & Field Specifications"], line_height=6, border=1, is_header=True, start_x=18)
    
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(45, 55, 72)
    for name, desc in tables_list:
        draw_row(pdf, [42, 132], [name, desc], line_height=5.5, border=1, is_header=False, start_x=18, table_headers=["Table Name", "Schema Design & Field Specifications"])
    pdf.ln(5)

    add_subheading("Relational Database Entity Relationship (ER) Graph")
    
    er_diagram = (
        "  [organizations] 1 ----- * [users]\n"
        "         1\n"
        "         |\n"
        "         * \n"
        "    [projects] 1 ----- * [queues] 1 ----- * [jobs]\n"
        "         |                                   |\n"
        "         |                                   + 1 ----- * [job_executions] 1 ----- 1 [ai_analyses]\n"
        "         |                                   |\n"
        "         |                                   + 1 ----- * [job_logs]\n"
        "         |                                   |\n"
        "         |                                   + 1 ----- 0..1 [dead_letter_jobs]\n"
        "         *\n"
        "    [workflows] 1 ---- * [workflow_dependencies]\n"
    )
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_font("Courier", "", 8.5)
    pdf.set_x(18)
    pdf.multi_cell(174, 5.5, er_diagram, border=1, fill=True)
    pdf.ln(4)

    # ------------------ 5. JOB LIFECYCLE ------------------
    pdf.add_page()
    add_heading("Job Lifecycle & State Machine Transitions", "5")
    add_p(
        "SmartQueue jobs progress through a formal state-machine model to ensure transaction safety, "
        "execution auditing, and workflow triggers. Downstream child tasks remain BLOCKED until all parents complete."
    )
    
    lifecycle_flow = (
        " [BLOCKED] --(Parent tasks complete)--> [QUEUED]\n"
        "                                           |\n"
        " [SCHEDULED] --(Scheduled time reached)----+ (Worker Selects Row)\n"
        "                                           v\n"
        "                                       [CLAIMED]\n"
        "                                           |\n"
        "                                           v\n"
        "                                       [RUNNING]\n"
        "                                        /     \\\n"
        "                             (Success) /       \\ (Failure & Retries Exhausted)\n"
        "                                      v         v\n"
        "                                [COMPLETED]   [DLQ] (Quarantined)\n"
        "                                     | \n"
        "                                     +--(Triggers workflow children unblock)\n"
    )
    pdf.set_fill_color(245, 247, 250)
    pdf.set_font("Courier", "", 8.5)
    pdf.set_x(18)
    pdf.multi_cell(174, 5.5, lifecycle_flow, border=1, fill=True)
    pdf.ln(4)
    
    add_p(
        "Transition Rules:\n"
        "1. QUEUED: Immediate task ready for any worker. Available scheduled jobs become queued when scheduled_at <= NOW().\n"
        "2. CLAIMED: A worker locks the job row, assigning its worker_id.\n"
        "3. RUNNING: The job is executing. Attempt count is incremented, started_at timestamp is logged.\n"
        "4. COMPLETED: The task exits successfully. Its outputs are recorded. Downstream dependencies are resolved.\n"
        "5. FAILED / DLQ: If a task raises an error, the AI failure analyzer categorizes it. Temporary failures transition back to QUEUED after backoff delay. Permanent failures (or those exceeding max_retries) route directly to DLQ status."
    )

    # ------------------ 6. CONCURRENCY CONTROL ------------------
    pdf.add_page()
    add_heading("Concurrency Control & Atomic Claiming", "6")
    add_p(
        "In a distributed scheduler environment, a critical challenge is ensuring that multiple concurrent worker processes "
        "do not double-claim or double-execute the same job task. SmartQueue solves this at the database transaction layer "
        "using PostgreSQL native row locking (SELECT FOR UPDATE SKIP LOCKED)."
    )
    
    sql_query = (
        "SELECT jobs.* FROM jobs \n"
        "JOIN queues ON jobs.queue_id = queues.id \n"
        "WHERE jobs.status = 'QUEUED' AND queues.is_paused = FALSE \n"
        "  AND jobs.scheduled_at <= NOW() \n"
        "ORDER BY jobs.priority DESC, jobs.created_at ASC \n"
        "LIMIT 1 FOR UPDATE SKIP LOCKED;"
    )
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_font("Courier", "", 8.5)
    pdf.set_x(18)
    pdf.multi_cell(174, 5, sql_query, border=1, fill=True)
    pdf.ln(4)
    
    add_p(
        "Claim Mechanism Explanation:\n"
        "1. Atomic Row Lock: The FOR UPDATE lock instructs PostgreSQL to lock the matched job rows for the duration of the current transaction. If another worker queries the DB, it blocks on these rows.\n"
        "2. Throughput Efficiency: SKIP LOCKED overrides blocking behavior, instructing the DBMS to ignore locked rows and immediately select the next available queued job. Workers process tasks in parallel without waiting.\n"
        "3. Concurrency Limits Enforced: Before locking rows, the claiming session checks the active running count of jobs in the queue against its max_concurrency. If the limit is reached, the worker skips that queue for that sweep. This dynamic check is executed atomically inside the database transaction."
    )

    # ------------------ 7. RETRY STRATEGIES ------------------
    add_heading("Retry Strategies & Backoff Calculations", "7")
    add_p(
        "SmartQueue supports three backoff models to schedule retries dynamically on transient exceptions. "
        "The delay seconds progression for base_delay = 5 seconds is calculated as follows:"
    )
    
    retry_data = [
        ("Retry Attempt", "FIXED Delay (base)", "LINEAR Delay (base * (count+1))", "EXPONENTIAL Delay (base * (2**count))"),
        ("Attempt 1 (count=0)", "5 seconds", "5 seconds", "5 seconds"),
        ("Attempt 2 (count=1)", "5 seconds", "10 seconds", "10 seconds"),
        ("Attempt 3 (count=2)", "5 seconds", "15 seconds", "20 seconds"),
        ("Attempt 4 (count=3)", "5 seconds", "20 seconds", "40 seconds")
    ]

    # Table layout
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(26, 54, 93)
    draw_row(pdf, [38, 45, 46, 45], retry_data[0], line_height=7, border=1, is_header=True, start_x=18)
    
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(45, 55, 72)
    for row in retry_data[1:]:
        draw_row(pdf, [38, 45, 46, 45], row, line_height=7.5, border=1, is_header=False, start_x=18, table_headers=retry_data[0])
    pdf.ln(5)

    # ------------------ 8. WORKER DAEMON ------------------
    pdf.add_page()
    add_heading("Worker Daemon Service Architecture", "8")
    add_p(
        "The worker executor daemon is built as an independent multi-threaded application designed to scale horizontally. "
        "Upon startup, the worker initializes a thread pool matching its CPU core allocations, registers its worker UUID "
        "and details in the database, and begins executing the claim cycle."
    )
    add_p(
        "Core Worker Mechanics:\n"
        "- Polling Loop: Workers sweep the database for queued jobs every second.\n"
        "- Telemetry Heartbeats: Workers send heartbeats to the database every 5 seconds, updating last_heartbeat timestamps and system information (CPU/memory usages).\n"
        "- Inactive Worker Sweeper: A background thread sweeps the workers table. If a worker fails to send heartbeats for >30 seconds, it is marked OFFLINE. Any jobs left in CLAIMED or RUNNING status by that worker are automatically rolled back, reset to QUEUED, and their worker_id is cleared.\n"
        "- Graceful Shutdown: The worker registers intercepts for SIGINT and SIGTERM. On shutdown, it stops claiming new jobs, allows active threads to complete their execution, writes terminal completion stats, updates its status to OFFLINE, and exits safely. This prevents corrupted job states during redeployments."
    )

    # ------------------ 9. REST API DOCUMENTATION ------------------
    pdf.add_page()
    add_heading("REST API Endpoint Specifications", "9")
    add_p(
        "The FastAPI REST API provides a complete set of CRUD and control endpoints for managing users, projects, "
        "queues, jobs, workers, workflows, and failure analyses. All data schemas are enforced via Pydantic v2."
    )
    
    endpoints = [
        ("POST", "/auth/register", "Public", "Registers tenant organization, default project, priority queues, SRE user account, and returns JWT access token."),
        ("POST", "/auth/login", "Public", "Authenticates user credentials and returns a Bearer access token."),
        ("GET", "/projects", "JWT Token", "Lists all projects linked to the user's organization."),
        ("POST", "/projects", "JWT Token", "Creates a new project namespace (requires: name)."),
        ("GET", "/queues", "JWT Token", "Lists queues within the selected project. Optional project_id filter."),
        ("POST", "/queues", "JWT Token", "Creates a custom queue (name, priority, max_concurrency) within a project."),
        ("POST", "/queues/{id}/pause", "JWT Token", "Pauses queue processing. Active workers skip claiming jobs from this queue."),
        ("POST", "/queues/{id}/resume", "JWT Token", "Resumes queue processing, re-enabling job claiming sweeps."),
        ("GET", "/queues/{id}/stats", "JWT Token", "Returns queue stats (name, current depth, completed count, failed count)."),
        ("GET", "/jobs", "JWT Token", "Lists jobs. Supports filtering by status, priority, search text, limit/offset paging."),
        ("POST", "/jobs", "JWT Token", "Dispatches immediate or delayed job (project_id, queue_name, task_name, payload, priority)."),
        ("GET", "/jobs/{id}", "JWT Token", "Retrieves complete metadata details for a specific job."),
        ("GET", "/jobs/{id}/executions", "JWT Token", "Retrieves all execution history records for a job."),
        ("GET", "/jobs/{id}/logs", "JWT Token", "Retrieves execution log entries matching a job ID."),
        ("POST", "/jobs/{id}/retry", "JWT Token", "Manually schedules an immediate retry attempt for a failed or dead job."),
        ("POST", "/jobs/{id}/cancel", "JWT Token", "Cancels a queued or scheduled job, preventing execution."),
        ("GET", "/workers", "JWT Token", "Lists all active worker daemons, metrics, and heartbeat statuses."),
        ("GET", "/dlq", "JWT Token", "Retrieves all failed jobs quarantined in the Dead Letter Queue."),
        ("GET", "/workflows", "JWT Token", "Lists all visual multi-step workflow pipelines."),
        ("POST", "/workflows", "JWT Token", "Creates a sequential workflow pipeline defining jobs and parent/child dependencies."),
        ("GET", "/jobs/{id}/failure-analysis", "JWT Token", "Retrieves SRE failure diagnostics (cause, severity, solution) for a crashed job.")
    ]

    # Render API table
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(26, 54, 93)
    draw_row(pdf, [18, 44, 18, 98], ["Method", "Endpoint Path", "Auth", "Description & Purpose"], line_height=6, border=1, is_header=True, start_x=18)
    
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(45, 55, 72)
    for method, path, auth_req, desc in endpoints:
        draw_row(pdf, [18, 44, 18, 98], [method, path, auth_req, desc], line_height=5.5, border=1, is_header=False, start_x=18, table_headers=["Method", "Endpoint Path", "Auth", "Description & Purpose"])
    pdf.ln(5)

    # ------------------ 10. FRONTEND / DASHBOARD ------------------
    pdf.add_page()
    add_heading("React Frontend Dashboard Interface", "10")
    add_p(
        "The user dashboard is built as a single-page application in React, styled with vanilla Tailwind CSS. "
        "It provides real-time monitoring of job schedules, worker states, and queue depths."
    )
    add_p(
        "Key Frontend Components:\n"
        "1. Metrics Dashboard: Displays four KPI cards (Total Jobs, Running Jobs, Completed Jobs, Failed Jobs/DLQ) "
        "and active worker counts. Dynamic calculations show success rates and overall system health (HEALTHY, WARNING, "
        "CRITICAL) determined by historical failure rates and DLQ depth.\n"
        "2. Queue Management: Displays a grid of project queues. Admins can pause/resume queues and update max_concurrency caps dynamically.\n"
        "3. Job Explorer: Features full text search, status filters (QUEUED, RUNNING, COMPLETED, FAILED, DLQ), and execution log modals.\n"
        "4. AI SRE Diagnostics Modal: Opens when a failed job is clicked. Displays a structured diagnostics report (crashed line, error message, "
        "severity tag, and recommended solutions generated by Gemini AI or rule fallbacks).\n"
        "5. Workflow Builder/Visualizer: Displays dependency chains (DAGs) and traces child execution progression."
    )

    # ------------------ 11. AI FAILURE ANALYSIS ------------------
    add_heading("Intelligent AI Failure Analysis Integration", "11")
    add_p(
        "On task execution failure, execution telemetry is gathered. SmartQueue uses Google Gemini Flash (gemini-1.5-flash) "
        "to generate automated failure diagnostic reports. If `GEMINI_API_KEY` is missing or the external API call fails, "
        "a regex-based parser executes as a fallback."
    )
    add_p(
        "Rule-Based Fallback Parser Heuristics:\n"
        "- Transient Network / Timeout: Matches keywords (timeout, socket.timeout, connection timeout, connection refused, max retries exceeded). Returns MEDIUM severity and schedules a retry attempt.\n"
        "- Database Operational Conflict: Matches deadlock, psycopg2.OperationalError, lock timeout, connection limit exceeded. Returns MEDIUM severity, schedules retry.\n"
        "- Authentication/Authorization Failure: Matches unauthorized, forbidden, permission denied, 401, 403. Returns CRITICAL severity, halts retries, and flags job as permanent failure.\n"
        "- Invalid Arguments / Validation Bug: Matches ValueError, KeyError, TypeError, SyntaxError, ValidationError. Returns HIGH severity, flags job as permanent failure, and routes to DLQ immediately."
    )

    # ------------------ 12. TESTING SUITE ------------------
    pdf.add_page()
    add_heading("Automated Testing Suite & Test Verification", "12")
    add_p(
        "SmartQueue implements a pytest testing suite covering critical system components. "
        "The test cases are located in `backend/tests/test_smartqueue.py`. All 11 tests have run and passed successfully:"
    )
    
    tests = [
        ("test_user_registration_creates_sandbox", "Verifies registration flow. Creates Organization, User, main Project, and default queues ('default', 'high-priority')."),
        ("test_queue_pause_resume_stats", "Creates a queue, triggers pause and resume endpoints, and checks queue depth stats."),
        ("test_immediate_job_execution", "Claims a job, runs task_success from the registry, and marks status COMPLETED."),
        ("test_backoff_calculations", "Verifies mathematical delay progression for FIXED (5s), LINEAR (5s, 10s, 15s), and EXPONENTIAL (5s, 10s, 20s) models."),
        ("test_failed_job_moves_to_dlq", "Verifies retry limits. Failing jobs retry until attempt exceeds max_retries, then move to DLQ."),
        ("test_workflow_dependency_execution", "Verifies DAG unblocking. Child job status is BLOCKED and transitions to QUEUED when the parent job completes."),
        ("test_worker_recovery_orphaned_jobs", "Simulates worker crash. Offline sweep daemon detects missing heartbeat, updates status to OFFLINE, and resets jobs to QUEUED."),
        ("test_atomic_claiming_concurrency", "Spawns 5 threads claiming jobs from a queue of 10 tasks concurrently, verifying that no job is double-claimed."),
        ("test_workspace_registration_flow", "Verifies project queue isolation, registration idempotency, and restoration of missing default queues."),
        ("test_queue_uniqueness_within_project", "Asserts composite key constraints block duplicate queues under a single project but allow identical names in different projects."),
        ("test_registration_transaction_rollback", "Tests transaction rollbacks. DB operations roll back cleanly if registration fails (e.g. invalid name length).")
    ]
    
    # Render test table
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(26, 54, 93)
    draw_row(pdf, [64, 110], ["Test Case Name", "Functional Behavior Verified"], line_height=6, border=1, is_header=True, start_x=18)
    
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(45, 55, 72)
    for t_name, t_desc in tests:
        draw_row(pdf, [64, 110], [t_name, t_desc], line_height=5.5, border=1, is_header=False, start_x=18, table_headers=["Test Case Name", "Functional Behavior Verified"])
    pdf.ln(5)

    # ------------------ 13. TRADE-OFFS & DESIGN DECISIONS ------------------
    pdf.add_page()
    add_heading("Architecture Trade-offs & Design Decisions", "13")
    add_p(
        "1. PostgreSQL Row-level Transactional Locks vs Redis Queue Brokers:\n"
        "Instead of using dedicated queues (like Celery, BullMQ, or RabbitMQ), SmartQueue uses PostgreSQL with the SELECT FOR UPDATE SKIP LOCKED clause. "
        "While Redis is faster, using PostgreSQL provides strict transaction isolation (ACID compliance). State transitions (e.g. worker heartbeats, execution logs, and workflow dependencies) are managed in a single database, preventing state desynchronization. Performance is optimized using indices on status, priority, and scheduled_at columns.\n\n"
        "2. Heartbeat Telemetry & Daemon Sweeper vs Active WebSocket Streams:\n"
        "Workers write heartbeat status timestamps to the database every 5 seconds. A background sweeper sweeps for dead workers (missing heartbeats for >30 seconds). "
        "This design handles temporary network drops without prematurely marking workers as offline, guaranteeing recovery of orphaned tasks.\n\n"
        "3. Decoupled Multi-threaded Workers:\n"
        "Workers run in separate processes from the FastAPI server. This prevents memory leaks or high CPU usage from background jobs from affecting the responsiveness of the REST API."
    )

    # ------------------ 14. DEPLOYMENT SETUP ------------------
    add_heading("Local Development and Cloud Deployment Config", "14")
    add_subheading("Production Configuration (Render & Vercel)")
    add_p(
        "- Frontend Dashboard: Deployed to GitHub Pages (https://nithyanarikimilli.github.io/jobschedular/). It communicates with the backend REST API.\n"
        "- FastAPI Backend REST API: Deployed as a web service on Render. It handles routing and dashboard summary computations.\n"
        "- Worker Daemon Process: Runs on Render as an independent background worker service executing the polling loop.\n"
        "- Database Layer: Serverless PostgreSQL hosted on Neon.\n"
        "- Cache/Synchronization Broker: Redis hosted on Upstash.\n"
        "- Environment Variables: DATABASE_URL, REDIS_URL, SECRET_KEY, GEMINI_API_KEY, VITE_API_URL."
    )
    
    add_subheading("Local Execution (Docker Compose / Terminal)")
    add_p(
        "1. Set up database and Redis connection configurations in a local `.env` file.\n"
        "2. To spin up all services (Database, Redis, API Backend, Frontend, Workers) using Docker:\n"
        "   docker compose up --build\n"
        "3. Scale background workers dynamically to test atomic claiming:\n"
        "   docker compose up --build --scale worker=3\n"
        "4. To run backend services locally:\n"
        "   cd backend && pip install -r requirements.txt && python seed.py\n"
        "   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000\n"
        "5. Start worker executors: python -m workers.worker Worker-Alpha\n"
        "6. Launch React client: cd frontend && npm install && npm run dev"
    )

    # ------------------ 15. VISUAL LAYOUTS ------------------
    pdf.add_page()
    add_heading("Frontend Visual Layout & UI wireframes", "15")
    add_p(
        "Since Playwright cannot download its drivers in the current sandbox environment, we have mapped out the "
        "Frontend UI dashboard layout and widgets below using ASCII wireframe blocks."
    )
    
    add_subheading("Main SRE Analytics Dashboard Layout Wireframe")
    dash_wireframe = (
        "+-----------------------------------------------------------------------------------+\n"
        "|  [SmartQueue SRE Portal]             Tenant: SmartQueue Global   Project: Ops CC  |\n"
        "+-----------------------------------------------------------------------------------+\n"
        "|  +------------------+  +------------------+  +------------------+  +-----------+  |\n"
        "|  | TOTAL JOBS: 152  |  | RUNNING JOBS: 3  |  | COMPLETED: 142   |  | DLQ: 7    |  |\n"
        "|  +------------------+  +------------------+  +------------------+  +-----------+  |\n"
        "|                                                                                   |\n"
        "|  +--------------------------------------------+  +-----------------------------+  |\n"
        "|  |  Active Queue Health Metrics Monitor       |  | Worker Executors Registry   |  |\n"
        "|  |  * default (Priority 1) ..... HEALTHY      |  | * Worker-Alpha  [ACTIVE]    |  |\n"
        "|  |  * high-priority (P 3) ..... HEALTHY      |  | * Worker-Beta   [BUSY]      |  |\n"
        "|  |  * low-priority (P 0) ...... WARNING      |  | * Worker-Gamma  [OFFLINE]   |  |\n"
        "|  +--------------------------------------------+  +-----------------------------+  |\n"
        "|                                                                                   |\n"
        "|  +-----------------------------------------------------------------------------+  |\n"
        "|  |  Job Scheduler Telemetry Timeline (Last 24 hours - charts)                 |  |\n"
        "|  +-----------------------------------------------------------------------------+  |\n"
        "+-----------------------------------------------------------------------------------+\n"
    )
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_font("Courier", "", 8.5)
    pdf.set_x(18)
    pdf.multi_cell(174, 4.5, dash_wireframe, border=1, fill=True)
    pdf.ln(5)

    add_subheading("Intelligent AI Diagnostics failure Analysis Modal Wireframe")
    diag_wireframe = (
        "+-----------------------------------------------------------------------------------+\n"
        "| [X] AI FAILURE DIAGNOSTICS -- Job ID: e9fb841b-c741-4541-baee-1c39c84e1bfa        |\n"
        "+-----------------------------------------------------------------------------------+\n"
        "|  * Task Name: task_network_error                                                  |\n"
        "|  * Active Queue: default (priority 1)                                             |\n"
        "|  * Failed Attempt: 1 / 3                                                          |\n"
        "|  * Severity Level: [ MEDIUM ]    Transience Category: [ TEMPORARY ]               |\n"
        "|                                                                                   |\n"
        "|  +-----------------------------------------------------------------------------+  |\n"
        "|  | Root Cause Diagnostic Analysis:                                             |  |\n"
        "|  | Transient Network Failure. connection refused on port 443 at api.github.com |  |\n"
        "|  +-----------------------------------------------------------------------------+  |\n"
        "|  +-----------------------------------------------------------------------------+  |\n"
        "|  | Suggested SRE Solution / Remediation:                                       |  |\n"
        "|  | Verify network routing. Job is flagged transient; auto-retry scheduled.     |  |\n"
        "|  +-----------------------------------------------------------------------------+  |\n"
        "|                                                                                   |\n"
        "|  [ Close Panel ]                                        [ Manual Trigger Retry ]  |\n"
        "+-----------------------------------------------------------------------------------+\n"
    )
    pdf.set_x(18)
    pdf.multi_cell(174, 4.5, diag_wireframe, border=1, fill=True)
    pdf.ln(5)

    # ------------------ 16. PROJECT STRUCTURE ------------------
    pdf.add_page()
    add_heading("Project Workspace Directory Structure", "16")
    add_p(
        "Below is the file layout of the SmartQueue distributed scheduler workspace, defining "
        "the boundaries between backend routers, services, background workers, and client scripts:"
    )
    
    workspace_tree = (
        "smartqueue-workspace/\n"
        "|-- backend/\n"
        "|   |-- app/\n"
        "|   |   |-- api/            # FastAPI route controllers\n"
        "|   |   |   |-- auth.py     # Signup, login, JWT token generation\n"
        "|   |   |   |-- jobs.py     # Job dispatch, cancels, and executions\n"
        "|   |   |   |-- queues.py   # Pause/resume and max concurrency caps\n"
        "|   |   |-- core/           # Security keys, connection engine config\n"
        "|   |   |-- models/         # SQLAlchemy schema declarations (15 tables)\n"
        "|   |   |-- schemas/        # Pydantic validation payload classes\n"
        "|   |   |-- services/       # Core business logic engines\n"
        "|   |   |   |-- scheduler.py # Claim, sweep, retry, and cron loops\n"
        "|   |   |   |-- ai_analyzer.py # Gemini SRE and regex fallback models\n"
        "|   |   |-- main.py         # Main API engine and database migrations\n"
        "|   |   |-- seeder.py       # Seeds sandbox database models\n"
        "|   |-- tests/              # Pytest automated test suites\n"
        "|   |-- workers/            # Multi-threaded worker executor runners\n"
        "|-- frontend/               # React client application code\n"
        "|   |-- src/\n"
        "|   |   |-- App.jsx         # Main UI application routing and panels\n"
        "|   |   |-- api.js          # HTTP fetch calls mapped to REST API routes\n"
        "|   |-- vite.config.js      # Build parameters\n"
        "|-- docker-compose.yml      # Config for database, API, and workers\n"
        "|-- render.yaml             # Render deployment configuration\n"
        "|-- seed.py                 # Seeds local database\n"
    )
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_font("Courier", "", 9.5)
    pdf.set_x(18)
    pdf.multi_cell(174, 5.5, workspace_tree, border=1, fill=True)
    pdf.ln(5)

    # ------------------ 17. CONCLUSION ------------------
    pdf.add_page()
    add_heading("Conclusion", "17")
    add_p(
        "SmartQueue is a robust, production-inspired distributed background job scheduler designed for high-concurrency "
        "and reliable environments. By using PostgreSQL row-level transactional locks (SELECT FOR UPDATE SKIP LOCKED), "
        "it prevents race conditions and guarantees that tasks are claimed by exactly one worker. "
        "Dynamic checks enforce queue-level concurrency limits, and a background daemon handles inactive workers "
        "and recovers orphaned tasks."
    )
    add_p(
        "Integrating Gemini AI failure diagnostics helps SRE teams resolve execution errors, while the regex-based parser "
        "provides a reliable fallback. The pytest suite verifies security, transactional integrity, retries, and worker "
        "recovery. SmartQueue provides a solid architecture for processing background tasks in multi-tenant cloud applications."
    )

    # ------------------ 18. FINAL LINKS ------------------
    add_heading("Final Submission & Live Links", "18")
    add_p(
        "The complete source code and deployment URLs for the SmartQueue internship assignment are listed below. "
        "The live demo site hosts the compiled frontend, which connects to the backend REST API on Render."
    )
    
    pdf.ln(10)
    pdf.set_draw_color(49, 130, 206)
    pdf.set_line_width(1.5)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 10, "SmartQueue Project submission URLs", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(45, 55, 72)
    pdf.cell(50, 8, "Live Demo Link:", align="R")
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(49, 130, 206)
    pdf.cell(124, 8, " https://nithyanarikimilli.github.io/jobschedular/", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(45, 55, 72)
    pdf.cell(50, 8, "GitHub Repository:", align="R")
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(49, 130, 206)
    pdf.cell(124, 8, " https://github.com/nithyanarikimilli/jobschedular", new_x="LMARGIN", new_y="NEXT")
    
    # Save PDF to project root
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "227003096_Hema_Nithya_Narikimilli.pdf")
    pdf.output(output_path)
    print(f"PDF generated successfully at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_report()
