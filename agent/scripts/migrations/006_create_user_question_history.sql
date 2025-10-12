-- Migration 006: Create User Question History Table
-- Run this in Supabase SQL Editor
-- Aggregate history of each user's performance on each question

CREATE TABLE user_question_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),

  -- Performance
  times_seen INTEGER DEFAULT 0,
  times_correct INTEGER DEFAULT 0,
  times_wrong INTEGER DEFAULT 0,

  -- Timestamps
  first_seen_at TIMESTAMPTZ,
  last_seen_at TIMESTAMPTZ,

  -- Metrics
  average_time_seconds DECIMAL(6,2),

  -- Mastery level (auto-calculated)
  mastery_level TEXT DEFAULT 'not_seen' CHECK (mastery_level IN ('not_seen', 'learning', 'practicing', 'mastered')),

  UNIQUE(user_id, question_id)
);

-- Indexes
CREATE INDEX idx_history_user ON user_question_history(user_id);
CREATE INDEX idx_history_question ON user_question_history(question_id);
CREATE INDEX idx_history_mastery ON user_question_history(mastery_level);
CREATE INDEX idx_history_user_mastery ON user_question_history(user_id, mastery_level);

-- Function to calculate mastery level
CREATE OR REPLACE FUNCTION calculate_mastery_level(
  p_times_seen INTEGER,
  p_times_correct INTEGER,
  p_times_wrong INTEGER
) RETURNS TEXT AS $$
DECLARE
  accuracy DECIMAL;
BEGIN
  IF p_times_seen = 0 THEN
    RETURN 'not_seen';
  END IF;

  IF p_times_seen <= 2 THEN
    IF p_times_correct::DECIMAL / p_times_seen < 0.5 THEN
      RETURN 'learning';
    ELSE
      RETURN 'practicing';
    END IF;
  END IF;

  accuracy := p_times_correct::DECIMAL / p_times_seen;

  IF accuracy < 0.5 THEN
    RETURN 'learning';
  ELSIF accuracy <= 0.8 THEN
    RETURN 'practicing';
  ELSE
    RETURN 'mastered';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to auto-update mastery level
CREATE OR REPLACE FUNCTION update_mastery_level()
RETURNS TRIGGER AS $$
BEGIN
  NEW.mastery_level := calculate_mastery_level(
    NEW.times_seen,
    NEW.times_correct,
    NEW.times_wrong
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_mastery_level
BEFORE INSERT OR UPDATE ON user_question_history
FOR EACH ROW EXECUTE FUNCTION update_mastery_level();

-- Verify table was created
SELECT 'Migration 006 completed successfully - user_question_history table created' AS status;
