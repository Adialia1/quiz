-- Migration 007: Create User Topic Performance Table
-- Run this in Supabase SQL Editor
-- Aggregate performance by topic for each user

CREATE TABLE user_topic_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic TEXT NOT NULL,

  -- Performance
  total_questions INTEGER DEFAULT 0,
  correct_answers INTEGER DEFAULT 0,
  wrong_answers INTEGER DEFAULT 0,
  accuracy_percentage DECIMAL(5,2),

  -- Metrics
  average_time_seconds DECIMAL(6,2),
  last_practiced_at TIMESTAMPTZ,

  -- Strength level (auto-calculated)
  strength_level TEXT DEFAULT 'average' CHECK (strength_level IN ('weak', 'average', 'strong')),

  UNIQUE(user_id, topic)
);

-- Indexes
CREATE INDEX idx_topic_perf_user ON user_topic_performance(user_id);
CREATE INDEX idx_topic_perf_topic ON user_topic_performance(topic);
CREATE INDEX idx_topic_perf_strength ON user_topic_performance(strength_level);
CREATE INDEX idx_topic_perf_user_strength ON user_topic_performance(user_id, strength_level);

-- Function to calculate strength level
CREATE OR REPLACE FUNCTION calculate_strength_level(
  p_accuracy DECIMAL
) RETURNS TEXT AS $$
BEGIN
  IF p_accuracy IS NULL THEN
    RETURN 'average';
  END IF;

  IF p_accuracy < 70 THEN
    RETURN 'weak';
  ELSIF p_accuracy <= 90 THEN
    RETURN 'average';
  ELSE
    RETURN 'strong';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to auto-update strength level and accuracy
CREATE OR REPLACE FUNCTION update_topic_performance()
RETURNS TRIGGER AS $$
BEGIN
  -- Calculate accuracy percentage
  IF NEW.total_questions > 0 THEN
    NEW.accuracy_percentage := (NEW.correct_answers::DECIMAL / NEW.total_questions) * 100;
  ELSE
    NEW.accuracy_percentage := NULL;
  END IF;

  -- Calculate strength level
  NEW.strength_level := calculate_strength_level(NEW.accuracy_percentage);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_topic_performance
BEFORE INSERT OR UPDATE ON user_topic_performance
FOR EACH ROW EXECUTE FUNCTION update_topic_performance();

-- Verify table was created
SELECT 'Migration 007 completed successfully - user_topic_performance table created' AS status;
