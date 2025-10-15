-- Add onboarding and notification fields to users table
-- This allows us to:
-- 1. Track onboarding completion
-- 2. Send push notifications from server
-- 3. Schedule automatic notifications
-- 4. Sync user preferences across devices

ALTER TABLE users
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS exam_date DATE,
ADD COLUMN IF NOT EXISTS study_hours JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS expo_push_token TEXT,
ADD COLUMN IF NOT EXISTS notification_preferences JSONB DEFAULT '{
  "study_reminders_enabled": true,
  "exam_countdown_enabled": true,
  "achievement_notifications_enabled": true
}'::jsonb;

-- Create index for notification scheduling queries
CREATE INDEX IF NOT EXISTS idx_users_exam_date
ON users(exam_date)
WHERE exam_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_push_token
ON users(expo_push_token)
WHERE expo_push_token IS NOT NULL;

-- Add comments
COMMENT ON COLUMN users.onboarding_completed IS 'Whether user has completed onboarding flow';
COMMENT ON COLUMN users.exam_date IS 'User exam date for countdown and reminders';
COMMENT ON COLUMN users.study_hours IS 'Array of hours (0-23) for daily study reminders';
COMMENT ON COLUMN users.expo_push_token IS 'Expo push notification token for server-side notifications';
COMMENT ON COLUMN users.notification_preferences IS 'User notification preferences and settings';

-- Verify migration
SELECT
  'Migration completed successfully' AS status,
  count(*) AS total_users,
  count(expo_push_token) AS users_with_push_token,
  count(exam_date) AS users_with_exam_date
FROM users;
