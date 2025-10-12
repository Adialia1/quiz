-- Migration 005: Create Exam Question Answers Junction Table
-- Run this in Supabase SQL Editor
-- Links exams to questions with user answers

CREATE TABLE exam_question_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),

  -- Question order in exam
  question_order INTEGER NOT NULL, -- 1, 2, 3, etc.

  -- User's answer
  user_answer TEXT CHECK (user_answer IN ('A', 'B', 'C', 'D', 'E', NULL)),
  is_correct BOOLEAN,

  -- Timing
  time_taken_seconds INTEGER,
  answered_at TIMESTAMPTZ,

  -- Flags
  flagged_for_review BOOLEAN DEFAULT false, -- User can flag during exam

  UNIQUE(exam_id, question_order)
);

-- Indexes
CREATE INDEX idx_exam_answers_exam ON exam_question_answers(exam_id);
CREATE INDEX idx_exam_answers_question ON exam_question_answers(question_id);
CREATE INDEX idx_exam_answers_correct ON exam_question_answers(is_correct);
CREATE INDEX idx_exam_answers_order ON exam_question_answers(exam_id, question_order);

-- Verify table was created
SELECT 'Migration 005 completed successfully - exam_question_answers table created' AS status;
