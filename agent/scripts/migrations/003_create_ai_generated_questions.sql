-- Migration 003: Create AI Generated Questions Table
-- Run this in Supabase SQL Editor
-- This table stores AI-generated questions that users actually answer
-- Note: This is different from 'exam_questions' which is the RAG reference table

CREATE TABLE ai_generated_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Question Content (matches quiz_generator.py output format)
  question_text TEXT NOT NULL,

  -- Options (exactly 5: A, B, C, D, E)
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  option_e TEXT NOT NULL,

  correct_answer TEXT NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D', 'E')),
  explanation TEXT NOT NULL,

  -- Metadata
  topic TEXT NOT NULL,
  sub_topic TEXT,
  difficulty_level TEXT NOT NULL CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
  legal_reference TEXT,

  -- Optional
  image_url TEXT,
  source_doc_id UUID, -- Link to RAG document if available

  -- Generation metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  generated_by TEXT DEFAULT 'quiz_generator',

  -- Quality tracking (updated as users answer)
  quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
  times_shown INTEGER DEFAULT 0,
  times_correct INTEGER DEFAULT 0,
  times_wrong INTEGER DEFAULT 0,
  average_time_seconds DECIMAL(6,2),

  -- Expert validation metadata (from quiz_generator.py)
  expert_validated BOOLEAN DEFAULT false,
  expert_validation_data JSONB
);

-- Indexes for performance
CREATE INDEX idx_ai_questions_topic ON ai_generated_questions(topic);
CREATE INDEX idx_ai_questions_difficulty ON ai_generated_questions(difficulty_level);
CREATE INDEX idx_ai_questions_active ON ai_generated_questions(is_active);
CREATE INDEX idx_ai_questions_quality ON ai_generated_questions(quality_score);
CREATE INDEX idx_ai_questions_topic_difficulty ON ai_generated_questions(topic, difficulty_level);

-- Verify table was created
SELECT 'Migration 003 completed successfully - ai_generated_questions table created' AS status;
