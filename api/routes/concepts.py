"""
Concepts API Routes
Provides endpoints for accessing legal concepts and rules flashcards
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from semantic_router.encoders import HuggingFaceEncoder

# Load environment variables
load_dotenv()

router = APIRouter(
    prefix="/api/concepts",
    tags=["Concepts"]
)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

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
    user_id: str
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
    Get all topics with optional concept counts

    Returns list of topics organized hierarchically
    """
    try:
        # Get all unique topics with counts
        result = supabase.rpc(
            'get_concepts_by_topic',
            {}
        ).execute()

        if result.data:
            return result.data

        # Fallback: manual query
        concepts_result = supabase.table("concepts")\
            .select("topic")\
            .execute()

        # Count concepts per topic
        topic_counts = {}
        for concept in concepts_result.data:
            topic = concept['topic']
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        topics = [
            TopicGroup(
                topic=topic,
                concept_count=count
            )
            for topic, count in sorted(topic_counts.items())
        ]

        return topics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching topics: {str(e)}")


@router.get("/topics/{topic}", response_model=List[Concept])
async def get_concepts_by_topic(
    topic: str,
    limit: int = Query(100, ge=1, le=500, description="Max concepts to return")
):
    """
    Get all concepts for a specific topic

    **Parameters:**
    - **topic**: Topic name (e.g., "מידע פנים")
    - **limit**: Maximum concepts to return (default: 100)
    """
    try:
        result = supabase.table("concepts")\
            .select("*")\
            .eq("topic", topic)\
            .limit(limit)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail=f"No concepts found for topic: {topic}")

        concepts = [Concept(**concept) for concept in result.data]
        return concepts

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching concepts: {str(e)}")


@router.get("/{concept_id}", response_model=Concept)
async def get_concept_by_id(concept_id: str):
    """
    Get a specific concept by ID

    **Parameters:**
    - **concept_id**: Concept UUID
    """
    try:
        result = supabase.table("concepts")\
            .select("*")\
            .eq("id", concept_id)\
            .single()\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail=f"Concept not found: {concept_id}")

        return Concept(**result.data)

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
    """
    try:
        if request.use_semantic:
            # Semantic search using vector embeddings
            encoder = get_encoder()

            # Generate query embedding
            query_embedding = encoder([request.query])[0]

            # Search using match_concepts function
            result = supabase.rpc(
                'match_concepts',
                {
                    'query_embedding': query_embedding.tolist(),
                    'match_threshold': 0.6,  # Lower threshold for broader results
                    'match_count': request.limit,
                    'filter_topic': request.topic
                }
            ).execute()

            if result.data:
                search_results = [
                    SearchResult(
                        concept=Concept(**{
                            'id': item['id'],
                            'topic': item['topic'],
                            'title': item['title'],
                            'explanation': item['explanation'],
                            'example': item.get('example'),
                            'key_points': item.get('key_points', []),
                            'source_document': item.get('source_document'),
                            'source_page': item.get('source_page')
                        }),
                        similarity=item.get('similarity'),
                        relevance='high' if item.get('similarity', 0) > 0.8 else 'medium' if item.get('similarity', 0) > 0.7 else 'low'
                    )
                    for item in result.data
                ]
                return search_results

        # Fallback: Text search on title and explanation
        query = supabase.table("concepts").select("*")

        if request.topic:
            query = query.eq("topic", request.topic)

        # Use ilike for case-insensitive search
        query = query.or_(
            f"title.ilike.%{request.query}%,explanation.ilike.%{request.query}%"
        )

        query = query.limit(request.limit)
        result = query.execute()

        if result.data:
            search_results = [
                SearchResult(
                    concept=Concept(**concept),
                    similarity=None,
                    relevance='medium'
                )
                for concept in result.data
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
    """
    try:
        # Use PostgreSQL random() function
        query = supabase.table("concepts").select("*")

        if topic:
            query = query.eq("topic", topic)

        # Note: Supabase doesn't support order by random() directly
        # Workaround: Get all IDs and pick random ones
        all_ids_result = query.select("id").execute()

        if not all_ids_result.data:
            return []

        import random
        all_ids = [item['id'] for item in all_ids_result.data]
        random_ids = random.sample(all_ids, min(count, len(all_ids)))

        # Fetch full concepts
        result = supabase.table("concepts")\
            .select("*")\
            .in_("id", random_ids)\
            .execute()

        return [Concept(**concept) for concept in result.data]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching random concepts: {str(e)}")


@router.get("/stats")
async def get_concepts_stats():
    """
    Get statistics about concepts database

    **Returns:**
    - Total concepts count
    - Topics count
    - Concepts per topic breakdown
    """
    try:
        # Get total count
        total_result = supabase.table("concepts")\
            .select("id", count="exact")\
            .execute()

        total_count = total_result.count if hasattr(total_result, 'count') else len(total_result.data)

        # Get topics
        topics_result = supabase.table("concepts")\
            .select("topic")\
            .execute()

        # Count per topic
        topic_counts = {}
        for concept in topics_result.data:
            topic = concept['topic']
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return {
            "total_concepts": total_count,
            "total_topics": len(topic_counts),
            "topics": [
                {"topic": topic, "count": count}
                for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            "timestamp": datetime.now().isoformat()
        }

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
    - **user_id**: User ID (from Clerk)
    - **concept_id**: Concept UUID
    """
    try:
        # Check if concept exists
        concept_check = supabase.table("concepts")\
            .select("id")\
            .eq("id", request.concept_id)\
            .single()\
            .execute()

        if not concept_check.data:
            raise HTTPException(status_code=404, detail="Concept not found")

        # Add to favorites (will handle duplicates via UNIQUE constraint)
        result = supabase.table("favorite_concepts")\
            .insert({
                "user_id": request.user_id,
                "concept_id": request.concept_id
            })\
            .execute()

        return {"success": True, "message": "נוסף למועדפים"}

    except HTTPException:
        raise
    except Exception as e:
        # Handle duplicate key error gracefully
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            return {"success": True, "message": "כבר קיים במועדפים"}
        raise HTTPException(status_code=500, detail=f"Error adding favorite: {str(e)}")


@router.delete("/favorites/{user_id}/{concept_id}")
async def remove_favorite(user_id: str, concept_id: str):
    """
    Remove a concept from user's favorites

    **Parameters:**
    - **user_id**: User ID (from Clerk)
    - **concept_id**: Concept UUID
    """
    try:
        result = supabase.table("favorite_concepts")\
            .delete()\
            .eq("user_id", user_id)\
            .eq("concept_id", concept_id)\
            .execute()

        return {"success": True, "message": "הוסר מהמועדפים"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing favorite: {str(e)}")


@router.get("/favorites/{user_id}", response_model=List[Concept])
async def get_user_favorites(user_id: str):
    """
    Get all favorite concepts for a user

    **Parameters:**
    - **user_id**: User ID (from Clerk)

    **Returns:**
    - List of favorite concepts with full concept data
    """
    try:
        # Get favorites with joined concept data
        result = supabase.table("favorite_concepts")\
            .select("*, concepts(*)")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()

        if not result.data:
            return []

        # Extract concepts from joined data
        concepts = [Concept(**item['concepts']) for item in result.data if item.get('concepts')]
        return concepts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching favorites: {str(e)}")


@router.get("/favorites/{user_id}/check/{concept_id}")
async def check_favorite(user_id: str, concept_id: str):
    """
    Check if a concept is in user's favorites

    **Parameters:**
    - **user_id**: User ID (from Clerk)
    - **concept_id**: Concept UUID

    **Returns:**
    - Boolean indicating if concept is favorited
    """
    try:
        result = supabase.table("favorite_concepts")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("concept_id", concept_id)\
            .execute()

        return {"is_favorite": len(result.data) > 0}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking favorite: {str(e)}")
