-- AI Ethica Database Schema
-- Run this in Supabase SQL Editor: Dashboard → SQL Editor → New Query

-- Enable pgvector extension (MUST RUN FIRST)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Legal Document Chunks (RAG #1)
-- ============================================================

CREATE TABLE IF NOT EXISTS legal_doc_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_name TEXT NOT NULL,
    page_number INT,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search (HNSW = fast approximate search)
CREATE INDEX IF NOT EXISTS legal_chunks_embedding_idx
ON legal_doc_chunks
USING hnsw (embedding vector_cosine_ops);

-- Create index for document lookup
CREATE INDEX IF NOT EXISTS legal_chunks_document_idx
ON legal_doc_chunks(document_name);

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_legal_chunks(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    document_name TEXT,
    page_number INT,
    chunk_index INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        legal_doc_chunks.id,
        legal_doc_chunks.document_name,
        legal_doc_chunks.page_number,
        legal_doc_chunks.chunk_index,
        legal_doc_chunks.content,
        legal_doc_chunks.metadata,
        1 - (legal_doc_chunks.embedding <=> query_embedding) AS similarity
    FROM legal_doc_chunks
    WHERE 1 - (legal_doc_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY legal_doc_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================
-- Exam Questions (RAG #2)
-- ============================================================

CREATE TABLE IF NOT EXISTS exam_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    option_e TEXT NOT NULL,
    correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A','B','C','D','E')),
    explanation TEXT,
    topic TEXT,
    difficulty TEXT CHECK (difficulty IN ('easy','medium','hard')),
    legal_reference TEXT,
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS exam_questions_embedding_idx
ON exam_questions
USING hnsw (embedding vector_cosine_ops);

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS exam_questions_topic_idx
ON exam_questions(topic);

CREATE INDEX IF NOT EXISTS exam_questions_difficulty_idx
ON exam_questions(difficulty);

CREATE INDEX IF NOT EXISTS exam_questions_active_idx
ON exam_questions(is_active);

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_exam_questions(
    query_embedding VECTOR(1024),
    filter_topic TEXT DEFAULT NULL,
    filter_difficulty TEXT DEFAULT NULL,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    question_text TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    option_e TEXT,
    correct_answer CHAR(1),
    explanation TEXT,
    topic TEXT,
    difficulty TEXT,
    legal_reference TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        exam_questions.id,
        exam_questions.question_text,
        exam_questions.option_a,
        exam_questions.option_b,
        exam_questions.option_c,
        exam_questions.option_d,
        exam_questions.option_e,
        exam_questions.correct_answer,
        exam_questions.explanation,
        exam_questions.topic,
        exam_questions.difficulty,
        exam_questions.legal_reference,
        exam_questions.metadata,
        1 - (exam_questions.embedding <=> query_embedding) AS similarity
    FROM exam_questions
    WHERE is_active = true
        AND (filter_topic IS NULL OR exam_questions.topic = filter_topic)
        AND (filter_difficulty IS NULL OR exam_questions.difficulty = filter_difficulty)
        AND 1 - (exam_questions.embedding <=> query_embedding) > match_threshold
    ORDER BY exam_questions.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================
-- Users
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    skill_level TEXT CHECK (skill_level IN ('beginner','intermediate','advanced','expert')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);

-- ============================================================
-- User Performance Tracking
-- ============================================================

CREATE TABLE IF NOT EXISTS user_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID REFERENCES exam_questions(id) ON DELETE CASCADE,
    selected_answer CHAR(1) CHECK (selected_answer IN ('A','B','C','D','E')),
    is_correct BOOLEAN NOT NULL,
    response_time_ms INT,
    session_id UUID,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance queries
CREATE INDEX IF NOT EXISTS user_performance_user_idx ON user_performance(user_id);
CREATE INDEX IF NOT EXISTS user_performance_question_idx ON user_performance(question_id);
CREATE INDEX IF NOT EXISTS user_performance_session_idx ON user_performance(session_id);
CREATE INDEX IF NOT EXISTS user_performance_timestamp_idx ON user_performance(timestamp DESC);

-- Composite index for user + timestamp queries
CREATE INDEX IF NOT EXISTS user_performance_user_time_idx
ON user_performance(user_id, timestamp DESC);

-- ============================================================
-- Chat History
-- ============================================================

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
    content TEXT NOT NULL,
    context_chunks JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for chat retrieval
CREATE INDEX IF NOT EXISTS chat_messages_user_idx ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS chat_messages_session_idx ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS chat_messages_created_idx ON chat_messages(created_at DESC);

-- Composite index for session-based queries
CREATE INDEX IF NOT EXISTS chat_messages_session_created_idx
ON chat_messages(session_id, created_at);

-- ============================================================
-- Study Sessions
-- ============================================================

CREATE TABLE IF NOT EXISTS study_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_type TEXT CHECK (session_type IN ('practice', 'exam', 'review')) NOT NULL,
    topic_focus TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    total_questions INT DEFAULT 0,
    correct_answers INT DEFAULT 0,
    accuracy FLOAT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS study_sessions_user_idx ON study_sessions(user_id);
CREATE INDEX IF NOT EXISTS study_sessions_started_idx ON study_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS study_sessions_type_idx ON study_sessions(session_type);

-- ============================================================
-- Topic Mastery Tracking
-- ============================================================

CREATE TABLE IF NOT EXISTS topic_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    mastery_score FLOAT DEFAULT 0.0 CHECK (mastery_score >= 0 AND mastery_score <= 1),
    total_attempts INT DEFAULT 0,
    correct_attempts INT DEFAULT 0,
    last_practiced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, topic)
);

-- Indexes
CREATE INDEX IF NOT EXISTS topic_mastery_user_idx ON topic_mastery(user_id);
CREATE INDEX IF NOT EXISTS topic_mastery_score_idx ON topic_mastery(mastery_score);
CREATE INDEX IF NOT EXISTS topic_mastery_last_practiced_idx ON topic_mastery(last_practiced_at);

-- ============================================================
-- Done!
-- ============================================================

-- Verify tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'legal_doc_chunks',
    'exam_questions',
    'users',
    'user_performance',
    'chat_messages',
    'study_sessions',
    'topic_mastery'
)
ORDER BY table_name;
