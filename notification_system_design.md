# Campus Notifications Microservice Design

## Stage 1: REST API Design

### Overview
The notification platform requires a robust REST API to handle real-time updates for students regarding Placements, Events, and Results. The API follows standard RESTful conventions, utilizing appropriate HTTP methods and status codes.

### Real-Time Notification Mechanism
For real-time notifications, **Server-Sent Events (SSE)** or **WebSockets** are recommended. Given that notifications are primarily a one-way communication channel (Server to Client), **SSE** is the most efficient and lightweight choice. It operates over standard HTTP, handles reconnections automatically, and is less resource-intensive than WebSockets.

### API Endpoints

#### 1. Fetch User Notifications
Retrieves a paginated list of notifications for the logged-in user.

**Endpoint:** `GET /api/v1/notifications`

**Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "Accept": "application/json"
}
```

**Query Parameters:**
- `page` (integer, default: 1)
- `limit` (integer, default: 20)
- `unreadOnly` (boolean, default: false)

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "notifications": [
      {
        "id": "d146095a-0d86-4a34-9e69-3900a14576bc",
        "type": "Result",
        "message": "mid-sem results published",
        "isRead": false,
        "createdAt": "2026-04-22T17:51:30Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalItems": 100
    }
  }
}
```

#### 2. Mark Notification as Read
Updates the status of a specific notification to read.

**Endpoint:** `PATCH /api/v1/notifications/{notificationId}/read`

**Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body:** (Empty, as the action is implied by the endpoint)

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Notification marked as read"
}
```

#### 3. Mark All Notifications as Read
Updates all unread notifications for the user to read.

**Endpoint:** `POST /api/v1/notifications/read-all`

**Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "All notifications marked as read"
}
```

#### 4. Real-Time Notification Stream (SSE)
Establishes a persistent connection to receive real-time updates.

**Endpoint:** `GET /api/v1/notifications/stream`

**Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "Accept": "text/event-stream"
}
```

**Response (200 OK - Stream):**
```text
data: {"id": "...", "type": "Placement", "message": "New drive announced", "createdAt": "..."}\n\n
```

---

## Stage 2: Database Design

### Persistent Storage Choice
I recommend **PostgreSQL** (a relational database) for this microservice. 

**Explanation:**
1. **Structured Data:** Notifications have a clear, predictable schema (ID, UserID, Type, Message, Status, Timestamp).
2. **ACID Compliance:** Ensures data integrity, especially when updating read statuses concurrently.
3. **Indexing:** PostgreSQL provides powerful indexing capabilities (B-Tree, Partial Indexes) which are crucial for fast retrieval of unread notifications ordered by time.
4. **JSONB Support:** If we need to store dynamic metadata associated with specific notification types in the future, PostgreSQL's JSONB column handles this efficiently.

### Database Schema

```sql
CREATE TYPE notification_type AS ENUM ('Placement', 'Event', 'Result');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

### Handling Data Volume Increases
As data volume grows (e.g., millions of notifications), the `notifications` table will become a bottleneck.

**Problems:**
- Slower read/write operations.
- Increased storage costs.
- Index bloat.

**Solutions:**
1. **Table Partitioning:** Partition the `notifications` table by date (e.g., monthly partitions). This keeps active indexes small and makes archiving old data trivial.
2. **Data Archival/Purging:** Move notifications older than 6 months to cold storage (e.g., AWS S3 or a cheaper NoSQL store like DynamoDB) or delete them if no longer needed.
3. **Read Replicas:** Route read-heavy operations (fetching notifications) to read replicas, reserving the primary database for writes.

### Queries based on REST APIs

**Fetch User Notifications (Paginated):**
```sql
SELECT id, type, message, is_read, created_at 
FROM notifications 
WHERE user_id = $1 
ORDER BY created_at DESC 
LIMIT $2 OFFSET $3;
```

**Mark Notification as Read:**
```sql
UPDATE notifications 
SET is_read = TRUE 
WHERE id = $1 AND user_id = $2;
```

---

## Stage 3: Query Optimization

### Analysis of the Slow Query
**Original Query:**
```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC;
```

**Is it accurate?** Yes, it accurately retrieves unread notifications for a specific student.
**Why is it slow?** With 5,000,000 notifications, if there is no index covering `studentID`, `isRead`, and `createdAt`, the database must perform a **Full Table Scan**. It checks every row to see if it matches the conditions, and then sorts the massive result set in memory.
**Computation Cost:** O(N) where N is the total number of rows in the table, plus O(M log M) for sorting where M is the number of matched rows.

### Proposed Changes
1. **Avoid `SELECT *`:** Only select the necessary columns to reduce memory and network overhead.
2. **Add a Partial Composite Index:** Create an index specifically tailored for this query.

```sql
CREATE INDEX idx_unread_notifications ON notifications (studentID, createdAt DESC) WHERE isRead = false;
```

### Evaluating the Teammate's Advice
**Advice:** "Add indexes on every column to be safe."
**Is it effective?** **NO.** This is a terrible practice.
**Why not?**
- **Write Penalty:** Every `INSERT`, `UPDATE`, or `DELETE` operation requires updating all those indexes, severely degrading write performance.
- **Storage Cost:** Indexes consume significant disk space. Indexing every column will bloat the database size unnecessarily.
- **Optimizer Confusion:** The query planner might get confused by too many overlapping indexes and choose a suboptimal execution plan.

### Query: Placement Notifications in Last 7 Days
```sql
SELECT DISTINCT u.student_id, u.name, u.email
FROM users u
JOIN notifications n ON u.id = n.user_id
WHERE n.notification_type = 'Placement'
  AND n.created_at >= CURRENT_DATE - INTERVAL '7 days';
```

---

## Stage 4: Performance Optimization

### The Problem
Fetching notifications from the DB on every page load for 50,000 students overwhelms the database, leading to high latency and poor UX.

### Proposed Solutions and Tradeoffs

#### 1. Implement a Caching Layer (Redis)
Store the unread notification count and the top N recent notifications for each user in an in-memory cache like Redis.
- **How it works:** On page load, the application queries Redis. If the data is present (Cache Hit), it returns immediately. If not (Cache Miss), it queries the DB, updates Redis, and returns the data. When a new notification is created, the cache is invalidated or updated.
- **Tradeoffs:**
  - *Pros:* Drastically reduces DB load; extremely fast read times (sub-millisecond).
  - *Cons:* Introduces system complexity; requires cache invalidation logic (cache staleness risk); additional infrastructure cost.

#### 2. Server-Sent Events (SSE) / WebSockets (Push instead of Pull)
Instead of the client polling (fetching) on every page load, maintain a persistent connection and push notifications to the client only when they occur.
- **How it works:** The client connects once. The server pushes updates. The client stores them locally (e.g., in Redux or LocalStorage) and persists them across page navigations within the SPA (Single Page Application).
- **Tradeoffs:**
  - *Pros:* Eliminates redundant API calls on page loads; provides true real-time experience.
  - *Cons:* Requires maintaining thousands of concurrent open connections; complex to scale across multiple server instances (requires a pub/sub broker like Redis Pub/Sub).

#### 3. Optimistic UI Updates & Local Storage
Cache the notifications in the browser's `localStorage` or `sessionStorage`.
- **How it works:** On initial load, fetch from the server and save to local storage. On subsequent page loads, render immediately from local storage while silently fetching updates in the background (stale-while-revalidate pattern).
- **Tradeoffs:**
  - *Pros:* Zero perceived latency for the user; very easy to implement on the frontend.
  - *Cons:* Data might be briefly stale; doesn't solve the backend load issue entirely, just hides the latency from the user.

**Recommendation:** A combination of **Redis Caching** (for fast initial loads) and **SSE** (for real-time updates without polling) is the industry standard for this scenario.

---

## Stage 5: Reliability & Fault Tolerance

### Shortcomings of the Proposed Implementation
```python
function notify_all(student_ids: array, message: string):
    for student_id in student_ids:
        send_email(student_id, message)  # calls Email API
        save_to_db(student_id, message)  # DB insert
        push_to_app(student_id, message) # real-time notification
```

1. **Synchronous and Blocking:** The loop processes one student at a time. If `send_email` takes 1 second, notifying 50,000 students takes ~14 hours.
2. **No Fault Tolerance:** If it fails at student 200, the loop crashes. Students 201-50,000 get nothing.
3. **No Retry Mechanism:** Transient network errors with the Email API will cause permanent failures for those specific students.
4. **Tight Coupling:** DB insertion and email sending are coupled. If the email API is down, the notification isn't even saved to the DB.

### Handling the Failure (Failed at 200 midway)
**What now?** We have a partial failure state. We don't know exactly which 200 failed unless we parse logs manually. We cannot simply rerun the function, or the successful ones will receive duplicate emails.

### Redesign for Reliability and Speed
We must decouple the processes using an **Asynchronous Message Queue** (e.g., RabbitMQ, Kafka, or AWS SQS) and a **Worker Pool**.

**Should saving to DB and sending email happen together?**
**NO.** Saving to the DB is a fast, internal operation. Sending an email relies on an external API, which is slow and prone to failure. They must be separated. The DB should act as the source of truth.

### Revised Pseudocode

```python
# 1. Main API Handler (Fast, synchronous)
function notify_all_handler(student_ids: array, message: string):
    # Bulk insert into DB first (Source of Truth)
    # Status defaults to 'pending_email'
    notification_ids = bulk_save_to_db(student_ids, message) 
    
    # Push jobs to a Message Queue for asynchronous processing
    for id, student_id in zip(notification_ids, student_ids):
        queue.push("email_queue", { "notification_id": id, "student_id": student_id, "message": message })
        queue.push("realtime_queue", { "student_id": student_id, "message": message })
        
    return "Notifications queued successfully"

# 2. Email Worker (Runs asynchronously, multiple instances in parallel)
function process_email_job(job):
    try:
        send_email(job.student_id, job.message)
        update_db_status(job.notification_id, 'email_sent')
    except TransientError:
        # Put back in queue with exponential backoff
        queue.retry(job, delay=exponential_backoff)
    except PermanentError:
        update_db_status(job.notification_id, 'email_failed')
        log_error("Email failed permanently", job)

# 3. Real-time Worker (Runs asynchronously)
function process_realtime_job(job):
    push_to_app(job.student_id, job.message) # e.g., via Redis Pub/Sub to SSE servers
```

**Why this is better:**
- **Fast:** The API responds immediately after queuing.
- **Reliable:** If an email fails, the worker retries it without affecting others.
- **Scalable:** We can spin up 100 email workers to process the queue in minutes instead of hours.
- **Resilient:** If the worker crashes, the message remains in the queue and is picked up by another worker.
