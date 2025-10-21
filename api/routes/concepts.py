"""
Concepts API Routes
Provides endpoints for accessing legal concepts and rules flashcards

OPTIMIZED: Week 2 - Migrated to async database queries + embedding caching
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import random
import hashlib
from dotenv import load_dotenv
from semantic_router.encoders import HuggingFaceEncoder
from api.utils.cache import get_cached, set_cached, CacheTTL
from api.utils.database import fetch_one, fetch_all, execute_query, fetch_val

# Load environment variables
load_dotenv()

router = APIRouter(
    prefix="/api/concepts",
    tags=["Concepts"]
)

# Configuration
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

# Initialize encoder for semantic search (lazy loading)
_encoder = None

def get_encoder():
    """Get or initialize encoder for semantic search"""
    global _encoder
    if _encoder is None:
        _encoder = HuggingFaceEncoder(name=EMBEDDING_MODEL)
    return _encoder


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class Concept(BaseModel):
    """Concept model"""
    id: str
    topic: str
    title: str
    explanation: str
    example: Optional[str] = None
    key_points: List[str] = []
    source_document: Optional[str] = None
    source_page: Optional[str] = None
    created_at: Optional[str] = None


class TopicGroup(BaseModel):
    """Topic with concept count"""
    topic: str
    concept_count: int
    concepts: Optional[List[Concept]] = None


class SearchResult(BaseModel):
    """Search result with relevance score"""
    concept: Concept
    similarity: Optional[float] = None
    relevance: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., min_length=1)
    topic: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)
    use_semantic: bool = Field(default=True, description="Use semantic search with embeddings")


class FavoriteRequest(BaseModel):
    """Favorite request"""
    clerk_user_id: str  # Clerk user ID (e.g., "user_...")
    concept_id: str


class FavoriteConcept(BaseModel):
    """Favorite concept with full concept data"""
    id: str
    user_id: str
    concept_id: str
    created_at: str
    concept: Concept


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/topics", response_model=List[TopicGroup])
async def get_all_topics(
    include_counts: bool = Query(True, description="Include concept counts per topic")
):
    """
    Get all topics with optional concept counts (with caching)

    Returns list of topics organized hierarchically
    Cache: 1 hour TTL

    OPTIMIZED: Async database queries + caching
    """
    try:
        # Try to get from cache
        cache_key = "concepts:topics:all"
        cached_topics = await get_cached(cache_key)

        if cached_topics:
            print("✅ Cache HIT: Concept topics")
            return [TopicGroup(**t) for t in cached_topics]

        print("❌ Cache MISS: Concept topics")

        # Get all concepts grouped by topic (async)
        topics = await fetch_all(
            """
            SELECT topic, COUNT(*) as concept_count
            FROM concepts
            GROUP BY topic
            ORDER BY topic
            """
        )

        topics_data = [
            {
                "topic": t["topic"],
                "concept_count": t["concept_count"]
            }
            for t in topics
        ]

        # Cache for 1 hour
        await set_cached(cache_key, topics_data, ttl_seconds=CacheTTL.LONG)

        return [TopicGroup(**t) for t in topics_data]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching topics: {str(e)}")


@router.get("/topics/{topic}", response_model=List[Concept])
async def get_concepts_by_topic(
    topic: str,
    limit: int = Query(100, ge=1, le=500, description="Max concepts to return")
):
    """
    Get all concepts for a specific topic (with caching)

    **Parameters:**
    - **topic**: Topic name (e.g., "מידע פנים")
    - **limit**: Maximum concepts to return (default: 100)

    Cache: 1 hour TTL

    OPTIMIZED: Async database query + Redis caching
    """
    try:
        # Try to get from cache
        cache_key = f"concepts:topic:{topic}:{limit}"
        cached_concepts = await get_cached(cache_key)

        if cached_concepts:
            print(f"✅ Cache HIT: Concepts for topic '{topic}'")
            return [Concept(**c) for c in cached_concepts]

        print(f"❌ Cache MISS: Concepts for topic '{topic}'")

        # Async SELECT
        concepts = await fetch_all(
            "SELECT * FROM concepts WHERE topic = $1 LIMIT $2",
            topic, limit
        )

        if not concepts:
            raise HTTPException(status_code=404, detail=f"No concepts found for topic: {topic}")

        # Convert to list of Concept objects with proper type conversion
        concept_objects = []
        for concept in concepts:
            # Convert types for Pydantic
            concept_data = {
                'id': str(concept['id']),  # Convert UUID to string
                'topic': concept['topic'],
                'title': concept['title'],
                'explanation': concept['explanation'],
                'example': concept.get('example'),
                'key_points': concept.get('key_points') if isinstance(concept.get('key_points'), list) else [],
                'source_document': concept.get('source_document'),
                'source_page': concept.get('source_page'),
                'created_at': concept.get('created_at').isoformat() if concept.get('created_at') else None
            }
            concept_objects.append(Concept(**concept_data))

        # Convert to dict for caching
        concepts_data = []
        for c in concept_objects:
            try:
                # Try Pydantic v2 first
                concepts_data.append(c.model_dump())
            except AttributeError:
                # Fallback to Pydantic v1
                concepts_data.append(c.dict())

        # Cache for 1 hour
        await set_cached(cache_key, concepts_data, ttl_seconds=CacheTTL.LONG)

        return concept_objects

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching concepts for topic '{topic}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching concepts: {str(e)}")


@router.get("/{concept_id}", response_model=Concept)
async def get_concept_by_id(concept_id: str):
    """
    Get a specific concept by ID

    **Parameters:**
    - **concept_id**: Concept UUID

    OPTIMIZED: Async database query
    """
    try:
        # Async SELECT
        concept = await fetch_one(
            "SELECT * FROM concepts WHERE id = $1",
            concept_id
        )

        if not concept:
            raise HTTPException(status_code=404, detail=f"Concept not found: {concept_id}")

        # Convert types for Pydantic
        concept_data = {
            'id': str(concept['id']),  # Convert UUID to string
            'topic': concept['topic'],
            'title': concept['title'],
            'explanation': concept['explanation'],
            'example': concept.get('example'),
            'key_points': concept.get('key_points') if isinstance(concept.get('key_points'), list) else [],
            'source_document': concept.get('source_document'),
            'source_page': concept.get('source_page'),
            'created_at': concept.get('created_at').isoformat() if concept.get('created_at') else None
        }

        return Concept(**concept_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching concept: {str(e)}")


@router.post("/search", response_model=List[SearchResult])
async def search_concepts(request: SearchRequest):
    """
    Smart search for concepts using semantic similarity and text search

    **Parameters:**
    - **query**: Search query in Hebrew
    - **topic**: Optional topic filter
    - **limit**: Max results to return (default: 10)
    - **use_semantic**: Use semantic search with embeddings (default: true)

    **Returns:**
    - List of matching concepts with relevance scores

    OPTIMIZED: Async database queries + embedding caching (Week 2)
    """
    try:
        if request.use_semantic:
            # Semantic search using vector embeddings
            encoder = get_encoder()

            # Check embedding cache first (Week 2 optimization)
            embedding_key = f"embedding:{hashlib.md5(request.query.encode()).hexdigest()}"
            cached_embedding = await get_cached(embedding_key)

            if cached_embedding:
                print(f"✅ Cache HIT: Embedding for query '{request.query[:20]}...'")
                query_embedding = cached_embedding
            else:
                print(f"❌ Cache MISS: Embedding for query '{request.query[:20]}...'")
                # Generate query embedding (300-800ms)
                embedding_result = encoder([request.query])[0]

                # Convert to list if it's a numpy array, otherwise use as-is
                if hasattr(embedding_result, 'tolist'):
                    query_embedding = embedding_result.tolist()
                else:
                    query_embedding = embedding_result if isinstance(embedding_result, list) else list(embedding_result)

                # Cache embedding for 7 days (embeddings don't change)
                await set_cached(embedding_key, query_embedding, ttl_seconds=CacheTTL.WEEK)

            # Convert embedding to PostgreSQL array format string
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            # Build query with optional topic filter
            if request.topic:
                results = await fetch_all(
                    """
                    SELECT *,
                           (embedding <=> $1::vector) AS distance,
                           1 - (embedding <=> $1::vector) AS similarity
                    FROM concepts
                    WHERE topic = $2
                    AND (embedding <=> $1::vector) < $3
                    ORDER BY embedding <=> $1::vector
                    LIMIT $4
                    """,
                    embedding_str, request.topic, 0.4, request.limit  # 0.4 distance = 0.6 similarity
                )
            else:
                results = await fetch_all(
                    """
                    SELECT *,
                           (embedding <=> $1::vector) AS distance,
                           1 - (embedding <=> $1::vector) AS similarity
                    FROM concepts
                    WHERE (embedding <=> $1::vector) < $2
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                    """,
                    embedding_str, 0.4, request.limit
                )

            if results:
                search_results = []
                for item in results:
                    # Convert types for Pydantic
                    concept_data = {
                        'id': str(item['id']),  # Convert UUID to string
                        'topic': item['topic'],
                        'title': item['title'],
                        'explanation': item['explanation'],
                        'example': item.get('example'),
                        'key_points': item.get('key_points') if isinstance(item.get('key_points'), list) else [],
                        'source_document': item.get('source_document'),
                        'source_page': item.get('source_page')
                    }

                    search_results.append(
                        SearchResult(
                            concept=Concept(**concept_data),
                            similarity=float(item.get('similarity', 0)) if item.get('similarity') is not None else None,
                            relevance='high' if item.get('similarity', 0) > 0.8 else 'medium' if item.get('similarity', 0) > 0.7 else 'low'
                        )
                    )
                return search_results

        # Fallback: Text search on title and explanation (async)
        if request.topic:
            results = await fetch_all(
                """
                SELECT * FROM concepts
                WHERE topic = $1
                AND (title ILIKE $2 OR explanation ILIKE $2)
                LIMIT $3
                """,
                request.topic, f"%{request.query}%", request.limit
            )
        else:
            results = await fetch_all(
                """
                SELECT * FROM concepts
                WHERE title ILIKE $1 OR explanation ILIKE $1
                LIMIT $2
                """,
                f"%{request.query}%", request.limit
            )

        if results:
            search_results = [
                SearchResult(
                    concept=Concept(**concept),
                    similarity=None,
                    relevance='medium'
                )
                for concept in results
            ]
            return search_results

        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching concepts: {str(e)}")


@router.get("/search/simple")
async def search_concepts_simple(
    query: str = Query(..., min_length=1, description="Search query"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    use_semantic: bool = Query(True, description="Use semantic search")
):
    """
    Simplified GET endpoint for searching concepts

    **Example:**
    ```
    GET /api/concepts/search/simple?query=מידע פנים&limit=5
    ```
    """
    request = SearchRequest(
        query=query,
        topic=topic,
        limit=limit,
        use_semantic=use_semantic
    )
    return await search_concepts(request)


@router.get("/random")
async def get_random_concepts(
    count: int = Query(5, ge=1, le=20, description="Number of random concepts"),
    topic: Optional[str] = Query(None, description="Filter by topic")
):
    """
    Get random concepts for study/practice

    **Parameters:**
    - **count**: Number of random concepts (default: 5)
    - **topic**: Optional topic filter

    OPTIMIZED: Async database query with PostgreSQL random()
    """
    try:
        # Use PostgreSQL TABLESAMPLE or ORDER BY random()
        if topic:
            results = await fetch_all(
                """
                SELECT * FROM concepts
                WHERE topic = $1
                ORDER BY random()
                LIMIT $2
                """,
                topic, count
            )
        else:
            results = await fetch_all(
                "SELECT * FROM concepts ORDER BY random() LIMIT $1",
                count
            )

        return [Concept(**concept) for concept in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching random concepts: {str(e)}")


@router.get("/stats")
async def get_concepts_stats():
    """
    Get statistics about concepts database (with caching)

    **Returns:**
    - Total concepts count
    - Topics count
    - Concepts per topic breakdown

    Cache: 1 hour TTL

    OPTIMIZED: Async database queries + caching
    """
    try:
        # Try to get from cache
        cache_key = "concepts:stats"
        cached_stats = await get_cached(cache_key)

        if cached_stats:
            print("✅ Cache HIT: Concept stats")
            return cached_stats

        print("❌ Cache MISS: Concept stats")

        # Get total count (async)
        total_count = await fetch_val("SELECT COUNT(*) FROM concepts")

        # Get topics with counts (async)
        topics = await fetch_all(
            """
            SELECT topic, COUNT(*) as count
            FROM concepts
            GROUP BY topic
            ORDER BY count DESC
            """
        )

        stats_data = {
            "total_concepts": total_count,
            "total_topics": len(topics),
            "topics": [
                {"topic": t["topic"], "count": t["count"]}
                for t in topics
            ],
            "timestamp": datetime.now().isoformat()
        }

        # Cache for 1 hour
        await set_cached(cache_key, stats_data, ttl_seconds=CacheTTL.LONG)

        return stats_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


# ============================================================================
# FAVORITES API ENDPOINTS
# ============================================================================

@router.post("/favorites", response_model=dict)
async def add_favorite(request: FavoriteRequest):
    """
    Add a concept to user's favorites

    **Parameters:**
    - **clerk_user_id**: User ID (from Clerk)
    - **concept_id**: Concept UUID

    OPTIMIZED: Async database queries
    """
    try:
        # Convert Clerk user ID to internal database user ID
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(request.clerk_user_id)
        user_id = str(user["id"])

        # Check if concept exists (async)
        concept = await fetch_one(
            "SELECT id FROM concepts WHERE id = $1",
            request.concept_id
        )

        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")

        # Add to favorites (async) - duplicates handled by UNIQUE constraint
        try:
            await execute_query(
                """
                INSERT INTO favorite_concepts (user_id, concept_id)
                VALUES ($1, $2)
                """,
                user_id, request.concept_id
            )
            return {"success": True, "message": "נוסף למועדפים"}
        except Exception as e:
            # Handle duplicate key error gracefully
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                return {"success": True, "message": "כבר קיים במועדפים"}
            raise

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding favorite: {str(e)}")


@router.delete("/favorites/{clerk_user_id}/{concept_id}")
async def remove_favorite(clerk_user_id: str, concept_id: str):
    """
    Remove a concept from user's favorites

    **Parameters:**
    - **clerk_user_id**: User ID (from Clerk)
    - **concept_id**: Concept UUID

    OPTIMIZED: Async database query
    """
    try:
        # Convert Clerk user ID to internal database user ID
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(clerk_user_id)
        user_id = str(user["id"])

        # Async DELETE
        await execute_query(
            """
            DELETE FROM favorite_concepts
            WHERE user_id = $1 AND concept_id = $2
            """,
            user_id, concept_id
        )

        return {"success": True, "message": "הוסר מהמועדפים"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing favorite: {str(e)}")


@router.get("/favorites/{clerk_user_id}", response_model=List[Concept])
async def get_user_favorites(clerk_user_id: str):
    """
    Get all favorite concepts for a user

    **Parameters:**
    - **clerk_user_id**: User ID from Clerk (e.g., "user_...")

    **Returns:**
    - List of favorite concepts with full concept data

    OPTIMIZED: Async database query with JOIN
    """
    try:
        # Convert Clerk user ID to internal database user ID
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(clerk_user_id)
        user_id = str(user["id"])

        # Get favorites with joined concept data (async)
        results = await fetch_all(
            """
            SELECT c.*
            FROM favorite_concepts fc
            JOIN concepts c ON fc.concept_id = c.id
            WHERE fc.user_id = $1
            ORDER BY fc.created_at DESC
            """,
            user_id
        )

        # Convert types for Pydantic
        concept_objects = []
        for concept in results:
            concept_data = {
                'id': str(concept['id']),  # Convert UUID to string
                'topic': concept['topic'],
                'title': concept['title'],
                'explanation': concept['explanation'],
                'example': concept.get('example'),
                'key_points': concept.get('key_points') if isinstance(concept.get('key_points'), list) else [],
                'source_document': concept.get('source_document'),
                'source_page': concept.get('source_page'),
                'created_at': concept.get('created_at').isoformat() if concept.get('created_at') else None
            }
            concept_objects.append(Concept(**concept_data))

        return concept_objects

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching favorites: {str(e)}")


@router.get("/favorites/{clerk_user_id}/check/{concept_id}")
async def check_favorite(clerk_user_id: str, concept_id: str):
    """
    Check if a concept is in user's favorites

    **Parameters:**
    - **clerk_user_id**: User ID from Clerk (e.g., "user_...")
    - **concept_id**: Concept UUID

    **Returns:**
    - Boolean indicating if concept is favorited

    OPTIMIZED: Async database query
    """
    try:
        # Convert Clerk user ID to internal database user ID
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(clerk_user_id)
        user_id = str(user["id"])

        # Check if favorite exists (async)
        count = await fetch_val(
            """
            SELECT COUNT(*)
            FROM favorite_concepts
            WHERE user_id = $1 AND concept_id = $2
            """,
            user_id, concept_id
        )

        return {"is_favorite": count > 0}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking favorite: {str(e)}")
