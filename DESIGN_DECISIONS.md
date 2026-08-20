# SmartQueue — Design Decisions & Reliability Blueprint

This document outlines the engineering rationale behind key architectural, database, and system-level design decisions implemented in **SmartQueue**.

---

## 1. Job Claiming: PostgreSQL Locking vs. Redis Queues

### The Decision:
SmartQueue uses PostgreSQL native row-level transactional locking (`SELECT FOR UPDATE SKIP LOCKED`) rather than external Redis-based queues (like BullMQ or Celery) for primary queue storage and job claiming.

### The Rationale:
1. **Strict Concurrency Enforcement**: Under Celery or Redis queues, enforcing dynamic queue-level concurrency limits requires complex lua scripts or distributed locks. In PostgreSQL, checking current running jobs and claiming new ones is executed in a single atomic database transaction.
2. **Transaction Integrity**: The execution log, heartbeat updates, job state transition, and workflow dependency unblocking are done in relational tables. Using Postgres as the single source of truth prevents distributed state desynchronization (e.g. where a job state changes in Redis but the database update fails due to network partitions).
3. **High Performance via `SKIP LOCKED`**: Older implementations using `FOR UPDATE` blocked multiple worker processes, creating lock contention. By appending `SKIP LOCKED`, workers skip rows that are currently locked by other transactions, enabling concurrent throughput similar to dedicated queue brokers.

---

## 2. Worker Heartbeats and Orphan Recovery

### The Decision:
Instead of workers keeping active TCP connections or WebSocket streams open, they write heartbeat records to the database every 5 seconds. A background sweep process monitors these timestamps and triggers automatic job recovery.

### The Rationale:
1. **Network Partition Resiliency**: Temporary worker network drops do not immediately trigger false failures. The recovery timeout is set to 30 seconds.
2. **Orphan Recovery Guarantee**: When a worker container crashes (e.g. due to Out of Memory errors), any job it claimed remains in state `RUNNING` forever. The recovery daemon detects the offline worker, resets the job status back to `QUEUED`, increments the failure attempt, logs the recovery action, and makes it available for other workers.

---

## 3. Workflow Dependency Engine

### The Decision:
Workflow execution is modeled using a relational Directed Acyclic Graph (DAG) schema. Downstream steps start with a state of `BLOCKED`. Transitions are triggered *only* when upstream predecessors succeed.

### The Rationale:
1. **State Simplicity**: Workers do not need to understand workflow topology. They simply query for `QUEUED` jobs. The dependency check is deferred to a post-success transaction handler.
2. **Bypass on Failure**: If any upstream node fails permanently and lands in the Dead Letter Queue (DLQ), downstream nodes remain in state `BLOCKED`, and the workflow status transitions to `FAILED`. This prevents executing broken pipelines.

---

## 4. Intelligent Retries & AI-Assisted SRE

### The Decision:
Failed jobs undergo AI analysis to classify failures as **transient** (eligible for exponential/linear retries) or **permanent** (routed directly to DLQ).

### The Rationale:
1. **API Cost Mitigation**: Calling Gemini for thousands of successful operations is unnecessary. The AI service is invoked *only on execution failure*.
2. **Rule-Based Fallback Reliability**: If the Gemini API key is missing or the external API call fails (e.g., due to connection limits or timeouts), a local regex-based analyzer executes. It classifies typical application exceptions (validation, database lockups, and HTTP timeouts) into transient or permanent types, ensuring system reliability.
3. **DLQ Routing**: Permanent failures (e.g. invalid syntax or validation arguments) are directed immediately to the DLQ. This prevents workers from wasting cycles retrying tasks that can never succeed without code modifications.
