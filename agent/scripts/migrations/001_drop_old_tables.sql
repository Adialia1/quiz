-- Migration 001: Drop Old Tables
-- Run this in Supabase SQL Editor
-- This migration drops old tables that will be replaced with new schema

-- Drop old tables (keeping legal_doc_chunks and exam_questions - those are RAG tables)
DROP TABLE IF EXISTS topic_mastery CASCADE;
DROP TABLE IF EXISTS study_sessions CASCADE;
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS user_performance CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Verify tables were dropped
SELECT 'Migration 001 completed successfully' AS status;
