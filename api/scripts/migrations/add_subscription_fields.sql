-- Add subscription fields to users table for RevenueCat integration
-- Run this in Supabase SQL Editor

-- Step 1: Add new columns if they don't exist
ALTER TABLE users
ADD COLUMN IF NOT EXISTS subscription_period VARCHAR(20) DEFAULT NULL CHECK (subscription_period IN ('monthly', 'quarterly', NULL)),
ADD COLUMN IF NOT EXISTS is_in_trial BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS subscription_will_renew BOOLEAN DEFAULT FALSE;

-- Step 2: Update the subscription_status constraint to include more statuses
-- First drop the old constraint if it exists
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_subscription_status_check;

-- Add new constraint with extended values
-- 'free' = no subscription
-- 'premium' = active paid subscription
-- 'trial' = in trial period
-- 'active' = active subscription (alternative to premium)
-- 'expired' = subscription expired
-- 'none' = no subscription (alternative to free)
ALTER TABLE users
ADD CONSTRAINT users_subscription_status_check
CHECK (subscription_status IN ('free', 'premium', 'trial', 'active', 'expired', 'none'));

-- Step 3: Create indexes for better query performance (if not exist)
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_users_subscription_expires_at ON users(subscription_expires_at);
CREATE INDEX IF NOT EXISTS idx_users_subscription_period ON users(subscription_period) WHERE subscription_period IS NOT NULL;

-- Step 4: Update existing data (set default values for existing users)
UPDATE users
SET subscription_will_renew = FALSE
WHERE subscription_will_renew IS NULL;

UPDATE users
SET is_in_trial = FALSE
WHERE is_in_trial IS NULL;

-- Step 5: Update subscription_status for consistency
-- Map 'premium' to 'active' for active subscribers
-- Keep 'free' as 'free' or change to 'none' (optional)
UPDATE users
SET subscription_status = 'active'
WHERE subscription_status = 'premium'
  AND subscription_expires_at IS NOT NULL
  AND subscription_expires_at > NOW();

-- Mark expired premium users as 'expired'
UPDATE users
SET subscription_status = 'expired'
WHERE subscription_status = 'premium'
  AND subscription_expires_at IS NOT NULL
  AND subscription_expires_at <= NOW();

-- Step 6: Add comments
COMMENT ON COLUMN users.subscription_period IS 'Subscription period: monthly or quarterly';
COMMENT ON COLUMN users.is_in_trial IS 'Whether user is in trial period (3 days for monthly plan)';
COMMENT ON COLUMN users.subscription_will_renew IS 'Whether subscription will auto-renew';

-- Verify migration
SELECT
  'Migration completed successfully' AS status,
  count(*) AS total_users,
  count(*) FILTER (WHERE subscription_status IN ('active', 'premium')) AS active_subscribers,
  count(*) FILTER (WHERE is_in_trial = TRUE) AS users_in_trial,
  count(*) FILTER (WHERE subscription_period IS NOT NULL) AS users_with_period
FROM users;
