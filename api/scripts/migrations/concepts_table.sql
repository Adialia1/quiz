-- Create concepts table (simplified - without Hebrew text search)
CREATE TABLE IF NOT EXISTS concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    title TEXT NOT NULL,
    explanation TEXT NOT NULL,
    example TEXT,
    key_points JSONB DEFAULT '[]'::jsonb,
    source_document TEXT,
    source_page TEXT,
    raw_content TEXT,
    embedding VECTOR(1024),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS concepts_topic_idx ON concepts(topic);

-- Create index for vector similarity search (requires pgvector extension)
CREATE INDEX IF NOT EXISTS concepts_embedding_idx
ON concepts
USING hnsw (embedding vector_cosine_ops);

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_concepts(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    filter_topic TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    topic TEXT,
    title TEXT,
    explanation TEXT,
    example TEXT,
    key_points JSONB,
    source_document TEXT,
    source_page TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        concepts.id,
        concepts.topic,
        concepts.title,
        concepts.explanation,
        concepts.example,
        concepts.key_points,
        concepts.source_document,
        concepts.source_page,
        1 - (concepts.embedding <=> query_embedding) AS similarity
    FROM concepts
    WHERE (filter_topic IS NULL OR concepts.topic = filter_topic)
        AND 1 - (concepts.embedding <=> query_embedding) > match_threshold
    ORDER BY concepts.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
