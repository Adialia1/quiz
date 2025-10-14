"""
Ingest Concepts to Supabase

This script takes the concepts_dataset.json and ingests it into Supabase:
1. Creates the 'concepts' table (if not exists)
2. Inserts all concepts with their explanations
3. Generates embeddings for semantic search (optional)

Usage:
    python scripts/ingest_concepts_to_supabase.py --input concepts_dataset.json
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import argparse
from typing import List, Dict, Any
from tqdm import tqdm
from supabase import create_client, Client
from semantic_router.encoders import HuggingFaceEncoder

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY, EMBEDDING_MODEL


def create_concepts_table(supabase: Client):
    """
    Create the concepts table in Supabase

    Table structure:
    - id: UUID
    - topic: TEXT
    - title: TEXT
    - explanation: TEXT
    - example: TEXT
    - key_points: TEXT[] or JSONB
    - source_document: TEXT
    - source_page: TEXT
    - raw_content: TEXT (optional, for full content)
    - embedding: VECTOR(1024) (optional, for semantic search)
    - created_at: TIMESTAMPTZ
    """
    print("\n📄 Creating 'concepts' table...")

    sql = """
    -- Create concepts table
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
    CREATE INDEX IF NOT EXISTS concepts_title_idx ON concepts USING gin(to_tsvector('hebrew', title));
    CREATE INDEX IF NOT EXISTS concepts_explanation_idx ON concepts USING gin(to_tsvector('hebrew', explanation));

    -- Create index for vector similarity search (if pgvector enabled)
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
    """

    try:
        # Note: Cannot execute raw SQL via Python client easily
        # User should run this SQL via Supabase SQL Editor
        print("⚠️  Please run the following SQL in Supabase SQL Editor:")
        print("-" * 70)
        print(sql)
        print("-" * 70)
        print("\nOr the table might already exist. Continuing with insertion...")

    except Exception as e:
        print(f"⚠️  Note: {e}")
        print("Continuing anyway (table might already exist)...")


def generate_embeddings(
    concepts: List[Dict[str, Any]],
    encoder: HuggingFaceEncoder
) -> List[Dict[str, Any]]:
    """
    Generate embeddings for all concepts

    Args:
        concepts: List of concepts
        encoder: HuggingFaceEncoder for generating embeddings

    Returns:
        Concepts with embeddings added
    """
    print("\n🧠 Generating embeddings for concepts...")

    # Prepare texts for embedding (title + explanation)
    texts = []
    for concept in concepts:
        text = f"{concept.get('title', '')} {concept.get('explanation', '')}"
        texts.append(text)

    # Generate embeddings in batches
    print(f"   Encoding {len(texts)} concepts...")
    embeddings = encoder(texts)

    # Add embeddings to concepts
    for i, concept in enumerate(concepts):
        embedding = embeddings[i]
        # Convert to list
        concept['embedding'] = embedding.tolist() if hasattr(embedding, 'tolist') else embedding

    print("   ✅ Embeddings generated")
    return concepts


def insert_concepts_to_supabase(
    supabase: Client,
    concepts: List[Dict[str, Any]],
    batch_size: int = 50
):
    """
    Insert concepts into Supabase in batches

    Args:
        supabase: Supabase client
        concepts: List of concepts to insert
        batch_size: Number of concepts per batch
    """
    print(f"\n💾 Inserting {len(concepts)} concepts to Supabase...")

    # Prepare data for insertion
    insert_data = []

    for concept in concepts:
        record = {
            'topic': concept.get('topic', 'לא ידוע'),
            'title': concept.get('title', 'ללא כותרת'),
            'explanation': concept.get('explanation', ''),
            'example': concept.get('example', ''),
            'key_points': concept.get('key_points', []),
            'source_document': concept.get('source_document', ''),
            'source_page': concept.get('source_page', ''),
            'raw_content': concept.get('raw_content', ''),
        }

        # Add embedding if available
        if 'embedding' in concept:
            record['embedding'] = concept['embedding']

        insert_data.append(record)

    # Insert in batches
    total_inserted = 0

    for i in tqdm(range(0, len(insert_data), batch_size), desc="Inserting"):
        batch = insert_data[i:i + batch_size]

        try:
            result = supabase.table("concepts").insert(batch).execute()
            total_inserted += len(batch)
        except Exception as e:
            print(f"\n❌ Error inserting batch {i//batch_size + 1}: {e}")
            print(f"   Sample record: {batch[0] if batch else 'N/A'}")
            # Continue with next batch

    print(f"\n✅ Successfully inserted {total_inserted}/{len(concepts)} concepts")


def main():
    parser = argparse.ArgumentParser(description='Ingest concepts to Supabase')
    parser.add_argument(
        '--input',
        type=str,
        default='concepts_dataset.json',
        help='Input JSON file with concepts'
    )
    parser.add_argument(
        '--skip-embeddings',
        action='store_true',
        help='Skip generating embeddings (faster, but no semantic search)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Batch size for insertion (default: 50)'
    )
    parser.add_argument(
        '--create-table',
        action='store_true',
        help='Show SQL to create table'
    )

    args = parser.parse_args()

    print("="*70)
    print("🚀 Concept Ingestion to Supabase")
    print("="*70)

    # Initialize Supabase client
    print("\n🔧 Connecting to Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Connected to Supabase")

    # Show table creation SQL if requested
    if args.create_table:
        create_concepts_table(supabase)
        print("\n⚠️  Please run the SQL above in Supabase SQL Editor, then re-run this script without --create-table")
        return

    # Load concepts dataset
    print(f"\n📂 Loading concepts from {args.input}...")

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    concepts = data.get('concepts', [])
    metadata = data.get('metadata', {})

    print(f"✅ Loaded {len(concepts)} concepts")
    print(f"   Topics: {metadata.get('total_topics', 'Unknown')}")
    print(f"   Enriched: {metadata.get('enriched', 'Unknown')}")

    # Generate embeddings if not skipped
    if not args.skip_embeddings:
        print("\n🧠 Initializing encoder for embeddings...")
        encoder = HuggingFaceEncoder(name=EMBEDDING_MODEL)
        concepts = generate_embeddings(concepts, encoder)
    else:
        print("\n⏭️  Skipping embeddings (--skip-embeddings flag)")

    # Insert to Supabase
    insert_concepts_to_supabase(supabase, concepts, batch_size=args.batch_size)

    # Summary
    print("\n" + "="*70)
    print("✅ INGESTION COMPLETE")
    print("="*70)
    print(f"Total concepts in database: {len(concepts)}")
    print(f"Embeddings included: {not args.skip_embeddings}")
    print("="*70)


if __name__ == "__main__":
    main()
