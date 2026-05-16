# Campus Hiring Evaluation - Backend

## Project Structure

```
22mic7179/
├── logging_middleware/              # Custom logging middleware package
│   ├── __init__.py
│   └── logger.py
├── vehicle_maintence_scheduler/     # Task 1: Vehicle Maintenance Scheduler
│   └── scheduler.py               # 0/1 Knapsack Algorithm Implementation
├── notification_app_be/             # Task 2: Campus Notifications Backend
│   └── priority_inbox.py          # Stage 6: Priority Inbox Implementation
├── notification_system_design.md    # Task 2: Stages 1-6 Design Document
├── .gitignore
└── README.md
```

## Setup

### Prerequisites
- Python 3.11+
- `requests` library (`pip install requests`)

### Environment Variables
Set the following environment variables before running:
```bash
export CLIENT_ID="your_client_id"
export CLIENT_SECRET="your_client_secret"
export EMAIL="your_email"
export NAME="your_name"
export ROLL_NO="your_roll_no"
export ACCESS_CODE="your_access_code"
```

## Running

### Task 1: Vehicle Maintenance Scheduler
```bash
python vehicle_maintence_scheduler/scheduler.py
```

### Task 2: Priority Inbox (Stage 6)
```bash
python notification_app_be/priority_inbox.py
```

## Logging Middleware
All modules use the custom logging middleware located in `logging_middleware/logger.py`. It sends structured logs to the evaluation service API with the following parameters:
- `stack`: The application stack (e.g., 'backend')
- `level`: Log level (debug, info, warn, error, fatal)
- `package`: Module/package name (e.g., 'controller', 'service')
- `message`: Log message (max 48 characters)
