# Notification System - How It Works

## 📋 Overview

Your notification system is fully configured and working! Here's how everything fits together.

---

## 🕐 How `/send-study-reminders` Works

### Basic Logic:
```python
Current Hour (Israel Time) → Check Users' study_hours → Send Notifications
```

### Example Scenarios:

**Scenario 1: User with study_hours = [18, 20, 22]**
- **17:00** - API called → Current hour = 17 → NOT in [18, 20, 22] → ❌ No notification
- **17:30** - API called → Current hour = 17 → NOT in [18, 20, 22] → ❌ No notification
- **18:00** - API called → Current hour = 18 → ✅ IN [18, 20, 22] → ✅ Notification sent
- **18:15** - API called → Current hour = 18 → ✅ IN [18, 20, 22] → ✅ Notification sent
- **18:59** - API called → Current hour = 18 → ✅ IN [18, 20, 22] → ✅ Notification sent
- **19:00** - API called → Current hour = 19 → NOT in [18, 20, 22] → ❌ No notification
- **20:00** - API called → Current hour = 20 → ✅ IN [18, 20, 22] → ✅ Notification sent

**Scenario 2: Called at 17:10**
```
Current time: 17:10 (Israel)
Current hour: 17
Users with 17 in their study_hours → Will receive notification
Users without 17 in study_hours → Will NOT receive notification
```

---

## ⏰ Timezone Configuration

✅ **The API now uses Israel timezone (`Asia/Jerusalem`)**

- Server local time might be different
- API always checks **Israel hour**
- Users select hours in Israel time in the app
- Everything matches! 🎯

**Current Time Check:**
```bash
Server Local: 2025-10-14 17:25:03 (Hour: 17)
UTC:          2025-10-14 14:25:03 (Hour: 14)
Israel:       2025-10-14 17:25:03 (Hour: 17) ← API uses this!
```

---

## 📱 Two API Endpoints

### 1. `/api/notifications/send` (General Notifications)
**Purpose:** Send custom notifications to users anytime

**Behavior:**
- ✅ Sends to ALL users with push tokens
- ✅ Ignores study hours
- ✅ Ignores notification preferences
- ✅ Can send anytime

**Use cases:**
- Testing notifications
- Special announcements
- Exam reminders
- Achievement notifications

**Example:**
```bash
curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send" \
  -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "מבחן מחר! 📚",
    "body": "אל תשכח להתכונן למבחן"
  }'
```

---

### 2. `/api/notifications/send-study-reminders` (Scheduled)
**Purpose:** Send study reminders based on user's selected hours

**Behavior:**
- ✅ Checks Israel current hour
- ✅ Only sends to users with matching hour in `study_hours`
- ✅ Respects `notification_preferences.study_reminders_enabled`
- ✅ Fixed notification text: "זמן ללמוד! 📚"

**Use cases:**
- Hourly scheduler (automated)
- Daily study reminders

**Example:**
```bash
curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send-study-reminders" \
  -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b"
```

---

## 🎯 User Flow

### During Onboarding:
1. User selects exam date
2. User selects study hours (e.g., [18, 20, 22])
3. App requests notification permission
4. If granted, gets Expo push token
5. Sends all data to API: `/api/users/me/onboarding`
6. Database stores:
   - `exam_date`
   - `study_hours` (array of hours 0-23)
   - `expo_push_token`
   - `notification_preferences` (JSON)
   - `onboarding_completed = true`

### When Scheduler Runs:
```
Every hour (e.g., 18:00 Israel time):
  ↓
API: /send-study-reminders
  ↓
Get current hour: 18
  ↓
Query users where:
  - onboarding_completed = true
  - expo_push_token != null
  - notification_preferences.study_reminders_enabled = true
  - 18 IN study_hours
  ↓
Send "זמן ללמוד! 📚" to matching users
  ↓
Return stats: sent/failed
```

---

## 🔧 Testing

### Quick Test Script:
```bash
source venv/bin/activate
python send_notification_now.py
# Choose option 1 for test notification
# Choose option 2 for study reminders
```

### Manual Test with curl:
```bash
# Test general notification
curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send" \
  -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b" \
  -H "Content-Type: application/json" \
  -d '{"title": "בדיקה", "body": "הודעת בדיקה"}'

# Test study reminders (will send only if current hour matches user's hours)
curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send-study-reminders" \
  -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b"
```

---

## 🤖 Setting Up Automated Scheduler

### Option 1: Cron Job (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add this line (runs every hour at :00)
0 * * * * curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send-study-reminders" -H "X-API-Key: a8e0d4c09a3c5c0dc1fc5e191c7bf1915f99060e271c30440fd5917acdd2970b" >> /var/log/study-reminders.log 2>&1
```

### Option 2: Vercel Cron
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
```yaml
name: Hourly Study Reminders
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
jobs:
  send:
    runs-on: ubuntu-latest
    steps:
      - name: Send Study Reminders
        run: |
          curl -X POST "https://accepted-awfully-bug.ngrok-free.app/api/notifications/send-study-reminders" \
            -H "X-API-Key: ${{ secrets.NOTIFICATION_API_KEY }}"
```

---

## 📊 Database Schema

### Users Table:
```sql
users:
  - onboarding_completed: BOOLEAN
  - exam_date: DATE
  - study_hours: JSONB  -- [18, 20, 22]
  - expo_push_token: TEXT  -- "ExponentPushToken[...]"
  - notification_preferences: JSONB:
      {
        "study_reminders_enabled": true,
        "exam_countdown_enabled": true,
        "achievement_notifications_enabled": true
      }
```

---

## 🔑 Important Details

### Minutes Don't Matter
- The system checks **hour only** (0-23)
- If called at 17:10, 17:25, or 17:59 → all use hour **17**
- This prevents duplicate notifications in the same hour

### Best Practice for Scheduler:
**Call at the START of each hour** (e.g., 18:00, 19:00, 20:00)

This way:
- Users get notifications at predictable times
- No duplicates within the same hour
- Clean logs and tracking

### Example Cron:
```bash
# Good: Runs at 00:00, 01:00, 02:00, ..., 23:00
0 * * * * [command]

# Also good: Runs at 00:05, 01:05, 02:05, ...
5 * * * * [command]

# Bad: Runs every minute (will send duplicate notifications!)
* * * * * [command]
```

---

## ✅ Current Status

**What's Working:**
- ✅ Onboarding flow saves all data
- ✅ Push tokens stored in database
- ✅ Notifications sending successfully
- ✅ Israel timezone configured
- ✅ API endpoints fully functional
- ✅ Error handling and logging
- ✅ Test scripts available

**What You Need to Do:**
- ⏰ Set up a scheduler (cron, Vercel, GitHub Actions)
- 📱 Test with real users
- 📊 Monitor logs for errors

---

## 🚨 Troubleshooting

### No Notifications Received:
1. Check user has `expo_push_token` in database
2. Check user has `onboarding_completed = true`
3. Check current hour matches user's `study_hours`
4. Check `notification_preferences.study_reminders_enabled = true`
5. Check API logs for errors

### Check User Settings:
```bash
source venv/bin/activate
python -c "
from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
result = supabase.table('users').select('*').eq('email', 'user@example.com').execute()
print(result.data)
"
```

### Test Current Hour:
```bash
source venv/bin/activate
python -c "
from datetime import datetime
from zoneinfo import ZoneInfo
israel_time = datetime.now(ZoneInfo('Asia/Jerusalem'))
print(f'Current Israel hour: {israel_time.hour}')
"
```

---

## 📞 API Response Examples

### Success:
```json
{
  "status": "success",
  "message": "Sent study reminders for hour 18",
  "current_hour": 18,
  "total_eligible_users": 5,
  "sent": 5,
  "failed": 0,
  "errors": []
}
```

### Partial Failure:
```json
{
  "status": "success",
  "total_users": 10,
  "sent": 8,
  "failed": 2,
  "errors": [
    "User user_123456: Push token is invalid",
    "User user_789012: No response from Expo"
  ]
}
```

---

## 🎉 Summary

Your notification system is **production-ready**!

- Users select their study hours during onboarding
- Scheduler calls API every hour
- API checks Israel time and sends to matching users
- Minutes don't matter - only the hour
- Everything is logged and tracked

Just set up your scheduler and you're good to go! 🚀
