
import requests
import json
import os


AUTH_URL = "http://4.224.186.213/evaluation-service/auth"
LOG_URL = "http://4.224.186.213/evaluation-service/logs"

def get_auth_token():
    """Fetches a new authorization token."""
    payload = {
        "email": os.environ.get("EMAIL"),
        "name": os.environ.get("NAME"),
        "rollNo": os.environ.get("ROLL_NO"),
        "accessCode": os.environ.get("ACCESS_CODE"),
        "clientID": os.environ.get("CLIENT_ID"),
        "clientSecret": os.environ.get("CLIENT_SECRET")
    }
    try:
        response = requests.post(AUTH_URL, json=payload)
        if response.status_code in [200, 201]:
            return response.json().get("access_token")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching auth token: {e}")
        return None

AUTH_TOKEN = None

def Log(stack: str, level: str, package: str, message: str):
    """Sends a log message to the evaluation service.

    Args:
        stack (str): The stack (e.g., 'backend', 'frontend').
        level (str): The log level (e.g., 'debug', 'info', 'warn', 'error', 'fatal').
        package (str): The package/module (e.g., 'controller', 'service', 'middleware').
        message (str): The log message.
    """
    global AUTH_TOKEN

    if not AUTH_TOKEN:
        AUTH_TOKEN = get_auth_token()
        if not AUTH_TOKEN:
            print("Failed to get auth token, cannot log.")
            return

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }

    try:
        response = requests.post(LOG_URL, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            return
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending log: {e}")
        if hasattr(response, 'status_code') and response.status_code in [401, 403]:
            print("Auth token might be expired or invalid. Attempting to refresh...")
            AUTH_TOKEN = get_auth_token()
            if AUTH_TOKEN:
                headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
                try:
                    response = requests.post(LOG_URL, headers=headers, json=payload)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e_retry:
                    print(f"Error sending log after refresh: {e_retry}")
            else:
                print("Failed to refresh token, cannot log.")


if __name__ == "__main__":

    pass
