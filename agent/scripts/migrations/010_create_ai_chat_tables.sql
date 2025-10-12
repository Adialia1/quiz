-- Migration 009: Create AI Chat Tables
-- Run this in Supabase SQL Editor
-- For "מרצה AI" feature

-- Chat Sessions
CREATE TABLE ai_chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Context
  topic TEXT,
  question_id UUID REFERENCES ai_generated_questions(id), -- If asking about specific question

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_message_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for chat_sessions
CREATE INDEX idx_chat_sessions_user ON ai_chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_created ON ai_chat_sessions(created_at DESC);

-- Chat Messages
CREATE TABLE ai_chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,

  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for chat_messages
CREATE INDEX idx_chat_messages_session ON ai_chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON ai_chat_messages(created_at DESC);
CREATE INDEX idx_chat_messages_session_created ON ai_chat_messages(session_id, created_at);

-- Trigger to update last_message_at in sessions
CREATE OR REPLACE FUNCTION update_session_last_message()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE ai_chat_sessions
  SET last_message_at = NEW.created_at
  WHERE id = NEW.session_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_last_message
AFTER INSERT ON ai_chat_messages
FOR EACH ROW EXECUTE FUNCTION update_session_last_message();

-- Verify tables were created
SELECT 'Migration 009 completed successfully - ai_chat_sessions and ai_chat_messages tables created' AS status;
