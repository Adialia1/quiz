"""
Configuration settings for AI Ethica backend system
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
LEGAL_DOCS_DIR = BASE_DIR / "legal_documents"
EXAM_QUESTIONS_DIR = BASE_DIR / "exam_questions"

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Embeddings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
EMBEDDING_DIMENSION = 1024  # multilingual-e5-large dimension

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "quiz-legal-docs")

# LLM Configuration
GEMINI_MODEL = "google/gemini-2.0-flash-001"  # Best for Hebrew OCR
GEMINI_MAX_TOKENS = 10000
GEMINI_TEMPERATURE = 0.0  # Deterministic for OCR

#Thinking Configuration
THINKING_MODEL = "google/gemini-2.5-pro"
THINKING_MAX_TOKENS = 10000
THINKING_TEMPERATURE = 0.5

# Chunking Configuration
CHUNK_METHOD = "statistical"  # statistical or consecutive
STATISTICAL_THRESHOLD = "auto"  # auto-tuning
CONSECUTIVE_THRESHOLD = 0.3

# RAG Configuration
RAG_TOP_K = 5  # Number of chunks to retrieve
RAG_SCORE_THRESHOLD = 0.7  # Minimum similarity score

# OCR Configuration
OCR_DPI = 300  # High quality for Hebrew text
OCR_MAX_PAGES = None  # None = process all pages
OCR_RATE_LIMIT_DELAY = 0.5  # seconds between API calls

# Performance thresholds
MASTERY_THRESHOLD = 0.8  # 80% accuracy = mastery
CONSECUTIVE_CORRECT_TO_REMOVE = 2  # Remove question after 2 correct answers
SPACED_REPETITION_MIN_HOURS = 24  # Don't show same question within 24h

# Question difficulty weights
DIFFICULTY_WEIGHTS = {
    "easy": 1.0,
    "medium": 1.5,
    "hard": 2.0
}

# Topic coverage for exams
EXAM_QUESTION_COUNT = 25
MIN_QUESTIONS_PER_TOPIC = 2

# Validation
def validate_config():
    """Validate required configuration is present"""
    required = {
        "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return True
