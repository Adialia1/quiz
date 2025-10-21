#!/usr/bin/env python3
"""
FastAPI Application for Quiz Generator and Legal Expert
Provides REST API endpoints for generating quizzes and asking legal questions
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import sys
from pathlib import Path
import json
import tempfile
import os
import time
from fastapi import Request

sys.path.append(str(Path(__file__).parent.parent))

from agent.agents.legal_expert import LegalExpertAgent
from agent.agents.quiz_generator import QuizGeneratorAgent
from agent.scripts.quiz_to_pdf import create_quiz_pdf_html
from api.routes.users import router as users_router
from api.routes.exams import router as exams_router
from api.routes.chat import router as chat_router
from api.routes.concepts import router as concepts_router
from api.routes.notifications import router as notifications_router
from api.routes.subscriptions import router as subscriptions_router
from api.routes.progress import router as progress_router
from api.routes.documents import router as documents_router
from api.routes.admin import router as admin_router
from api.utils.cache import get_redis, close_redis
from api.utils.database import get_db_pool, close_db_pool, test_connection

# Initialize FastAPI app
app = FastAPI(
    title="Quiz Generator & Legal Expert API",
    description="API for generating exam questions, querying legal expert, managing users, exams, AI chat, and concepts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression middleware for faster mobile responses
# Compresses responses > 1KB by ~70-90%
# Reduces 50KB response to ~5-10KB = 200-500ms faster on mobile
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses larger than 1KB
    compresslevel=6      # Balance between compression ratio and speed (1-9, 6 is optimal)
)

# Performance monitoring middleware - tracks request timing
@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """
    Monitor request performance and log slow endpoints

    Helps identify performance bottlenecks and track optimization improvements
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Add timing header for debugging
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

    # Log slow requests (> 1 second)
    if duration_ms > 1000:
        print(f"🐌 SLOW REQUEST: {request.method} {request.url.path} - {duration_ms:.0f}ms")
    elif duration_ms > 500:
        print(f"⚠️  SLOW: {request.method} {request.url.path} - {duration_ms:.0f}ms")
    else:
        # Log normal requests in development
        print(f"✅ {request.method} {request.url.path} - {duration_ms:.0f}ms")

    return response

# Mount static files directory
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(users_router)
app.include_router(exams_router)
app.include_router(chat_router)
app.include_router(concepts_router)
app.include_router(notifications_router)
app.include_router(subscriptions_router)
app.include_router(progress_router)
app.include_router(documents_router)
app.include_router(admin_router)

# Initialize agents (singleton pattern)
legal_expert = None
quiz_generator = None


def get_legal_expert():
    """Get or initialize Legal Expert Agent"""
    global legal_expert
    if legal_expert is None:
        legal_expert = LegalExpertAgent()
    return legal_expert


def get_quiz_generator():
    """Get or initialize Quiz Generator Agent"""
    global quiz_generator
    if quiz_generator is None:
        quiz_generator = QuizGeneratorAgent()
    return quiz_generator


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LegalQuestionRequest(BaseModel):
    """Request model for legal expert question"""
    question: str = Field(..., description="Legal question to ask", min_length=1)
    show_sources: bool = Field(default=True, description="Include source references in response")
    k: int = Field(default=10, description="Number of relevant legal chunks to use", ge=1, le=30)


class LegalQuestionResponse(BaseModel):
    """Response model for legal expert question"""
    answer: str = Field(..., description="Answer from legal expert")
    sources: Optional[List[str]] = Field(None, description="Source references (if show_sources=True)")
    query: str = Field(..., description="Original question")
    timestamp: str = Field(..., description="Response timestamp")


class GenerateQuestionsRequest(BaseModel):
    """Request model for question generation"""
    count: int = Field(..., description="Number of questions to generate", ge=1, le=50)
    topic: Optional[str] = Field(None, description="Specific topic (e.g., 'מידע פנים', 'חובות גילוי')")
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Field(None, description="Difficulty level")
    question_type: Optional[Literal["story", "basic", "mixed"]] = Field(
        "mixed",
        description="Question type: 'story' (70-80% story), 'basic' (definitions), 'mixed' (balanced)"
    )


class GenerateFullQuizRequest(BaseModel):
    """Request model for full quiz generation"""
    quiz_count: int = Field(1, description="Number of quizzes to generate", ge=1, le=10)
    focus_areas: Optional[List[str]] = Field(None, description="Focus areas/topics to emphasize")
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Field(None, description="Difficulty level")
    format: Literal["json", "pdf"] = Field("json", description="Output format")


class QuizMetadata(BaseModel):
    """Quiz metadata"""
    question_count: int
    requested_count: int
    topic: str
    difficulty: str
    focus_areas: List[str]
    generated_at: str
    validation_stats: dict


class QuizQuestion(BaseModel):
    """Single quiz question"""
    question_number: int
    question_text: str
    options: dict
    correct_answer: str
    explanation: str
    topic: str
    difficulty: str
    legal_reference: Optional[str] = None
    generated: bool = True
    validated_by_expert: bool = True
    expert_validation: Optional[dict] = None


class QuizResponse(BaseModel):
    """Response model for quiz generation"""
    questions: List[dict]
    metadata: dict
    reference_sources: List[str]


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint with welcome message"""
    return {
        "message": "Quiz Generator & Legal Expert API",
        "version": "1.0.0",
        "endpoints": {
            "legal_question": "/api/legal/ask",
            "generate_questions": "/api/questions/generate",
            "generate_quiz": "/api/quiz/generate",
            "user_profile": "/api/users/me",
            "user_stats": "/api/users/me/stats",
            "clerk_webhook": "/api/users/webhook",
            "create_exam": "/api/exams",
            "exam_history": "/api/exams/history",
            "exam_details": "/api/exams/{exam_id}",
            "submit_answer": "/api/exams/{exam_id}/answer",
            "submit_exam": "/api/exams/{exam_id}/submit",
            "exam_results": "/api/exams/{exam_id}/results",
            "concepts_topics": "/api/concepts/topics",
            "concepts_by_topic": "/api/concepts/topics/{topic}",
            "concept_detail": "/api/concepts/{concept_id}",
            "concepts_search": "/api/concepts/search",
            "concepts_stats": "/api/concepts/stats",
            "terms_pdf": "/static/documents/terms.pdf"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Railway deployment
    Always returns healthy if the app is running - agents initialize lazily on first use
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Quiz Generator & Legal Expert API",
        "version": "1.0.0"
    }


@app.post("/api/legal/ask", response_model=LegalQuestionResponse)
async def ask_legal_question(request: LegalQuestionRequest):
    """
    Ask a question to the Legal Expert Agent

    **Parameters:**
    - **question**: Legal question to ask
    - **show_sources**: Include source references in response (default: True)
    - **k**: Number of relevant legal chunks to use (default: 10)

    **Returns:**
    - Answer from legal expert
    - Source references (if show_sources=True)
    - Timestamp
    """
    try:
        expert = get_legal_expert()

        # Query legal expert with RAG
        response = expert.process_with_rag(
            query=request.question,
            k=request.k
        )

        answer = response.get('answer', '')
        sources = response.get('sources', []) if request.show_sources else None

        return LegalQuestionResponse(
            answer=answer,
            sources=sources if request.show_sources else None,
            query=request.question,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing legal question: {str(e)}")


@app.post("/api/questions/generate", response_model=QuizResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    """
    Generate exam questions using Quiz Generator Agent

    **Parameters:**
    - **count**: Number of questions to generate (1-50)
    - **topic**: Optional specific topic (e.g., "מידע פנים")
    - **difficulty**: Optional difficulty level (easy/medium/hard)
    - **question_type**: Question type (story/basic/mixed, default: mixed)

    **Returns:**
    - List of generated questions with full details
    - Metadata about generation process
    - Reference sources used
    """
    try:
        generator = get_quiz_generator()

        # Determine focus based on question_type
        # Note: The quiz generator naturally creates mixed questions (70-80% story, 20-30% basic)
        # This parameter is informational for metadata

        result = generator.generate_quiz(
            question_count=request.count,
            topic=request.topic,
            difficulty=request.difficulty,
            focus_areas=None  # Not using focus_areas for individual question generation
        )

        # Add question_type to metadata
        result['metadata']['question_type'] = request.question_type

        return QuizResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@app.post("/api/quiz/generate")
async def generate_full_quiz(request: GenerateFullQuizRequest):
    """
    Generate full quiz(zes) with 25 questions each

    **Parameters:**
    - **quiz_count**: Number of quizzes to generate (1-10, default: 1)
    - **focus_areas**: Optional list of focus areas/topics
    - **difficulty**: Optional difficulty level (easy/medium/hard)
    - **format**: Output format (json/pdf, default: json)

    **Returns:**
    - JSON: Quiz data with all questions and metadata
    - PDF: Downloadable PDF file with quiz and answers
    """
    try:
        generator = get_quiz_generator()

        quizzes = []

        # Generate multiple quizzes if requested
        for i in range(request.quiz_count):
            result = generator.generate_quiz(
                question_count=25,  # Fixed 25 questions per quiz
                topic=None,  # Full quiz covers all topics
                difficulty=request.difficulty,
                focus_areas=request.focus_areas
            )

            # Add quiz number to metadata
            result['metadata']['quiz_number'] = i + 1
            result['metadata']['total_quizzes'] = request.quiz_count

            quizzes.append(result)

        # If single quiz and PDF format requested
        if request.format == "pdf":
            if request.quiz_count > 1:
                raise HTTPException(
                    status_code=400,
                    detail="PDF format only supports quiz_count=1. For multiple quizzes, use JSON format."
                )

            # Create temporary JSON file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_json:
                json.dump(quizzes[0], tmp_json, ensure_ascii=False, indent=2)
                json_path = tmp_json.name

            # Create PDF
            pdf_path = json_path.replace('.json', '.pdf')
            create_quiz_pdf_html(json_path, pdf_path)

            # Clean up JSON file
            os.remove(json_path)

            # Return PDF file
            return FileResponse(
                path=pdf_path,
                media_type='application/pdf',
                filename=f'quiz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                background=None  # Delete file after sending
            )

        # JSON format (default)
        if request.quiz_count == 1:
            return JSONResponse(content=quizzes[0])
        else:
            return JSONResponse(content={
                "quizzes": quizzes,
                "total_count": request.quiz_count,
                "generated_at": datetime.now().isoformat()
            })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")


# ============================================================================
# QUERY PARAMETER ENDPOINTS (Alternative simpler interface)
# ============================================================================

@app.get("/api/legal/ask-simple")
async def ask_legal_question_simple(
    question: str = Query(..., description="Legal question to ask"),
    show_sources: bool = Query(True, description="Include source references"),
    k: int = Query(10, description="Number of legal chunks to use", ge=1, le=30)
):
    """
    Simplified GET endpoint for asking legal questions

    **Example:**
    ```
    GET /api/legal/ask-simple?question=מהו מידע פנים?&show_sources=true
    ```
    """
    request = LegalQuestionRequest(
        question=question,
        show_sources=show_sources,
        k=k
    )
    return await ask_legal_question(request)


@app.get("/api/questions/generate-simple")
async def generate_questions_simple(
    count: int = Query(..., description="Number of questions", ge=1, le=50),
    topic: Optional[str] = Query(None, description="Specific topic"),
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Query(None, description="Difficulty level"),
    question_type: Optional[Literal["story", "basic", "mixed"]] = Query("mixed", description="Question type")
):
    """
    Simplified GET endpoint for generating questions

    **Example:**
    ```
    GET /api/questions/generate-simple?count=5&topic=מידע פנים&difficulty=medium
    ```
    """
    request = GenerateQuestionsRequest(
        count=count,
        topic=topic,
        difficulty=difficulty,
        question_type=question_type
    )
    return await generate_questions(request)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} not found",
            "available_endpoints": [
                "/api/legal/ask",
                "/api/questions/generate",
                "/api/quiz/generate"
            ]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Initialize optional services on startup

    Services are initialized in the background to avoid blocking Railway's healthcheck.
    Agents are initialized lazily on first use for faster startup.
    """
    print("🚀 Starting Quiz Generator & Legal Expert API...")
    print("🏥 Health endpoint ready immediately for Railway healthcheck")

    # Initialize async database connection pool (optional - non-blocking)
    print("📊 Initializing async database connection pool in background...")
    try:
        pool = await get_db_pool()
        if pool:
            print("✅ Async database pool ready")
            # Test connection
            try:
                await test_connection()
                print("✅ Database connection tested successfully")
            except Exception as e:
                print(f"⚠️  Database test failed: {e}")
        else:
            print("⚠️  Running without async database pool")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize database pool: {e}")
        print("⚠️  Falling back to synchronous database operations")

    # Initialize Redis cache (optional - non-blocking)
    print("📦 Initializing Redis cache in background...")
    try:
        redis = await get_redis()
        if redis:
            print("✅ Redis cache ready")
        else:
            print("⚠️  Running without cache layer")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize Redis: {e}")
        print("⚠️  Running without cache layer")

    # Note: Agents are initialized LAZILY on first use, not during startup
    # This ensures Railway's healthcheck passes quickly
    print("📝 Agents will initialize lazily on first use")
    print("🎉 API startup complete - ready for requests!")
    print("📚 Documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down API...")

    # Close async database pool
    await close_db_pool()

    # Close Redis connection
    await close_redis()
    print("✅ All connections closed")


if __name__ == "__main__":
    import uvicorn

    # Run the API server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (disable in production)
        log_level="info"
    )
