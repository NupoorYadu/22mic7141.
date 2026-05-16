"""
Stage 6: Priority Inbox Implementation
=======================================
This module implements a Priority Inbox that displays the top 'n' most important
unread notifications based on a combination of type weight and recency.

Priority Scoring:
    - Placement: weight = 3 (highest)
    - Result:    weight = 2
    - Event:     weight = 1 (lowest)
    - Recency:   More recent notifications get a higher recency score.

The final priority score = type_weight + recency_score

Data Source: Notification API (GET http://4.224.186.213/evaluation-service/notifications)
"""

import os
import sys
import json
import requests
import heapq
from datetime import datetime

# Set environment variables before importing logging middleware
os.environ.setdefault("CLIENT_ID", "d3caf95c-01be-478b-aaa4-58ddef5cd6b2")
os.environ.setdefault("CLIENT_SECRET", "bRheXPQCcKXKrFXr")
os.environ.setdefault("EMAIL", "your_college_email@college.edu")
os.environ.setdefault("NAME", "your full name")
os.environ.setdefault("ROLL_NO", "22mic7179")
os.environ.setdefault("ACCESS_CODE", "SfFuWg")

# Add parent directory to path for importing logging middleware
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_middleware.logger import Log

# ============================================================
# Configuration
# ============================================================

BASE_URL = "http://4.224.186.213/evaluation-service"
NOTIFICATIONS_URL = f"{BASE_URL}/notifications"
AUTH_URL = f"{BASE_URL}/auth"

# Type weights for priority calculation
TYPE_WEIGHTS = {
    "Placement": 3,
    "Result": 2,
    "Event": 1
}

# Number of top priority notifications to display
TOP_N = 10


# ============================================================
# Authentication
# ============================================================

def get_auth_token() -> str:
    """Fetches a Bearer token from the authentication endpoint."""
    payload = {
        "email": os.environ.get("EMAIL"),
        "name": os.environ.get("NAME"),
        "rollNo": os.environ.get("ROLL_NO"),
        "accessCode": os.environ.get("ACCESS_CODE"),
        "clientID": os.environ.get("CLIENT_ID"),
        "clientSecret": os.environ.get("CLIENT_SECRET")
    }

    Log("backend", "info", "auth", "Requesting auth token")

    try:
        response = requests.post(AUTH_URL, json=payload)
        response.raise_for_status()
        token = response.json().get("access_token")
        Log("backend", "info", "auth", "Auth token obtained")
        return token
    except requests.exceptions.RequestException as e:
        Log("backend", "error", "auth", "Failed to obtain auth token")
        raise


# ============================================================
# Data Fetching
# ============================================================

def fetch_notifications(token: str) -> list:
    """Fetches all notifications from the evaluation service API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    Log("backend", "info", "service", "Fetching notifications from API")

    try:
        response = requests.get(NOTIFICATIONS_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        notifications = data.get("notifications", [])
        Log("backend", "info", "service", f"Fetched {len(notifications)} notifs")
        return notifications
    except requests.exceptions.RequestException as e:
        Log("backend", "error", "service", "Failed to fetch notifications")
        raise


# ============================================================
# Priority Calculation
# ============================================================

def calculate_recency_score(timestamp_str: str, reference_time: datetime) -> float:
    """
    Calculates a recency score based on how recent the notification is.
    More recent notifications receive a higher score (0.0 to 1.0 range).

    Uses an inverse time-decay approach:
        recency_score = 1 / (1 + hours_since_notification / 24)
    """
    try:
        notification_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Try ISO format as fallback
        notification_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")).replace(tzinfo=None)

    time_diff = reference_time - notification_time
    hours_diff = max(time_diff.total_seconds() / 3600, 0)

    # Inverse decay: notifications from the last hour score ~1.0,
    # notifications from 24 hours ago score ~0.5
    recency_score = 1.0 / (1.0 + hours_diff / 24.0)
    return recency_score


def calculate_priority(notification: dict, reference_time: datetime) -> float:
    """
    Calculates the overall priority score for a notification.
    Priority = type_weight + recency_score
    """
    notification_type = notification.get("Type", "Event")
    timestamp = notification.get("Timestamp", "")

    type_weight = TYPE_WEIGHTS.get(notification_type, 0)
    recency_score = calculate_recency_score(timestamp, reference_time)

    return type_weight + recency_score


# ============================================================
# Priority Inbox (Top-N using Min-Heap)
# ============================================================

def get_top_n_priority_notifications(notifications: list, n: int = TOP_N) -> list:
    """
    Finds the top 'n' highest priority notifications using a Min-Heap.

    Algorithm:
        - Maintain a min-heap of size 'n'.
        - For each notification, calculate its priority score.
        - If the heap has fewer than 'n' items, push the notification.
        - If the current notification's priority is higher than the heap's minimum,
          replace the minimum with the current notification.
        - This runs in O(N log n) time, which is efficient for large datasets.

    Maintaining Top-N Efficiently with New Notifications:
        - When a new notification arrives, calculate its priority.
        - Compare it with the minimum element in the heap (heap[0]).
        - If it's higher, pop the minimum and push the new one. O(log n).
        - This avoids re-sorting the entire list every time.
    """
    Log("backend", "info", "service", f"Calculating top {n} priorities")

    reference_time = datetime.now()
    min_heap = []

    for notification in notifications:
        priority = calculate_priority(notification, reference_time)

        if len(min_heap) < n:
            heapq.heappush(min_heap, (priority, notification.get("ID", ""), notification))
        elif priority > min_heap[0][0]:
            heapq.heapreplace(min_heap, (priority, notification.get("ID", ""), notification))

    # Extract results sorted by priority (highest first)
    top_notifications = sorted(min_heap, key=lambda x: x[0], reverse=True)

    Log("backend", "info", "service", f"Top {n} priorities determined")

    return [(score, notif) for score, _, notif in top_notifications]


# ============================================================
# Display (JSON Output)
# ============================================================

def display_results(top_notifications: list):
    """Displays the top priority notifications in JSON format."""
    output = {
        "priority_inbox": {
            "total_notifications_processed": len(top_notifications),
            "scoring_formula": "priority = type_weight + recency_score",
            "type_weights": TYPE_WEIGHTS,
            "recency_formula": "1 / (1 + hours_since / 24)",
            "top_notifications": []
        }
    }

    for rank, (score, notification) in enumerate(top_notifications, 1):
        output["priority_inbox"]["top_notifications"].append({
            "rank": rank,
            "priority_score": round(score, 4),
            "type": notification.get("Type", "Unknown"),
            "message": notification.get("Message", "N/A"),
            "timestamp": notification.get("Timestamp", "N/A")
        })

    print(json.dumps(output, indent=2))


# ============================================================
# Main Entry Point
# ============================================================

def main():
    """Main function to run the Priority Inbox."""
    Log("backend", "info", "controller", "Starting Priority Inbox")

    # Step 1: Authenticate
    token = get_auth_token()

    # Step 2: Fetch notifications
    notifications = fetch_notifications(token)

    if not notifications:
        Log("backend", "warn", "controller", "No notifications found")
        print(json.dumps({"error": "No notifications available"}))
        return

    # Step 3: Calculate priorities and get top N
    top_notifications = get_top_n_priority_notifications(notifications, TOP_N)

    # Step 4: Display results in JSON format
    display_results(top_notifications)

    Log("backend", "info", "controller", "Priority Inbox completed")


if __name__ == "__main__":
    main()
