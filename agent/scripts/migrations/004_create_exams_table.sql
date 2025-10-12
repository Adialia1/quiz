-- Migration 004: Create Exams Table
-- Run this in Supabase SQL Editor

CREATE TABLE exams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Exam metadata
  exam_type TEXT NOT NULL CHECK (exam_type IN ('practice', 'full_simulation', 'review_mistakes')),
  status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),

  -- Timestamps
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,

  -- Questions
  total_questions INTEGER NOT NULL,
  answered_questions INTEGER DEFAULT 0,
  correct_answers INTEGER DEFAULT 0,
  wrong_answers INTEGER DEFAULT 0,
  skipped_answers INTEGER DEFAULT 0,

  -- Results
  score_percentage DECIMAL(5,2),
  time_taken_seconds INTEGER,
  passing_threshold INTEGER DEFAULT 85, -- 85% to pass
  passed BOOLEAN,

  -- Topics covered in this exam
  topics_covered JSONB DEFAULT '[]'::jsonb -- e.g., ["מידע פנים", "חובות גילוי"]
);

-- Indexes
CREATE INDEX idx_exams_user ON exams(user_id);
CREATE INDEX idx_exams_type ON exams(exam_type);
CREATE INDEX idx_exams_status ON exams(status);
CREATE INDEX idx_exams_completed ON exams(completed_at DESC);
CREATE INDEX idx_exams_user_completed ON exams(user_id, completed_at DESC);

-- Verify table was created
SELECT 'Migration 004 completed successfully - exams table created' AS status;
