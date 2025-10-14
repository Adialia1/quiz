"""
Notification API Routes

Handles sending push notifications to users
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client, Client
import requests

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Router
router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# Expo Push API endpoint
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

# Simple API key for protection (set in environment)
NOTIFICATION_API_KEY = os.getenv("NOTIFICATION_API_KEY", "your-secret-key-here")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class NotificationRequest(BaseModel):
    """Request to send notifications"""
    title: str
    body: str
    data: Optional[dict] = None
    user_ids: Optional[List[str]] = None  # If None, send to all users


class NotificationResponse(BaseModel):
    """Response from sending notifications"""
    status: str
    total_users: int
    sent: int
    failed: int
    errors: List[str] = []


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_push_notification(push_token: str, title: str, body: str, data: dict = None) -> dict:
    """
    Send a push notification via Expo Push API

    Args:
        push_token: Expo push token
        title: Notification title
        body: Notification body
        data: Additional data payload

    Returns:
        Response from Expo API
    """
    message = {
        "to": push_token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data or {},
        "priority": "high",
        "channelId": "study-reminders",
    }

    try:
        response = requests.post(
            EXPO_PUSH_URL,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=message,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending notification: {e}")
        return {"error": str(e)}


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/send", response_model=NotificationResponse)
async def send_notifications(
    request: NotificationRequest,
    x_api_key: str = Header(None, description="API key for authentication")
):
    """
    Send push notifications to users

    Requires: X-API-Key header for authentication

    Query parameters:
    - title: Notification title
    - body: Notification body
    - data: Optional JSON data
    - user_ids: Optional list of user IDs (if not provided, sends to all)

    Example:
    ```bash
    curl -X POST "http://localhost:8000/api/notifications/send" \\
         -H "X-API-Key: your-secret-key-here" \\
         -H "Content-Type: application/json" \\
         -d '{
           "title": "זמן ללמוד! 📚",
           "body": "הגיע הזמן להתכונן למבחן שלך"
         }'
    ```
    """
    # Verify API key
    if x_api_key != NOTIFICATION_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # Build query
        query = supabase.table("users")\
            .select("id, clerk_user_id, expo_push_token, notification_preferences, study_hours")\
            .eq("onboarding_completed", True)\
            .not_.is_("expo_push_token", "null")

        # Filter by user IDs if provided
        if request.user_ids:
            query = query.in_("id", request.user_ids)

        result = query.execute()
        users = result.data or []

        if not users:
            return NotificationResponse(
                status="success",
                total_users=0,
                sent=0,
                failed=0,
                errors=["No users with push tokens found"]
            )

        # Get current hour in Israel timezone
        israel_tz = ZoneInfo("Asia/Jerusalem")
        current_time = datetime.now(israel_tz)
        current_hour = current_time.hour

        sent_count = 0
        failed_count = 0
        errors = []

        for user in users:
            push_token = user.get("expo_push_token")
            notification_prefs = user.get("notification_preferences", {})
            study_hours = user.get("study_hours", [])

            # Parse JSON strings if needed
            if isinstance(notification_prefs, str):
                try:
                    notification_prefs = json.loads(notification_prefs)
                except:
                    notification_prefs = {}

            if isinstance(study_hours, str):
                try:
                    study_hours = json.loads(study_hours)
                except:
                    study_hours = []

            # Check if study reminders are enabled (only for scheduled reminders)
            # For custom notifications via /send endpoint, we ignore this check
            # This allows sending notifications at any time

            # Send notification
            response = send_push_notification(
                push_token=push_token,
                title=request.title,
                body=request.body,
                data=request.data or {"type": "scheduled_reminder"}
            )

            # Check if notification was sent successfully
            if response and not response.get("error"):
                # Expo returns {"data": [{"status": "ok", "id": "..."}]}
                if "data" in response and isinstance(response["data"], list) and len(response["data"]) > 0:
                    ticket = response["data"][0]
                    if ticket.get("status") == "ok":
                        sent_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"User {user['clerk_user_id'][:12]}: {ticket.get('message', 'Unknown error')}")
                else:
                    # If no "data" field or not a list, assume success (Expo sometimes returns just the ticket)
                    sent_count += 1
            else:
                failed_count += 1
                if response:
                    errors.append(f"User {user['clerk_user_id'][:12]}: {response.get('error', 'Failed to send')}")
                else:
                    errors.append(f"User {user['clerk_user_id'][:12]}: No response from Expo")

        return NotificationResponse(
            status="success",
            total_users=len(users),
            sent=sent_count,
            failed=failed_count,
            errors=errors[:10]  # Limit to first 10 errors
        )

    except Exception as e:
        import traceback
        print(f"❌ Error sending notifications: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error sending notifications: {str(e)}")


@router.post("/send-study-reminders")
async def send_study_reminders(
    x_api_key: str = Header(None, description="API key for authentication")
):
    """
    Send study reminders to all users whose study hour matches current time

    This endpoint should be called every hour by a scheduler

    Requires: X-API-Key header for authentication

    Example:
    ```bash
    curl -X POST "http://localhost:8000/api/notifications/send-study-reminders" \\
         -H "X-API-Key: your-secret-key-here"
    ```
    """
    # Verify API key
    if x_api_key != NOTIFICATION_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # Get current hour in Israel timezone
        israel_tz = ZoneInfo("Asia/Jerusalem")
        current_time = datetime.now(israel_tz)
        current_hour = current_time.hour

        # Get all users with onboarding completed and push tokens
        result = supabase.table("users")\
            .select("id, clerk_user_id, expo_push_token, notification_preferences, study_hours")\
            .eq("onboarding_completed", True)\
            .not_.is_("expo_push_token", "null")\
            .execute()

        users = result.data or []

        if not users:
            return {
                "status": "success",
                "message": "No users with push tokens found",
                "current_hour": current_hour,
                "sent": 0
            }

        sent_count = 0
        failed_count = 0
        errors = []

        for user in users:
            push_token = user.get("expo_push_token")
            notification_prefs = user.get("notification_preferences", {})
            study_hours = user.get("study_hours", [])

            # Parse JSON strings if needed
            if isinstance(notification_prefs, str):
                try:
                    notification_prefs = json.loads(notification_prefs)
                except:
                    notification_prefs = {}

            if isinstance(study_hours, str):
                try:
                    study_hours = json.loads(study_hours)
                except:
                    study_hours = []

            # Check if study reminders are enabled
            if not notification_prefs.get("study_reminders_enabled", True):
                continue

            # Check if current hour matches user's study hours
            if current_hour not in study_hours:
                continue

            # Send notification
            response = send_push_notification(
                push_token=push_token,
                title="זמן ללמוד! 📚",
                body="הגיע הזמן להתכונן למבחן שלך",
                data={"type": "study_reminder", "hour": current_hour}
            )

            # Check if notification was sent successfully
            if response and not response.get("error"):
                # Expo returns {"data": [{"status": "ok", "id": "..."}]}
                if "data" in response and isinstance(response["data"], list) and len(response["data"]) > 0:
                    ticket = response["data"][0]
                    if ticket.get("status") == "ok":
                        sent_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"User {user['clerk_user_id'][:12]}: {ticket.get('message')}")
                else:
                    # If no "data" field or not a list, assume success
                    sent_count += 1
            else:
                failed_count += 1
                if response:
                    errors.append(f"User {user['clerk_user_id'][:12]}: {response.get('error', 'Failed to send')}")
                else:
                    errors.append(f"User {user['clerk_user_id'][:12]}: No response from Expo")

        return {
            "status": "success",
            "message": f"Sent study reminders for hour {current_hour}",
            "current_hour": current_hour,
            "total_eligible_users": sent_count + failed_count,
            "sent": sent_count,
            "failed": failed_count,
            "errors": errors[:5]  # Limit to first 5 errors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending study reminders: {str(e)}")
