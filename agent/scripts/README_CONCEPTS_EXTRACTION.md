# Concepts Extraction & Ingestion Guide

## Overview

This guide explains how to extract all concepts and rules from the legal RAG system and ingest them into Supabase for the "מושגים וחוקים" (Concepts and Rules) feature.

## 🎯 Process Flow

```
1. Get all topics from database
   ↓
2. For each topic → Query legal_expert with MAX top_k (200)
   ↓
3. Extract ALL rules/concepts/sub-concepts
   ↓
4. For each concept → Get detailed explanation from legal_expert
   ↓
5. Generate embeddings for semantic search
   ↓
6. Ingest to Supabase 'concepts' table
```

## 📦 Step-by-Step Instructions

### Step 1: Extract Concepts

```bash
cd /Users/adialia/Desktop/quiz

# Full extraction (all topics, with enrichment)
python agent/scripts/extract_all_concepts.py \
  --output concepts_dataset.json \
  --max-top-k 200

# Test mode (limit to 3 topics)
python agent/scripts/extract_all_concepts.py \
  --output concepts_test.json \
  --max-top-k 200 \
  --limit-topics 3

# Fast mode (skip enrichment)
python agent/scripts/extract_all_concepts.py \
  --output concepts_raw.json \
  --max-top-k 200 \
  --skip-enrichment
```

**Expected Output:**
```json
{
  "metadata": {
    "total_concepts": 1500,
    "total_topics": 25,
    "max_top_k_used": 200,
    "enriched": true
  },
  "topics": ["מידע פנים", "חובות גילוי", ...],
  "concepts": [
    {
      "chunk_id": 0,
      "topic": "מידע פנים",
      "title": "הגדרת מידע פנים",
      "explanation": "מידע פנים הוא...",
      "example": "לדוגמה...",
      "key_points": ["נקודה 1", "נקודה 2"],
      "source_document": "חוק ניירות ערך",
      "source_page": "42",
      "raw_content": "המידע המלא..."
    },
    ...
  ]
}
```

### Step 2: Create Concepts Table in Supabase

```bash
# Show SQL for table creation
python agent/scripts/ingest_concepts_to_supabase.py --create-table
```

**Copy the SQL output and run it in Supabase SQL Editor:**

1. Go to Supabase Dashboard → SQL Editor
2. Paste the SQL
3. Run it

### Step 3: Ingest to Supabase

```bash
# Full ingestion (with embeddings for semantic search)
python agent/scripts/ingest_concepts_to_supabase.py \
  --input concepts_dataset.json \
  --batch-size 50

# Without embeddings (faster)
python agent/scripts/ingest_concepts_to_supabase.py \
  --input concepts_dataset.json \
  --skip-embeddings
```

## 🗄️ Database Schema

### Concepts Table

```sql
CREATE TABLE concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,                  -- "מידע פנים", "חובות גילוי"
    title TEXT NOT NULL,                  -- "הגדרת מידע פנים"
    explanation TEXT NOT NULL,            -- Full explanation
    example TEXT,                         -- Practical example
    key_points JSONB DEFAULT '[]'::jsonb, -- ["נקודה 1", "נקודה 2"]
    source_document TEXT,                 -- "חוק ניירות ערך"
    source_page TEXT,                     -- "42"
    raw_content TEXT,                     -- Full original content
    embedding VECTOR(1024),               -- For semantic search
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Indexes

- `concepts_topic_idx` - Fast topic filtering
- `concepts_title_idx` - Hebrew full-text search on titles
- `concepts_explanation_idx` - Hebrew full-text search on explanations
- `concepts_embedding_idx` - Vector similarity search (HNSW)

## 📱 App Integration

### Backend API Endpoint

Add to `/api/routes/concepts.py`:

```python
from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter(prefix="/api/concepts", tags=["Concepts"])

@router.get("/")
async def get_all_concepts(
    topic: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500)
):
    """
    Get all concepts, optionally filtered by topic or search query
    """
    query = supabase.table("concepts").select("*")

    if topic:
        query = query.eq("topic", topic)

    if search:
        # Full-text search on title and explanation
        query = query.or_(
            f"title.ilike.%{search}%,explanation.ilike.%{search}%"
        )

    query = query.limit(limit)
    result = query.execute()

    return {
        "concepts": result.data,
        "total": len(result.data)
    }

@router.get("/topics")
async def get_concept_topics():
    """Get list of all available topics"""
    result = supabase.rpc('get_concept_topics').execute()
    return {"topics": result.data}

@router.get("/{concept_id}")
async def get_concept_details(concept_id: str):
    """Get full details for a specific concept"""
    result = supabase.table("concepts")\
        .select("*")\
        .eq("id", concept_id)\
        .single()\
        .execute()

    return result.data

@router.get("/search/semantic")
async def semantic_search(
    query: str,
    topic: Optional[str] = None,
    limit: int = 10
):
    """
    Semantic search using vector embeddings
    Requires embeddings to be generated during ingestion
    """
    # Generate query embedding
    encoder = HuggingFaceEncoder(name=EMBEDDING_MODEL)
    query_embedding = encoder([query])[0]

    # Search using match_concepts function
    result = supabase.rpc(
        'match_concepts',
        {
            'query_embedding': query_embedding.tolist(),
            'match_threshold': 0.7,
            'match_count': limit,
            'filter_topic': topic
        }
    ).execute()

    return {
        "query": query,
        "results": result.data
    }
```

### React Native Store

Create `app/src/stores/conceptsStore.ts`:

```typescript
import { create } from 'zustand';
import { storage } from '../utils/storage';

interface Concept {
  id: string;
  topic: string;
  title: string;
  explanation: string;
  example?: string;
  key_points: string[];
  source_document?: string;
  source_page?: string;
}

interface ConceptsStore {
  concepts: Concept[];
  topics: string[];
  favorites: Set<string>;
  learned: Set<string>;
  isLoading: boolean;

  // Actions
  loadConcepts: () => Promise<void>;
  searchConcepts: (query: string) => Concept[];
  getConceptsByTopic: (topic: string) => Concept[];
  toggleFavorite: (id: string) => void;
  markAsLearned: (id: string) => void;
}

export const useConceptsStore = create<ConceptsStore>((set, get) => ({
  concepts: [],
  topics: [],
  favorites: new Set(JSON.parse(storage.getString('concept_favorites') || '[]')),
  learned: new Set(JSON.parse(storage.getString('concept_learned') || '[]')),
  isLoading: false,

  loadConcepts: async () => {
    set({ isLoading: true });

    try {
      // Try cache first
      const cached = storage.getString('concepts_cache');
      if (cached) {
        const data = JSON.parse(cached);
        set({ concepts: data.concepts, topics: data.topics });
      }

      // Fetch from API in background
      const response = await fetch(`${API_URL}/api/concepts`);
      const data = await response.json();

      set({
        concepts: data.concepts,
        topics: [...new Set(data.concepts.map((c: Concept) => c.topic))]
      });

      // Update cache
      storage.set('concepts_cache', JSON.stringify({
        concepts: data.concepts,
        topics: data.topics,
        timestamp: Date.now()
      }));

    } catch (error) {
      console.error('Error loading concepts:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  searchConcepts: (query: string) => {
    const { concepts } = get();
    const lowerQuery = query.toLowerCase();

    return concepts.filter(c =>
      c.title.toLowerCase().includes(lowerQuery) ||
      c.explanation.toLowerCase().includes(lowerQuery)
    );
  },

  getConceptsByTopic: (topic: string) => {
    return get().concepts.filter(c => c.topic === topic);
  },

  toggleFavorite: (id: string) => {
    const { favorites } = get();
    const newFavorites = new Set(favorites);

    if (newFavorites.has(id)) {
      newFavorites.delete(id);
    } else {
      newFavorites.add(id);
    }

    storage.set('concept_favorites', JSON.stringify([...newFavorites]));
    set({ favorites: newFavorites });
  },

  markAsLearned: (id: string) => {
    const { learned } = get();
    const newLearned = new Set(learned);
    newLearned.add(id);

    storage.set('concept_learned', JSON.stringify([...newLearned]));
    set({ learned: newLearned });
  }
}));
```

## 🔍 Search Integration

### "שאל את המרצה" Button

When user searches and no concept is found:

```typescript
// In ConceptsScreen.tsx
const handleSearch = async (query: string) => {
  const results = searchConcepts(query);

  if (results.length === 0) {
    // Show "שאל את המרצה" button
    setShowAskMentor(true);
    setMentorQuestion(query);
  } else {
    setSearchResults(results);
  }
};

const handleAskMentor = () => {
  // Navigate to AI Mentor with pre-filled question
  navigation.navigate('AIMentor', {
    initialQuestion: mentorQuestion
  });
};
```

## ⚙️ Configuration

### Environment Variables

Already configured in `.env`:
```bash
SUPABASE_URL=your_url
SUPABASE_SERVICE_KEY=your_key
```

### Script Options

**extract_all_concepts.py:**
- `--output` - Output JSON file (default: concepts_dataset.json)
- `--max-top-k` - Max chunks per topic (default: 200)
- `--skip-enrichment` - Skip AI enrichment (faster)
- `--limit-topics` - Limit topics for testing

**ingest_concepts_to_supabase.py:**
- `--input` - Input JSON file
- `--skip-embeddings` - Skip embedding generation
- `--batch-size` - Batch size for insertion (default: 50)
- `--create-table` - Show table creation SQL

## 🚀 Running the Full Pipeline

```bash
# 1. Extract all concepts (takes ~30-60 minutes)
python agent/scripts/extract_all_concepts.py \
  --output concepts_full.json \
  --max-top-k 200

# 2. Create table in Supabase
python agent/scripts/ingest_concepts_to_supabase.py --create-table
# (Copy SQL and run in Supabase SQL Editor)

# 3. Ingest to database
python agent/scripts/ingest_concepts_to_supabase.py \
  --input concepts_full.json \
  --batch-size 50

# 4. Done! Concepts are now in Supabase
```

## 📊 Expected Results

- **Topics:** ~20-30 topics
- **Concepts per topic:** ~50-150 concepts
- **Total concepts:** ~1000-3000 concepts
- **Extraction time:** 30-60 minutes
- **Ingestion time:** 5-10 minutes

## 🐛 Troubleshooting

### "Not enough chunks"
- Increase `--max-top-k` to 300 or 500

### "Insertion failed"
- Check Supabase table exists
- Verify network connection
- Reduce `--batch-size` to 25

### "Embeddings too slow"
- Use `--skip-embeddings` for faster ingestion
- Add embeddings later with separate script

### "Out of memory"
- Process topics in batches using `--limit-topics`
- Combine results manually

## 📝 Notes

- Run extraction during off-peak hours (takes time)
- Monitor legal_expert token usage
- Keep raw JSON backup before ingestion
- Test with `--limit-topics 3` first

## ✅ Next Steps

After ingestion:
1. Test API endpoints
2. Build React Native screens
3. Implement search UI
4. Add "שאל את המרצה" integration
5. Test on device
