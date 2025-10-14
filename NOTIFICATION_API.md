# Notification API Documentation

This document describes how to use the notification API endpoints for sending scheduled push notifications to users.

## 🔑 Authentication

All notification endpoints require authentication via an API key passed in the `X-API-Key` header.

**API Key:** `a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b`

This key is stored in the `.env` file as `NOTIFICATION_API_KEY`.

## 📡 Endpoints

### 1. Send Study Reminders (Automated)

**Endpoint:** `POST /api/notifications/send-study-reminders`

**Purpose:** Sends study reminders to all users whose study hour matches the current hour. This endpoint should be called every hour by a scheduler service.

**Headers:**
```
X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b
```

**Example Request:**
```bash
curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send-study-reminders" \
  -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b"
```

**Response:**
```json
{
  "status": "success",
  "message": "Sent study reminders for hour 14",
  "current_hour": 14,
  "total_eligible_users": 5,
  "sent": 5,
  "failed": 0,
  "errors": []
}
```

**How it works:**
1. Gets the current hour (0-23)
2. Queries all users with:
   - `onboarding_completed = true`
   - `expo_push_token` is not null
   - `notification_preferences.study_reminders_enabled = true`
   - Current hour is in their `study_hours` array
3. Sends push notification: "זמן ללמוד! 📚" / "הגיע הזמן להתכונן למבחן שלך"

---

### 2. Send Custom Notifications

**Endpoint:** `POST /api/notifications/send`

**Purpose:** Send custom notifications to specific users or all users.

**Headers:**
```
X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "כותרת ההודעה",
  "body": "תוכן ההודעה",
  "data": {
    "type": "custom",
    "custom_field": "value"
  },
  "user_ids": ["user-id-1", "user-id-2"]  // Optional - if omitted, sends to all users
}
```

**Example Request:**
```bash
curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send" \
  -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "מבחן מתקרב! 📝",
    "body": "המבחן שלך בעוד שבוע - זמן להתכונן",
    "data": {
      "type": "exam_reminder",
      "days_until_exam": 7
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "total_users": 10,
  "sent": 9,
  "failed": 1,
  "errors": [
    "User user_xyz: Push token is invalid"
  ]
}
```

---

## 🕐 Setting Up a Scheduler

You need to set up a scheduler service to call the study reminders endpoint every hour.

### Option 1: Cron Job (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add this line to run every hour:
```bash
0 * * * * curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send-study-reminders" -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b" >> /var/log/study-reminders.log 2>&1
```

### Option 2: Vercel Cron

If your API is deployed on Vercel, add to `vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/notifications/send-study-reminders",
      "schedule": "0 * * * *"
    }
  ]
}
```

### Option 3: GitHub Actions

Create `.github/workflows/study-reminders.yml`:

```yaml
name: Send Study Reminders
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:  # Allow manual trigger

jobs:
  send-reminders:
    runs-on: ubuntu-latest
    steps:
      - name: Send Study Reminders
        run: |
          curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send-study-reminders" \
            -H "X-API-Key: ${{ secrets.NOTIFICATION_API_KEY }}"
```

### Option 4: Python Script with Schedule

Create `send_hourly_reminders.py`:

```python
import schedule
import time
import requests

API_URL = "https://accepted-awfully-bug.ngrok-free.app"
API_KEY = "a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b"

def send_study_reminders():
    try:
        response = requests.post(
            f"{API_URL}/api/notifications/send-study-reminders",
            headers={"X-API-Key": API_KEY},
            timeout=30
        )
        print(f"✅ Sent reminders: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Schedule to run every hour
schedule.every().hour.do(send_study_reminders)

print("🕐 Scheduler started. Sending study reminders every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

Run it:
```bash
python send_hourly_reminders.py
```

---

## 📊 User Settings

Users control their notifications through onboarding and profile settings:

### Onboarding Data Collected:
- **Exam Date:** When is their exam (`exam_date`)
- **Study Hours:** What hours they want reminders (`study_hours` array)
- **Push Token:** Their Expo push token (`expo_push_token`)

### Notification Preferences (stored in `notification_preferences` JSONB):
```json
{
  "study_reminders_enabled": true,
  "exam_countdown_enabled": true,
  "achievement_notifications_enabled": true
}
```

---

## 🧪 Testing

### Test 1: Send Study Reminders Now
```bash
curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send-study-reminders" \
  -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b"
```

### Test 2: Send Custom Notification to All Users
```bash
curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send" \
  -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "בדיקה 🧪",
    "body": "זו הודעת בדיקה"
  }'
```

---

## 🔒 Security Notes

1. **Never commit the API key to Git** - It's already in `.env` which is in `.gitignore`
2. **Use HTTPS** - The API should always be served over HTTPS in production
3. **Rate Limiting** - Consider adding rate limiting to prevent abuse
4. **Monitoring** - Set up monitoring to track failed notifications

---

## 📱 Push Token Management

Users get their push token during onboarding:

1. User completes onboarding
2. App requests notification permission
3. If granted, gets Expo push token
4. Token sent to API via `POST /api/users/me/onboarding`
5. Stored in `users.expo_push_token`

If a push token becomes invalid (user uninstalled app, etc.), Expo will return an error. The API logs these errors but continues sending to other users.

---

## 🚀 Deployment Checklist

- [ ] `.env` file has `NOTIFICATION_API_KEY` set
- [ ] API is deployed and accessible
- [ ] Scheduler service is configured (cron/Vercel/GitHub Actions)
- [ ] Test endpoint manually before scheduling
- [ ] Monitor logs for errors
- [ ] Set up alerts for failed notifications

---

## 📞 Support

If you need help:
1. Check API logs for errors
2. Test endpoints manually with curl
3. Verify user has `expo_push_token` in database
4. Check user's `notification_preferences` and `study_hours`
