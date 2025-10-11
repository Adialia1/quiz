"""
Supabase Database Schema Setup Script
Creates all tables, indexes, and functions for the AI Ethica system

IMPORTANT: Run this via Supabase SQL Editor for best results
This script provides instructions and verification
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY, validate_config

def get_supabase_client() -> Client:
    """Initialize Supabase client with service key"""
    validate_config()
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def setup_pgvector_extension(supabase: Client):
    """Enable pgvector extension"""
    print("🔧 Enabling pgvector extension...")

    sql = """
    CREATE EXTENSION IF NOT EXISTS vector;
    """

    try:
        supabase.rpc('exec_sql', {'query': sql}).execute()
        print("✅ pgvector extension enabled")
    except Exception as e:
        print(f"⚠️  pgvector might already be enabled: {e}")

def create_legal_docs_table(supabase: Client):
    """Create table for legal document chunks (RAG #1)"""
    print("📄 Creating legal_doc_chunks table...")

    sql = """
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
    """

    supabase.rpc('exec_sql', {'query': sql}).execute()
    print("✅ legal_doc_chunks table created")

def create_exam_questions_table(supabase: Client):
    """Create table for exam questions (RAG #2)"""
    print("❓ Creating exam_questions table...")

    sql = """
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
    """

    supabase.rpc('exec_sql', {'query': sql}).execute()
    print("✅ exam_questions table created")

def create_users_table(supabase: Client):
    """Create users table"""
    print("👤 Creating users table...")

    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email TEXT UNIQUE NOT NULL,
        full_name TEXT,
        skill_level TEXT CHECK (skill_level IN ('beginner','intermediate','advanced','expert')),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        last_active_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);
    """

    supabase.rpc('exec_sql', {'query': sql}).execute()
    print("✅ users table created")

def create_performance_tracking_table(supabase: Client):
    """Create user performance tracking table"""
    print("📊 Creating user_performance table...")

    sql = """
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
    """

    supabase.rpc('exec_sql', {'query': sql}).execute()
    print("✅ user_performance table created")

def create_chat_history_table(supabase: Client):
    """Create chat history table for AI Mentor"""
    print("💬 Creating chat_messages table...")

    sql = """
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
    """

    supabase.rpc('exec_sql', {'query': sql}).execute()
    print("✅ chat_messages table created")

def create_study_sessions_table(supabase: Client):
    """Create study sessions table"""
    print("📚 Creating study_sessions table...")

    sql = """
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
    """

    supabase.rpc('exec_sql', {'query': sql}).execute()
    print("✅ study_sessions table created")

def create_topic_mastery_table(supabase: Client):
    """Create topic mastery tracking table"""
    print("🎯 Creating topic_mastery table...")

    sql = """
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
    """

    supabase.rpc('exec_sql', {'query': sql}).execute()
    print("✅ topic_mastery table created")

def main():
    """Run all setup steps"""
    print("\n" + "="*60)
    print("🚀 AI Ethica - Supabase Schema Setup")
    print("="*60 + "\n")

    try:
        # Initialize client
        supabase = get_supabase_client()
        print(f"✅ Connected to Supabase: {SUPABASE_URL}\n")

        # Note: pgvector extension must be enabled via Supabase dashboard
        # Database → Extensions → Enable "vector"
        print("⚠️  IMPORTANT: Enable pgvector extension manually in Supabase dashboard:")
        print("   Dashboard → Database → Extensions → Enable 'vector'\n")

        # Create tables
        create_legal_docs_table(supabase)
        create_exam_questions_table(supabase)
        create_users_table(supabase)
        create_performance_tracking_table(supabase)
        create_chat_history_table(supabase)
        create_study_sessions_table(supabase)
        create_topic_mastery_table(supabase)

        print("\n" + "="*60)
        print("✅ Schema setup complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Enable pgvector extension in Supabase dashboard")
        print("2. Run: python scripts/ingest_legal_docs.py")
        print("3. Run: python scripts/ingest_exam_questions.py")

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
