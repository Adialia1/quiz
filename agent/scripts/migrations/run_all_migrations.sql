-- Run All Migrations
-- Execute this in Supabase SQL Editor to set up the complete database schema
--
-- WARNING: This will drop existing tables (users, user_performance, chat_messages, study_sessions, topic_mastery)
-- Tables NOT touched: legal_doc_chunks, exam_questions (RAG tables)

BEGIN;

-- ============================================================
-- Migration 001: Drop Old Tables
-- ============================================================

DROP TABLE IF EXISTS topic_mastery CASCADE;
DROP TABLE IF EXISTS study_sessions CASCADE;
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS user_performance CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- Migration 002: Create Users Table
-- ============================================================

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  phone TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_login_at TIMESTAMPTZ,
  subscription_status TEXT DEFAULT 'free' CHECK (subscription_status IN ('free', 'premium', 'trial')),
  subscription_expires_at TIMESTAMPTZ,
  total_questions_answered INTEGER DEFAULT 0,
  total_exams_taken INTEGER DEFAULT 0,
  average_score DECIMAL(5,2),
  preferred_difficulty TEXT DEFAULT 'adaptive' CHECK (preferred_difficulty IN ('easy', 'medium', 'hard', 'adaptive'))
);

CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription ON users(subscription_status);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Migration 003: Create AI Generated Questions
-- ============================================================

CREATE TABLE ai_generated_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_text TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  option_e TEXT NOT NULL,
  correct_answer TEXT NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D', 'E')),
  explanation TEXT NOT NULL,
  topic TEXT NOT NULL,
  sub_topic TEXT,
  difficulty_level TEXT NOT NULL CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
  legal_reference TEXT,
  image_url TEXT,
  source_doc_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  generated_by TEXT DEFAULT 'quiz_generator',
  quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
  times_shown INTEGER DEFAULT 0,
  times_correct INTEGER DEFAULT 0,
  times_wrong INTEGER DEFAULT 0,
  average_time_seconds DECIMAL(6,2),
  expert_validated BOOLEAN DEFAULT false,
  expert_validation_data JSONB
);

CREATE INDEX idx_ai_questions_topic ON ai_generated_questions(topic);
CREATE INDEX idx_ai_questions_difficulty ON ai_generated_questions(difficulty_level);
CREATE INDEX idx_ai_questions_active ON ai_generated_questions(is_active);
CREATE INDEX idx_ai_questions_quality ON ai_generated_questions(quality_score);
CREATE INDEX idx_ai_questions_topic_difficulty ON ai_generated_questions(topic, difficulty_level);

-- ============================================================
-- Migration 004: Create Exams Table
-- ============================================================

CREATE TABLE exams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  exam_type TEXT NOT NULL CHECK (exam_type IN ('practice', 'full_simulation', 'review_mistakes')),
  status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  total_questions INTEGER NOT NULL,
  answered_questions INTEGER DEFAULT 0,
  correct_answers INTEGER DEFAULT 0,
  wrong_answers INTEGER DEFAULT 0,
  skipped_answers INTEGER DEFAULT 0,
  score_percentage DECIMAL(5,2),
  time_taken_seconds INTEGER,
  passing_threshold INTEGER DEFAULT 85,
  passed BOOLEAN,
  topics_covered JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX idx_exams_user ON exams(user_id);
CREATE INDEX idx_exams_type ON exams(exam_type);
CREATE INDEX idx_exams_status ON exams(status);
CREATE INDEX idx_exams_completed ON exams(completed_at DESC);
CREATE INDEX idx_exams_user_completed ON exams(user_id, completed_at DESC);

-- ============================================================
-- Migration 005: Create Exam Question Answers
-- ============================================================

CREATE TABLE exam_question_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),
  question_order INTEGER NOT NULL,
  user_answer TEXT CHECK (user_answer IN ('A', 'B', 'C', 'D', 'E', NULL)),
  is_correct BOOLEAN,
  time_taken_seconds INTEGER,
  answered_at TIMESTAMPTZ,
  flagged_for_review BOOLEAN DEFAULT false,
  UNIQUE(exam_id, question_order)
);

CREATE INDEX idx_exam_answers_exam ON exam_question_answers(exam_id);
CREATE INDEX idx_exam_answers_question ON exam_question_answers(question_id);
CREATE INDEX idx_exam_answers_correct ON exam_question_answers(is_correct);
CREATE INDEX idx_exam_answers_order ON exam_question_answers(exam_id, question_order);

-- ============================================================
-- Migration 006: Create User Question History
-- ============================================================

CREATE TABLE user_question_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),
  times_seen INTEGER DEFAULT 0,
  times_correct INTEGER DEFAULT 0,
  times_wrong INTEGER DEFAULT 0,
  first_seen_at TIMESTAMPTZ,
  last_seen_at TIMESTAMPTZ,
  average_time_seconds DECIMAL(6,2),
  mastery_level TEXT DEFAULT 'not_seen' CHECK (mastery_level IN ('not_seen', 'learning', 'practicing', 'mastered')),
  UNIQUE(user_id, question_id)
);

CREATE INDEX idx_history_user ON user_question_history(user_id);
CREATE INDEX idx_history_question ON user_question_history(question_id);
CREATE INDEX idx_history_mastery ON user_question_history(mastery_level);
CREATE INDEX idx_history_user_mastery ON user_question_history(user_id, mastery_level);

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

CREATE OR REPLACE FUNCTION update_mastery_level()
RETURNS TRIGGER AS $$
BEGIN
  NEW.mastery_level := calculate_mastery_level(NEW.times_seen, NEW.times_correct, NEW.times_wrong);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_mastery_level
BEFORE INSERT OR UPDATE ON user_question_history
FOR EACH ROW EXECUTE FUNCTION update_mastery_level();

-- ============================================================
-- Migration 007: Create User Topic Performance
-- ============================================================

CREATE TABLE user_topic_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic TEXT NOT NULL,
  total_questions INTEGER DEFAULT 0,
  correct_answers INTEGER DEFAULT 0,
  wrong_answers INTEGER DEFAULT 0,
  accuracy_percentage DECIMAL(5,2),
  average_time_seconds DECIMAL(6,2),
  last_practiced_at TIMESTAMPTZ,
  strength_level TEXT DEFAULT 'average' CHECK (strength_level IN ('weak', 'average', 'strong')),
  UNIQUE(user_id, topic)
);

CREATE INDEX idx_topic_perf_user ON user_topic_performance(user_id);
CREATE INDEX idx_topic_perf_topic ON user_topic_performance(topic);
CREATE INDEX idx_topic_perf_strength ON user_topic_performance(strength_level);
CREATE INDEX idx_topic_perf_user_strength ON user_topic_performance(user_id, strength_level);

CREATE OR REPLACE FUNCTION calculate_strength_level(p_accuracy DECIMAL)
RETURNS TEXT AS $$
BEGIN
  IF p_accuracy IS NULL THEN RETURN 'average'; END IF;
  IF p_accuracy < 70 THEN RETURN 'weak';
  ELSIF p_accuracy <= 90 THEN RETURN 'average';
  ELSE RETURN 'strong';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION update_topic_performance()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.total_questions > 0 THEN
    NEW.accuracy_percentage := (NEW.correct_answers::DECIMAL / NEW.total_questions) * 100;
  ELSE
    NEW.accuracy_percentage := NULL;
  END IF;
  NEW.strength_level := calculate_strength_level(NEW.accuracy_percentage);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_topic_performance
BEFORE INSERT OR UPDATE ON user_topic_performance
FOR EACH ROW EXECUTE FUNCTION update_topic_performance();

-- ============================================================
-- Migration 008: Create User Mistakes
-- ============================================================

CREATE TABLE user_mistakes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),
  exam_id UUID REFERENCES exams(id),
  times_wrong INTEGER DEFAULT 1,
  first_wrong_at TIMESTAMPTZ DEFAULT NOW(),
  last_wrong_at TIMESTAMPTZ DEFAULT NOW(),
  reviewed BOOLEAN DEFAULT false,
  reviewed_at TIMESTAMPTZ,
  marked_for_review BOOLEAN DEFAULT true
);

CREATE INDEX idx_mistakes_user ON user_mistakes(user_id);
CREATE INDEX idx_mistakes_question ON user_mistakes(question_id);
CREATE INDEX idx_mistakes_reviewed ON user_mistakes(reviewed);
CREATE INDEX idx_mistakes_marked ON user_mistakes(marked_for_review);
CREATE INDEX idx_mistakes_user_reviewed ON user_mistakes(user_id, reviewed, marked_for_review);

-- ============================================================
-- Migration 009: Add Unique Constraint to User Mistakes
-- ============================================================

ALTER TABLE user_mistakes
ADD CONSTRAINT user_mistakes_user_question_unique
UNIQUE (user_id, question_id);

-- ============================================================
-- Migration 010: Create AI Chat Tables
-- ============================================================

CREATE TABLE ai_chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic TEXT,
  question_id UUID REFERENCES ai_generated_questions(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_message_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user ON ai_chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_created ON ai_chat_sessions(created_at DESC);

CREATE TABLE ai_chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON ai_chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON ai_chat_messages(created_at DESC);
CREATE INDEX idx_chat_messages_session_created ON ai_chat_messages(session_id, created_at);

CREATE OR REPLACE FUNCTION update_session_last_message()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE ai_chat_sessions SET last_message_at = NEW.created_at WHERE id = NEW.session_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_last_message
AFTER INSERT ON ai_chat_messages
FOR EACH ROW EXECUTE FUNCTION update_session_last_message();

-- ============================================================
-- Verify All Tables
-- ============================================================

SELECT 'All migrations completed successfully!' AS status;

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'users',
    'ai_generated_questions',
    'exams',
    'exam_question_answers',
    'user_question_history',
    'user_topic_performance',
    'user_mistakes',
    'ai_chat_sessions',
    'ai_chat_messages'
)
ORDER BY table_name;

COMMIT;
