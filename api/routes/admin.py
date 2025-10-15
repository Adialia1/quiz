"""
Admin API Routes

Admin-only endpoints for data ingestion and management
Requires authentication token with admin privileges
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Depends
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import tempfile
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from agent.ingestion.ocr_utils import GeminiOCR
from agent.ingestion.semantic_chunking import SemanticChunker
from agent.agents.legal_expert import LegalExpertAgent
from agent.ingestion.llm_exam_parser import LLMExamParser
from supabase import create_client, Client
from api.auth import get_current_admin_user_id

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Router
router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class IngestLegalDocRequest(BaseModel):
    """Request to ingest legal documents"""
    document_name: str
    max_pages: Optional[int] = None


class IngestExamQuestionsRequest(BaseModel):
    """Request to ingest exam questions from JSON"""
    questions: List[dict]
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    use_enrichment: bool = True


class IngestConceptsRequest(BaseModel):
    """Request to ingest concepts"""
    concepts: List[dict]
    generate_embeddings: bool = True


class IngestionResponse(BaseModel):
    """Response from ingestion operations"""
    success: bool
    message: str
    total_processed: int
    total_inserted: int
    errors: List[str] = []


# ============================================================================
# LEGAL DOCUMENTS INGESTION
# ============================================================================

@router.post("/ingest/legal-docs", response_model=IngestionResponse)
async def ingest_legal_document(
    file: UploadFile = File(...),
    max_pages: Optional[int] = None,
    admin_user_id: str = Depends(get_current_admin_user_id)
):
    """
    Ingest a legal document PDF

    Performs OCR, semantic chunking, and generates embeddings

    Requires: Bearer token with admin privileges

    Example:
    ```bash
    curl -X POST "http://localhost:8000/api/admin/ingest/legal-docs" \\
         -H "Authorization: Bearer <clerk-token>" \\
         -F "file=@legal_doc.pdf" \\
         -F "max_pages=10"
    ```
    """

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Initialize ingestion pipeline
        ocr = GeminiOCR()
        chunker = SemanticChunker()

        pdf_name = Path(file.filename).stem

        # Step 1: OCR
        print(f"[1/3] OCR Processing {pdf_name}...")
        ocr_result = ocr.process_document(tmp_path, max_pages)

        # Step 2: Semantic Chunking
        print(f"[2/3] Semantic Chunking...")
        chunks = chunker.chunk_with_embeddings(ocr_result['full_document'])

        # Step 3: Prepare and insert to Supabase
        print(f"[3/3] Inserting {len(chunks)} chunks to database...")

        supabase_records = []
        for chunk in chunks:
            approx_page = min(
                chunk['chunk_index'] // (len(chunks) // ocr_result['total_pages'] + 1) + 1,
                ocr_result['total_pages']
            )

            record = {
                'document_name': pdf_name,
                'page_number': approx_page,
                'chunk_index': chunk['chunk_index'],
                'content': chunk['content'],
                'embedding': chunk['embedding'],
                'metadata': {
                    'char_count': chunk['char_count'],
                    'word_count': chunk['word_count'],
                    'token_count_approx': chunk['token_count_approx'],
                    'total_pages': ocr_result['total_pages'],
                    'file_name': file.filename
                }
            }
            supabase_records.append(record)

        # Insert to Supabase
        response = supabase.table('legal_doc_chunks').insert(supabase_records).execute()

        # Clean up temp file
        os.unlink(tmp_path)

        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {pdf_name}",
            total_processed=ocr_result['total_pages'],
            total_inserted=len(supabase_records),
            errors=[]
        )

    except Exception as e:
        # Clean up temp file if exists
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass

        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# ============================================================================
# EXAM QUESTIONS INGESTION
# ============================================================================

@router.post("/ingest/exam-questions/json", response_model=IngestionResponse)
async def ingest_exam_questions_json(
    request: IngestExamQuestionsRequest,
    admin_user_id: str = Depends(get_current_admin_user_id)
):
    """
    Ingest exam questions from JSON

    Validates questions, optionally enriches with legal context, generates embeddings

    Requires: Bearer token with admin privileges

    Request body:
    ```json
    {
      "questions": [
        {
          "question": "מהו מידע פנים?",
          "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
          "correct_answer": "B",
          "explanation": "...",
          "topic": "מידע פנים",
          "difficulty": "medium"
        }
      ],
      "topic": "Securities Law",
      "difficulty": "medium",
      "use_enrichment": true
    }
    ```
    """

    try:
        questions = request.questions

        # Validate questions
        valid_questions = []
        errors = []

        for i, q in enumerate(questions):
            required_fields = ['question', 'options', 'correct_answer']
            missing_fields = [f for f in required_fields if f not in q]

            if missing_fields:
                errors.append(f"Question {i+1}: Missing fields {missing_fields}")
                continue

            # Validate options
            if not isinstance(q['options'], dict):
                errors.append(f"Question {i+1}: Options must be a dictionary")
                continue

            required_options = ['A', 'B', 'C', 'D', 'E']
            missing_options = [opt for opt in required_options if opt not in q['options']]

            if missing_options:
                errors.append(f"Question {i+1}: Missing options {missing_options}")
                continue

            # Validate correct answer
            if q['correct_answer'] not in required_options:
                errors.append(f"Question {i+1}: Invalid correct_answer")
                continue

            # Apply defaults
            if request.topic and not q.get('topic'):
                q['topic'] = request.topic
            if request.difficulty and not q.get('difficulty'):
                q['difficulty'] = request.difficulty

            valid_questions.append(q)

        if not valid_questions:
            raise HTTPException(status_code=400, detail="No valid questions found")

        # Enrich with legal expert if requested
        if request.use_enrichment:
            print(f"Enriching {len(valid_questions)} questions with legal context...")
            legal_expert = LegalExpertAgent(use_thinking_model=True, top_k=15)

            for i, q in enumerate(valid_questions):
                if q.get('explanation') and q.get('topic') and q.get('legal_reference'):
                    continue

                try:
                    enrichment = legal_expert.enrich_exam_question(
                        question_text=q['question'],
                        options=q['options'],
                        correct_answer=q['correct_answer']
                    )

                    q['explanation'] = enrichment.get('explanation', q.get('explanation'))
                    q['topic'] = enrichment.get('topic', q.get('topic'))
                    q['difficulty'] = enrichment.get('difficulty', q.get('difficulty', 'medium'))
                    q['legal_reference'] = enrichment.get('legal_reference', q.get('legal_reference'))

                except Exception as e:
                    errors.append(f"Question {i+1}: Enrichment failed - {str(e)}")

        # Generate embeddings
        print(f"Generating embeddings for {len(valid_questions)} questions...")
        chunker = SemanticChunker()

        supabase_records = []
        for q in valid_questions:
            # Create embedding text
            embedding_text = ' | '.join([
                q['question'],
                q['options']['A'], q['options']['B'], q['options']['C'],
                q['options']['D'], q['options']['E'],
                q.get('explanation', ''),
                f"נושא: {q.get('topic', '')}"
            ])

            # Generate embedding
            embedding = chunker.encoder([embedding_text])[0]
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else embedding

            # Prepare record
            record = {
                'question_text': q['question'],
                'option_a': q['options']['A'],
                'option_b': q['options']['B'],
                'option_c': q['options']['C'],
                'option_d': q['options']['D'],
                'option_e': q['options']['E'],
                'correct_answer': q['correct_answer'],
                'explanation': q.get('explanation'),
                'topic': q.get('topic'),
                'difficulty': q.get('difficulty', 'medium'),
                'legal_reference': q.get('legal_reference'),
                'embedding': embedding_list,
                'metadata': {
                    'source': 'api_upload',
                    'enriched': request.use_enrichment
                }
            }
            supabase_records.append(record)

        # Insert to Supabase
        print(f"Inserting {len(supabase_records)} questions to database...")
        response = supabase.table('exam_questions').insert(supabase_records).execute()

        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {len(supabase_records)} questions",
            total_processed=len(questions),
            total_inserted=len(supabase_records),
            errors=errors
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/exam-questions/pdf", response_model=IngestionResponse)
async def ingest_exam_questions_pdf(
    file: UploadFile = File(...),
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    use_enrichment: bool = True,
    admin_user_id: str = Depends(get_current_admin_user_id)
):
    """
    Ingest exam questions from PDF

    Uses LLM to parse PDF and extract questions, then validates and enriches

    Requires: Bearer token with admin privileges

    Example:
    ```bash
    curl -X POST "http://localhost:8000/api/admin/ingest/exam-questions/pdf" \\
         -H "Authorization: Bearer <clerk-token>" \\
         -F "file=@exam.pdf" \\
         -F "topic=Securities Law" \\
         -F "difficulty=medium"
    ```
    """

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Parse PDF
        print(f"Parsing PDF: {file.filename}...")
        parser = LLMExamParser()
        valid_questions, validation_report = parser.extract_and_validate(
            tmp_path,
            use_llm_validation=True
        )

        # Clean up temp file
        os.unlink(tmp_path)

        if not valid_questions:
            raise HTTPException(
                status_code=400,
                detail=f"No valid questions found in PDF. Report: {validation_report}"
            )

        # Format questions
        formatted_questions = []
        for q in valid_questions:
            formatted_questions.append({
                'question': q.get('question_text', ''),
                'options': q.get('options', {}),
                'correct_answer': q.get('correct_answer', ''),
                'topic': topic,
                'difficulty': difficulty or 'medium',
                'source': file.filename
            })

        # Use the JSON ingestion endpoint logic
        request = IngestExamQuestionsRequest(
            questions=formatted_questions,
            topic=topic,
            difficulty=difficulty,
            use_enrichment=use_enrichment
        )

        return await ingest_exam_questions_json(request, admin_user_id)

    except HTTPException:
        raise
    except Exception as e:
        # Clean up temp file if exists
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass

        raise HTTPException(status_code=500, detail=f"PDF ingestion failed: {str(e)}")


# ============================================================================
# CONCEPTS INGESTION
# ============================================================================

@router.post("/ingest/concepts", response_model=IngestionResponse)
async def ingest_concepts(
    request: IngestConceptsRequest,
    admin_user_id: str = Depends(get_current_admin_user_id)
):
    """
    Ingest concepts into the database

    Validates concepts and optionally generates embeddings for semantic search

    Requires: Bearer token with admin privileges

    Request body:
    ```json
    {
      "concepts": [
        {
          "topic": "מידע פנים",
          "title": "הגדרת מידע פנים",
          "explanation": "...",
          "example": "...",
          "key_points": ["נקודה 1", "נקודה 2"],
          "source_document": "חוק ניירות ערך",
          "source_page": "42"
        }
      ],
      "generate_embeddings": true
    }
    ```
    """

    try:
        concepts = request.concepts

        # Validate concepts
        valid_concepts = []
        errors = []

        for i, concept in enumerate(concepts):
            required_fields = ['topic', 'title', 'explanation']
            missing_fields = [f for f in required_fields if not concept.get(f)]

            if missing_fields:
                errors.append(f"Concept {i+1}: Missing fields {missing_fields}")
                continue

            valid_concepts.append(concept)

        if not valid_concepts:
            raise HTTPException(status_code=400, detail="No valid concepts found")

        # Generate embeddings if requested
        if request.generate_embeddings:
            print(f"Generating embeddings for {len(valid_concepts)} concepts...")
            chunker = SemanticChunker()

            texts = []
            for concept in valid_concepts:
                text = f"{concept.get('title', '')} {concept.get('explanation', '')}"
                texts.append(text)

            embeddings = chunker.encoder(texts)

            for i, concept in enumerate(valid_concepts):
                embedding = embeddings[i]
                concept['embedding'] = embedding.tolist() if hasattr(embedding, 'tolist') else embedding

        # Prepare records for Supabase
        supabase_records = []
        for concept in valid_concepts:
            record = {
                'topic': concept.get('topic', 'לא ידוע'),
                'title': concept.get('title', 'ללא כותרת'),
                'explanation': concept.get('explanation', ''),
                'example': concept.get('example', ''),
                'key_points': concept.get('key_points', []),
                'source_document': concept.get('source_document', ''),
                'source_page': concept.get('source_page', ''),
                'raw_content': concept.get('raw_content', '')
            }

            if 'embedding' in concept:
                record['embedding'] = concept['embedding']

            supabase_records.append(record)

        # Insert to Supabase in batches
        print(f"Inserting {len(supabase_records)} concepts to database...")
        batch_size = 50
        total_inserted = 0

        for i in range(0, len(supabase_records), batch_size):
            batch = supabase_records[i:i + batch_size]
            try:
                response = supabase.table('concepts').insert(batch).execute()
                total_inserted += len(batch)
            except Exception as e:
                errors.append(f"Batch {i//batch_size + 1}: {str(e)}")

        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {total_inserted} concepts",
            total_processed=len(concepts),
            total_inserted=total_inserted,
            errors=errors
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# ============================================================================
# ADMIN UTILITIES
# ============================================================================

@router.get("/stats")
async def get_admin_stats(
    admin_user_id: str = Depends(get_current_admin_user_id)
):
    """
    Get database statistics

    Returns counts and statistics for all data tables

    Requires: Bearer token with admin privileges
    """

    try:
        stats = {}

        # Legal documents
        result = supabase.table('legal_doc_chunks').select('id', count='exact').execute()
        stats['legal_doc_chunks'] = result.count

        # Exam questions
        result = supabase.table('exam_questions').select('id', count='exact').execute()
        stats['exam_questions'] = result.count

        # AI generated questions
        result = supabase.table('ai_generated_questions').select('id', count='exact').execute()
        stats['ai_generated_questions'] = result.count

        # Concepts
        result = supabase.table('concepts').select('id', count='exact').execute()
        stats['concepts'] = result.count

        # Users
        result = supabase.table('users').select('id', count='exact').execute()
        stats['users'] = result.count

        # Exams
        result = supabase.table('exams').select('id', count='exact').execute()
        stats['exams'] = result.count

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")
