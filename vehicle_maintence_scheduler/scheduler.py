"""
Task 1: Vehicle Maintenance Scheduler
======================================
This module solves the Vehicle Maintenance Scheduling problem using the
0/1 Knapsack Algorithm.

Problem:
    - Each depot has limited mechanic-hours (capacity).
    - Each vehicle task has a Duration (weight) and Importance/Impact (value).
    - Goal: Select the combination of tasks that maximizes total importance
      without exceeding the available mechanic-hours for each depot.

Algorithm: 0/1 Knapsack (Dynamic Programming)
    - Time Complexity: O(n * W) where n = number of tasks, W = capacity
    - Space Complexity: O(n * W)

Data Sources:
    - Depots API: GET http://4.224.186.213/evaluation-service/depots
    - Vehicles API: GET http://4.224.186.213/evaluation-service/vehicles
"""

import os
import sys
import json
import requests

os.environ.setdefault("CLIENT_ID", "680332e6-3a09-4d72-806e-7d505b12d2a8")
os.environ.setdefault("CLIENT_SECRET", "dZYRjtrcaYWvdNnz")
os.environ.setdefault("EMAIL", "nupooryaduvanshi@gmail.com")
os.environ.setdefault("NAME", "nupoor kumari")
os.environ.setdefault("ROLL_NO", "22mic7141")
os.environ.setdefault("ACCESS_CODE", "SfFuWg")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_middleware.logger import Log


BASE_URL = "http://4.224.186.213/evaluation-service"
AUTH_URL = f"{BASE_URL}/auth"
DEPOTS_URL = f"{BASE_URL}/depots"
VEHICLES_URL = f"{BASE_URL}/vehicles"



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



def fetch_depots(token: str) -> list:
    """Fetches all depots from the evaluation service API."""
    headers = {"Authorization": f"Bearer {token}"}

    Log("backend", "info", "service", "Fetching depots from API")

    try:
        response = requests.get(DEPOTS_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        depots = data.get("depots", [])
        Log("backend", "info", "service", f"Fetched {len(depots)} depots")
        return depots
    except requests.exceptions.RequestException as e:
        Log("backend", "error", "service", "Failed to fetch depots")
        raise


def fetch_vehicles(token: str) -> list:
    """Fetches all vehicle tasks from the evaluation service API."""
    headers = {"Authorization": f"Bearer {token}"}

    Log("backend", "info", "service", "Fetching vehicles from API")

    try:
        response = requests.get(VEHICLES_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        vehicles = data.get("vehicles", [])
        Log("backend", "info", "service", f"Fetched {len(vehicles)} vehicles")
        return vehicles
    except requests.exceptions.RequestException as e:
        Log("backend", "error", "service", "Failed to fetch vehicles")
        raise



def knapsack_01(capacity: int, tasks: list) -> dict:
    """
    Solves the 0/1 Knapsack problem using Dynamic Programming.

    Args:
        capacity (int): Maximum mechanic-hours available (knapsack capacity).
        tasks (list): List of task dicts with 'TaskID', 'Duration', 'Impact'.

    Returns:
        dict: {
            'max_importance': int,
            'selected_tasks': list of selected task dicts,
            'total_duration': int
        }
    """
    n = len(tasks)

    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        duration = tasks[i - 1]["Duration"]
        impact = tasks[i - 1]["Impact"]

        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]

            if duration <= w:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - duration] + impact)

    selected_tasks = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected_tasks.append(tasks[i - 1])
            w -= tasks[i - 1]["Duration"]

    selected_tasks.reverse()

    total_duration = sum(t["Duration"] for t in selected_tasks)
    max_importance = dp[n][capacity]

    return {
        "max_importance": max_importance,
        "selected_tasks": selected_tasks,
        "total_duration": total_duration
    }



def main():
    """Main function to run the Vehicle Maintenance Scheduler."""
    Log("backend", "info", "controller", "Starting Vehicle Scheduler")

    token = get_auth_token()

    depots = fetch_depots(token)
    vehicles = fetch_vehicles(token)

    if not depots:
        Log("backend", "warn", "controller", "No depots found")
        print(json.dumps({"error": "No depots available"}))
        return

    if not vehicles:
        Log("backend", "warn", "controller", "No vehicles found")
        print(json.dumps({"error": "No vehicle tasks available"}))
        return

    output = {
        "vehicle_maintenance_schedule": {
            "algorithm": "0/1 Knapsack (Dynamic Programming)",
            "time_complexity": "O(n * W)",
            "total_depots": len(depots),
            "total_vehicle_tasks": len(vehicles),
            "depot_schedules": [],
            "grand_total_importance": 0
        }
    }

    total_importance = 0

    for depot in depots:
        depot_id = depot["ID"]
        capacity = depot["MechanicHours"]

        Log("backend", "info", "service",
            f"Solving knapsack for depot {depot_id}")

        result = knapsack_01(capacity, vehicles)
        total_importance += result["max_importance"]

        depot_result = {
            "depot_id": depot_id,
            "capacity_hours": capacity,
            "used_hours": result["total_duration"],
            "max_importance": result["max_importance"],
            "tasks_selected": len(result["selected_tasks"]),
            "selected_tasks": [
                {
                    "TaskID": task["TaskID"],
                    "Duration": task["Duration"],
                    "Impact": task["Impact"]
                }
                for task in result["selected_tasks"]
            ]
        }

        output["vehicle_maintenance_schedule"]["depot_schedules"].append(depot_result)

        Log("backend", "info", "service",
            f"Depot {depot_id}: score={result['max_importance']}")

    output["vehicle_maintenance_schedule"]["grand_total_importance"] = total_importance

    print(json.dumps(output, indent=2))

    Log("backend", "info", "controller", "Vehicle Scheduler completed")


if __name__ == "__main__":
    main()
