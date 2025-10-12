-- Migration 008: Create User Mistakes Table
-- Run this in Supabase SQL Editor
-- Track questions the user got wrong for "חזרה על טעויות"

CREATE TABLE user_mistakes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),
  exam_id UUID REFERENCES exams(id), -- Which exam it was from (optional)

  -- Mistake tracking
  times_wrong INTEGER DEFAULT 1,
  first_wrong_at TIMESTAMPTZ DEFAULT NOW(),
  last_wrong_at TIMESTAMPTZ DEFAULT NOW(),

  -- Review status
  reviewed BOOLEAN DEFAULT false, -- True after user gets it right in review mode
  reviewed_at TIMESTAMPTZ,
  marked_for_review BOOLEAN DEFAULT true
);

-- Indexes
CREATE INDEX idx_mistakes_user ON user_mistakes(user_id);
CREATE INDEX idx_mistakes_question ON user_mistakes(question_id);
CREATE INDEX idx_mistakes_reviewed ON user_mistakes(reviewed);
CREATE INDEX idx_mistakes_marked ON user_mistakes(marked_for_review);
CREATE INDEX idx_mistakes_user_reviewed ON user_mistakes(user_id, reviewed, marked_for_review);

-- Verify table was created
SELECT 'Migration 008 completed successfully - user_mistakes table created' AS status;
