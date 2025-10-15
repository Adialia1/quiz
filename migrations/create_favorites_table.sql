-- Create favorite_concepts table
CREATE TABLE IF NOT EXISTS favorite_concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, concept_id)
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_favorite_concepts_user_id ON favorite_concepts(user_id);
CREATE INDEX IF NOT EXISTS idx_favorite_concepts_concept_id ON favorite_concepts(concept_id);

-- Enable RLS
ALTER TABLE favorite_concepts ENABLE ROW LEVEL SECURITY;

-- Create policy for users to manage their own favorites
CREATE POLICY "Users can manage their own favorites"
    ON favorite_concepts
    FOR ALL
    USING (true)
    WITH CHECK (true);
