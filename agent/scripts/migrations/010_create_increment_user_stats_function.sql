-- Create function to increment user statistics
-- This function is called after exam submission to update user counts

CREATE OR REPLACE FUNCTION increment_user_stats(
    p_user_id UUID,
    p_questions_answered INTEGER DEFAULT 0,
    p_exams_taken INTEGER DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET
        total_questions_answered = COALESCE(total_questions_answered, 0) + p_questions_answered,
        total_exams_taken = COALESCE(total_exams_taken, 0) + p_exams_taken,
        updated_at = NOW()
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT increment_user_stats('user-uuid-here'::UUID, 25, 1);
