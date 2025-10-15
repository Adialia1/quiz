#!/usr/bin/env python3
"""
Quick script to send a test notification to all users now
"""
import requests
import sys

API_URL = "https://accepted-awfully-bug.ngrok-free.app"
API_KEY = "a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b"

def send_test_notification():
    """Send a test notification to all users"""
    try:
        print("📤 Sending test notification...")

        response = requests.post(
            f"{API_URL}/api/notifications/send",
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "title": "בדיקה 🧪",
                "body": "זו הודעת בדיקה מהמערכת",
                "data": {
                    "type": "test",
                    "timestamp": "now"
                }
            },
            timeout=30
        )

        if response.ok:
            result = response.json()
            print(f"\n✅ Success!")
            print(f"   Total users: {result['total_users']}")
            print(f"   Sent: {result['sent']}")
            print(f"   Failed: {result['failed']}")
            if result['errors']:
                print(f"\n⚠️  Errors:")
                for error in result['errors']:
                    print(f"   - {error}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

def send_study_reminders():
    """Send study reminders to users whose hour matches now"""
    try:
        print("📚 Sending study reminders for current hour...")

        response = requests.post(
            f"{API_URL}/api/notifications/send-study-reminders",
            headers={"X-API-Key": API_KEY},
            timeout=30
        )

        if response.ok:
            result = response.json()
            print(f"\n✅ Success!")
            print(f"   Current hour: {result['current_hour']}")
            print(f"   Eligible users: {result['total_eligible_users']}")
            print(f"   Sent: {result['sent']}")
            print(f"   Failed: {result['failed']}")
            if result.get('errors'):
                print(f"\n⚠️  Errors:")
                for error in result['errors'][:5]:
                    print(f"   - {error}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("\n🔔 Notification Sender\n")
    print("Choose option:")
    print("1. Send test notification to all users")
    print("2. Send study reminders (current hour)")
    print()

    choice = input("Enter 1 or 2 (or just press Enter for option 1): ").strip() or "1"
    print()

    if choice == "1":
        send_test_notification()
    elif choice == "2":
        send_study_reminders()
    else:
        print("Invalid choice")
        sys.exit(1)
