"""
Send test study reminder notifications to all users

This script sends an immediate test notification to all users who have:
- Completed onboarding
- Provided an Expo push token
- Have study reminders enabled
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client
import requests

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Expo Push API endpoint
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_push_notification(push_token: str, title: str, body: str, data: dict = None):
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
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending notification: {e}")
        return None


def main():
    """Send test notifications to all eligible users"""

    print("🔍 Fetching users from database...")

    # Get all users with push tokens and onboarding completed
    result = supabase.table("users")\
        .select("id, clerk_user_id, expo_push_token, notification_preferences, exam_date")\
        .eq("onboarding_completed", True)\
        .not_.is_("expo_push_token", "null")\
        .execute()

    users = result.data or []

    if not users:
        print("❌ No users with push tokens found")
        return

    print(f"✅ Found {len(users)} users with push tokens")

    sent_count = 0
    failed_count = 0

    for user in users:
        push_token = user.get("expo_push_token")
        notification_prefs = user.get("notification_preferences", {})

        # Parse JSON if it's a string
        if isinstance(notification_prefs, str):
            try:
                notification_prefs = json.loads(notification_prefs)
            except:
                notification_prefs = {}

        # Check if study reminders are enabled
        if not notification_prefs.get("study_reminders_enabled", True):
            print(f"⏭️  Skipping user {user['clerk_user_id'][:12]}... (reminders disabled)")
            continue

        print(f"📤 Sending to {user['clerk_user_id'][:12]}...")

        # Send test notification
        response = send_push_notification(
            push_token=push_token,
            title="זמן ללמוד! 📚",
            body="זו הודעת בדיקה - התזכורות שלך פועלות!",
            data={
                "type": "test_study_reminder",
                "user_id": user["id"],
            }
        )

        if response and response.get("data"):
            ticket = response["data"][0]
            if ticket.get("status") == "ok":
                print(f"   ✅ Sent successfully")
                sent_count += 1
            else:
                print(f"   ❌ Failed: {ticket.get('message', 'Unknown error')}")
                failed_count += 1
        else:
            print(f"   ❌ Failed to send")
            failed_count += 1

    print("\n" + "="*50)
    print(f"📊 Summary:")
    print(f"   Total users: {len(users)}")
    print(f"   ✅ Sent: {sent_count}")
    print(f"   ❌ Failed: {failed_count}")
    print("="*50)


if __name__ == "__main__":
    main()
