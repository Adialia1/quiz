-- Database functions for concepts API

-- Function to get concepts grouped by topic with counts
CREATE OR REPLACE FUNCTION get_concepts_by_topic()
RETURNS TABLE (
    topic TEXT,
    concept_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        concepts.topic,
        COUNT(*)::BIGINT as concept_count
    FROM concepts
    GROUP BY concepts.topic
    ORDER BY concepts.topic;
END;
$$;
