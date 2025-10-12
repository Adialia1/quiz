-- Migration 009: Add Unique Constraint to User Mistakes
-- Run this in Supabase SQL Editor
-- This allows upsert operations on user_id + question_id

-- Add unique constraint on user_id and question_id combination
-- This ensures one record per user per question
ALTER TABLE user_mistakes
ADD CONSTRAINT user_mistakes_user_question_unique
UNIQUE (user_id, question_id);

-- Verify constraint was added
SELECT 'Migration 009 completed successfully - unique constraint added to user_mistakes' AS status;
