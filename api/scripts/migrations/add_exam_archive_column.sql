-- Add is_archived column to exams table
-- This allows users to hide exams from their history without deleting them

ALTER TABLE exams
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- Create index for faster queries when filtering archived exams
CREATE INDEX IF NOT EXISTS idx_exams_is_archived
ON exams(user_id, is_archived, started_at DESC);

-- Comment
COMMENT ON COLUMN exams.is_archived IS 'Whether this exam has been archived by the user';
