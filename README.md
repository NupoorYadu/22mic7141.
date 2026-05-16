# Backend Engineering Solutions

## Overview

This repository contains backend solutions for two core engineering challenges:

1. **Vehicle Maintenance Scheduler** — An optimization engine that allocates maintenance tasks across multiple depots using the 0/1 Knapsack algorithm to maximize total task importance within constrained mechanic-hours.

2. **Campus Notifications Microservice** — A system design and implementation for a real-time campus notification platform, including a Priority Inbox that surfaces the most critical notifications using weighted scoring and time-decay.

---

## Project Structure

```
├── logging_middleware/              # Custom logging middleware (shared)
│   ├── __init__.py
│   └── logger.py                   # Structured log dispatch to remote API
├── vehicle_maintence_scheduler/     # Task 1: Optimization Engine
│   └── scheduler.py                # 0/1 Knapsack (Dynamic Programming)
├── notification_app_be/             # Task 2: Notification Backend
│   └── priority_inbox.py           # Priority Inbox (Min-Heap + Weighted Scoring)
├── notification_system_design.md    # System Design Document (Stages 1-6)
├── .gitignore
└── README.md
```

---

## Prerequisites

- Python 3.11+
- `requests` library

```bash
pip install requests
```

---

## Configuration

Both scripts require authentication credentials. Update the following values at the top of each script (`scheduler.py` and `priority_inbox.py`):

```python
os.environ.setdefault("CLIENT_ID", "your_client_id")
os.environ.setdefault("CLIENT_SECRET", "your_client_secret")
os.environ.setdefault("EMAIL", "your_email")
os.environ.setdefault("NAME", "your_name")
os.environ.setdefault("ROLL_NO", "your_roll_no")
os.environ.setdefault("ACCESS_CODE", "your_access_code")
```

---

## Running the Solutions

### Task 1: Vehicle Maintenance Scheduler

```bash
python vehicle_maintence_scheduler/scheduler.py
```

**What it does:**
- Authenticates with the evaluation API
- Fetches depot data (ID, available mechanic-hours)
- Fetches vehicle task data (TaskID, Duration, Impact)
- Solves the 0/1 Knapsack problem for each depot independently
- Outputs optimal task selection per depot in JSON format

**Algorithm:** Dynamic Programming (0/1 Knapsack)
- Time Complexity: O(n * W) per depot, where n = tasks, W = capacity
- Space Complexity: O(n * W)

---

### Task 2: Priority Inbox (Stage 6)

```bash
python notification_app_be/priority_inbox.py
```

**What it does:**
- Authenticates with the evaluation API
- Fetches campus notifications (Placements, Results, Events)
- Calculates priority score for each notification using:
  - `priority = type_weight + recency_score`
  - Type Weights: Placement=3, Result=2, Event=1
  - Recency: `1 / (1 + hours_since / 24)` — range [0.0, 1.0]
- Uses a Min-Heap to efficiently extract Top-N notifications in O(N log n)
- Outputs the top 10 highest-priority notifications in JSON format

---

### System Design Document (Stages 1-5)

The file `notification_system_design.md` contains the full system design covering:

| Stage | Topic |
|-------|-------|
| 1 | REST API Design — Endpoints, request/response contracts, pagination |
| 2 | Database Schema — Tables, indexes, relationships |
| 3 | Query Optimization — Identifying and resolving slow queries |
| 4 | Performance — Caching strategy, SSE for real-time delivery |
| 5 | Reliability — Fault tolerance, retry logic, dead-letter queues |
| 6 | Priority Inbox — Algorithm design and implementation details |

---

## Logging Middleware

All modules use a custom logging middleware (`logging_middleware/logger.py`) that:

- Authenticates independently with the evaluation service
- Sends structured log entries via POST to the remote logging API
- Supports log levels: `debug`, `info`, `warn`, `error`, `fatal`
- Accepts parameters: `stack`, `level`, `package`, `message` (max 48 chars)
- Handles token refresh and error recovery gracefully

No `console.log` or `print` statements are used for logging — all operational logs go through this middleware.

---

## Output Format

Both solutions output structured JSON for programmatic consumption and evaluation:

**Task 1 Sample:**
```json
{
  "vehicle_maintenance_schedule": {
    "algorithm": "0/1 Knapsack (Dynamic Programming)",
    "depot_schedules": [...],
    "grand_total_importance": 713
  }
}
```

**Task 2 Sample:**
```json
{
  "priority_inbox": {
    "scoring_formula": "priority = type_weight + recency_score",
    "top_notifications": [...]
  }
}
```

---

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Python 3.11 | Fast development, clean syntax, strong stdlib |
| No external algorithm libraries | All algorithms implemented from scratch |
| Min-Heap for Top-N | O(N log n) vs O(N log N) for full sort |
| JSON output | Standard backend format, machine-readable |
| Environment variables for credentials | Security best practice, easy configuration |
| Modular structure | Each task is independently runnable |
