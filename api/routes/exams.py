"""
Exam Management API Routes

Handles exam sessions, question delivery, answer submission, and results.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID
import os
from supabase import create_client, Client

from api.auth import get_current_user_id

router = APIRouter(prefix="/api/exams", tags=["Exams"])

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== Models ====================

class CreateExamRequest(BaseModel):
    exam_type: str = Field(..., description="Type of exam: practice, full_simulation, review_mistakes")
    question_count: Optional[int] = Field(25, description="Number of questions (default: 25)")
    topics: Optional[List[str]] = Field(None, description="Filter by specific topics. If not specified, uses adaptive selection based on weak topics")
    difficulty: Optional[str] = Field(None, description="Filter by difficulty: easy, medium, hard")

    class Config:
        json_schema_extra = {
            "example": {
                "exam_type": "practice",
                "question_count": 25,
                "topics": ["מידע פנים", "חובות גילוי"],
                "difficulty": "medium"
            }
        }


class QuestionResponse(BaseModel):
    id: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_e: str
    topic: str
    sub_topic: Optional[str]
    difficulty_level: str
    image_url: Optional[str]
    # Note: correct_answer and explanation NOT included until after submission


class PreviousAnswer(BaseModel):
    question_id: str
    user_answer: Optional[str]
    time_taken_seconds: int

class ExamResponse(BaseModel):
    exam_id: str
    exam_type: str
    total_questions: int
    questions: List[QuestionResponse]
    started_at: str
    time_limit_minutes: Optional[int] = None  # Computed based on exam_type, not stored in DB
    previous_answers: Optional[List[PreviousAnswer]] = None


class ExamDetailsResponse(BaseModel):
    id: str
    exam_type: str
    status: str
    started_at: str
    completed_at: Optional[str]
    total_questions: int
    answered_questions: int
    current_question: int
    time_limit_minutes: Optional[int]


class SubmitAnswerRequest(BaseModel):
    question_id: str
    user_answer: str = Field(..., description="A, B, C, D, or E")
    time_taken_seconds: int

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "uuid-here",
                "user_answer": "B",
                "time_taken_seconds": 45
            }
        }


class BatchAnswerRequest(BaseModel):
    answers: List[SubmitAnswerRequest]

    class Config:
        json_schema_extra = {
            "example": {
                "answers": [
                    {
                        "question_id": "uuid-1",
                        "user_answer": "A",
                        "time_taken_seconds": 45
                    },
                    {
                        "question_id": "uuid-2",
                        "user_answer": "C",
                        "time_taken_seconds": 32
                    }
                ]
            }
        }


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    immediate_feedback: bool = Field(description="True for practice mode, False for full simulation")


class SubmitExamResponse(BaseModel):
    exam_id: str
    score_percentage: float
    passed: bool
    correct_answers: int
    wrong_answers: int
    time_taken_seconds: int
    weak_topics: List[str]
    strong_topics: List[str]


class ExamHistoryItem(BaseModel):
    id: str
    exam_type: str
    status: str
    score_percentage: Optional[float]
    passed: Optional[bool]
    started_at: str
    completed_at: Optional[str]
    total_questions: int


class ExamHistoryResponse(BaseModel):
    exams: List[ExamHistoryItem]
    total_count: int
    average_score: Optional[float]


class DetailedQuestionResult(BaseModel):
    question_id: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_e: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    time_taken_seconds: int
    topic: str
    difficulty_level: str
    explanation: str


class ExamResultsResponse(BaseModel):
    exam: ExamDetailsResponse
    questions: List[DetailedQuestionResult]
    analytics: Dict


# ==================== Helper Functions ====================

def get_user_by_clerk_id(clerk_user_id: str):
    """Get user from database by Clerk user ID"""
    result = supabase.table("users").select("*").eq("clerk_user_id", clerk_user_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data


def get_user_weak_topics(user_id: str, limit: int = 5) -> List[str]:
    """
    Get user's weakest topics based on performance

    Returns list of topic names ordered by weakness (worst first)
    """
    # Get topic performance, ordered by accuracy (weakest first)
    result = supabase.table("user_topic_performance")\
        .select("topic, accuracy_percentage")\
        .eq("user_id", user_id)\
        .order("accuracy_percentage", desc=False)\
        .limit(limit)\
        .execute()

    if result.data:
        return [item['topic'] for item in result.data]

    # If user has no history, return empty list (will use random questions)
    return []


def select_questions_for_exam(
    question_count: int,
    topics: Optional[List[str]] = None,
    difficulty: Optional[str] = None,
    exam_type: str = "practice",
    user_id: str = None
) -> List[Dict]:
    """
    Select questions for an exam based on criteria

    Logic:
    - practice: Random questions (can repeat)
    - full_simulation: ONLY questions user has never seen before (fresh questions)
    - review_mistakes: Questions from user_mistakes table

    Adaptive Selection (when no topics specified):
    - 60-70% from user's weakest topics
    - 30-40% from all other topics (to discover new weak areas)
    """
    import random

    if exam_type == "review_mistakes" and user_id:
        # Get questions user got wrong
        query = supabase.table("user_mistakes")\
            .select("question_id, ai_generated_questions(*)")\
            .eq("user_id", user_id)\
            .eq("is_resolved", False)\
            .limit(question_count)

        result = query.execute()
        questions = [item['ai_generated_questions'] for item in result.data if item.get('ai_generated_questions')]
    else:
        # Get all questions user has seen (for full_simulation filtering)
        seen_question_ids = []
        if exam_type == "full_simulation" and user_id:
            # Get all question IDs from user's history
            history = supabase.table("user_question_history")\
                .select("question_id")\
                .eq("user_id", user_id)\
                .execute()
            seen_question_ids = [item['question_id'] for item in history.data]

        questions = []

        # ADAPTIVE SELECTION: If no topics specified, use smart topic selection
        if not topics and user_id:
            weak_topics = get_user_weak_topics(user_id, limit=5)

            if weak_topics:
                # 60% from weak topics, 40% from others
                weak_count = int(question_count * 0.6)
                other_count = question_count - weak_count

                # Get questions from weak topics
                weak_query = supabase.table("ai_generated_questions")\
                    .select("*")\
                    .eq("is_active", True)\
                    .in_("topic", weak_topics)

                if difficulty:
                    weak_query = weak_query.eq("difficulty_level", difficulty)

                if exam_type == "full_simulation" and seen_question_ids:
                    weak_query = weak_query.not_.in_("id", seen_question_ids)

                weak_query = weak_query.limit(weak_count * 2)
                weak_result = weak_query.execute()
                weak_questions = weak_result.data

                # Get questions from other topics
                other_query = supabase.table("ai_generated_questions")\
                    .select("*")\
                    .eq("is_active", True)\
                    .not_.in_("topic", weak_topics)

                if difficulty:
                    other_query = other_query.eq("difficulty_level", difficulty)

                if exam_type == "full_simulation" and seen_question_ids:
                    other_query = other_query.not_.in_("id", seen_question_ids)

                other_query = other_query.limit(other_count * 2)
                other_result = other_query.execute()
                other_questions = other_result.data

                # Randomly select from each pool
                selected_weak = random.sample(weak_questions, min(weak_count, len(weak_questions)))
                selected_other = random.sample(other_questions, min(other_count, len(other_questions)))

                # Combine and shuffle
                questions = selected_weak + selected_other
                random.shuffle(questions)

        # STANDARD SELECTION: Topics specified or no adaptive selection
        if not questions:
            query = supabase.table("ai_generated_questions")\
                .select("*")\
                .eq("is_active", True)

            if topics:
                query = query.in_("topic", topics)

            if difficulty:
                query = query.eq("difficulty_level", difficulty)

            # For full_simulation: exclude questions user has seen
            if exam_type == "full_simulation" and seen_question_ids:
                query = query.not_.in_("id", seen_question_ids)

            # Get more questions than needed for random selection
            query = query.limit(question_count * 3)
            result = query.execute()

            # Randomly select question_count questions
            questions = result.data
            if len(questions) > question_count:
                questions = random.sample(questions, question_count)

    if len(questions) < question_count:
        if exam_type == "full_simulation" and seen_question_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough fresh questions available. You've seen {len(seen_question_ids)} questions. "
                       f"Requested: {question_count}, Fresh available: {len(questions)}. "
                       f"Try reducing question count or selecting specific topics."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough questions available. Requested: {question_count}, Available: {len(questions)}"
            )

    return questions


def calculate_exam_results(exam_id: str, user_id: str) -> Dict:
    """Calculate comprehensive exam results"""
    # Get all answers for this exam
    answers = supabase.table("exam_question_answers")\
        .select("*, ai_generated_questions(*)")\
        .eq("exam_id", exam_id)\
        .execute()

    if not answers.data:
        raise HTTPException(status_code=404, detail="No answers found for this exam")

    total_questions = len(answers.data)
    correct_answers = sum(1 for a in answers.data if a['is_correct'])
    wrong_answers = total_questions - correct_answers
    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    passed = score_percentage >= 70  # 70% passing grade

    # Calculate time taken (handle None values)
    total_time = sum((a.get('time_taken_seconds') or 0) for a in answers.data)

    # Analyze topics
    topic_performance = {}
    for answer in answers.data:
        question = answer.get('ai_generated_questions')
        if question:
            topic = question['topic']
            if topic not in topic_performance:
                topic_performance[topic] = {'correct': 0, 'total': 0}
            topic_performance[topic]['total'] += 1
            if answer['is_correct']:
                topic_performance[topic]['correct'] += 1

    # Calculate accuracy per topic
    topic_accuracy = {
        topic: (stats['correct'] / stats['total']) * 100
        for topic, stats in topic_performance.items()
    }

    # Identify weak and strong topics
    weak_topics = [topic for topic, acc in topic_accuracy.items() if acc < 60]
    strong_topics = [topic for topic, acc in topic_accuracy.items() if acc >= 80]

    return {
        "score_percentage": round(score_percentage, 2),
        "passed": passed,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "time_taken_seconds": total_time,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "topic_accuracy": topic_accuracy
    }


# ==================== Endpoints ====================

@router.post("", response_model=ExamResponse)
async def create_exam(
    request: CreateExamRequest,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Create a new exam session

    Exam Types:
    - practice: Practice mode with immediate feedback
    - full_simulation: Simulation mode, no feedback until submission
    - review_mistakes: Review previously incorrect answers
    """
    # Get user from database
    user = get_user_by_clerk_id(clerk_user_id)

    # Validate exam type
    valid_types = ["practice", "full_simulation", "review_mistakes"]
    if request.exam_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exam_type. Must be one of: {valid_types}"
        )

    # Select questions
    questions = select_questions_for_exam(
        question_count=request.question_count or 20,
        topics=request.topics,
        difficulty=request.difficulty,
        exam_type=request.exam_type,
        user_id=user['id']
    )

    # Create exam record
    exam_data = {
        "user_id": user['id'],
        "exam_type": request.exam_type,
        "status": "in_progress",
        "started_at": datetime.now().isoformat(),
        "total_questions": len(questions)
    }

    exam_result = supabase.table("exams").insert(exam_data).execute()
    exam = exam_result.data[0]

    # Link questions to exam
    for idx, question in enumerate(questions):
        link_data = {
            "exam_id": exam['id'],
            "question_id": question['id'],
            "question_order": idx + 1
        }
        supabase.table("exam_question_answers").insert(link_data).execute()

    # Prepare response (without correct answers or explanations)
    question_responses = [
        QuestionResponse(
            id=q['id'],
            question_text=q['question_text'],
            option_a=q['option_a'],
            option_b=q['option_b'],
            option_c=q['option_c'],
            option_d=q['option_d'],
            option_e=q['option_e'],
            topic=q['topic'],
            sub_topic=q.get('sub_topic'),
            difficulty_level=q['difficulty_level'],
            image_url=q.get('image_url')
        )
        for q in questions
    ]

    # Determine time limit based on exam type (for frontend timer)
    time_limit = None
    if exam['exam_type'] == "full_simulation":
        time_limit = 60  # 60 minutes for full simulation

    return ExamResponse(
        exam_id=exam['id'],
        exam_type=exam['exam_type'],
        total_questions=exam['total_questions'],
        questions=question_responses,
        started_at=exam['started_at'],
        time_limit_minutes=time_limit
    )


@router.get("/history", response_model=ExamHistoryResponse)
async def get_exam_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None, description="Filter by exam type"),
    clerk_user_id: str = Depends(get_current_user_id)
):
    """Get user's exam history"""
    user = get_user_by_clerk_id(clerk_user_id)

    # Build query
    query = supabase.table("exams")\
        .select("*")\
        .eq("user_id", user['id'])\
        .order("started_at", desc=True)

    if type:
        query = query.eq("exam_type", type)

    # Get total count
    count_result = supabase.table("exams")\
        .select("id", count="exact")\
        .eq("user_id", user['id'])

    if type:
        count_result = count_result.eq("exam_type", type)

    count_result = count_result.execute()
    total_count = count_result.count

    # Get paginated results
    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    # Calculate average score
    completed_exams = [e for e in result.data if e.get('score_percentage') is not None]
    average_score = None
    if completed_exams:
        average_score = sum(e['score_percentage'] for e in completed_exams) / len(completed_exams)

    # Format response
    exams = [
        ExamHistoryItem(
            id=exam['id'],
            exam_type=exam['exam_type'],
            status=exam['status'],
            score_percentage=exam.get('score_percentage'),
            passed=exam.get('passed'),
            started_at=exam['started_at'],
            completed_at=exam.get('completed_at'),
            total_questions=exam['total_questions']
        )
        for exam in result.data
    ]

    return ExamHistoryResponse(
        exams=exams,
        total_count=total_count,
        average_score=round(average_score, 2) if average_score else None
    )


@router.get("/{exam_id}")
async def get_exam(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """Get exam details and progress. Returns full exam session if in_progress, otherwise details only."""
    user = get_user_by_clerk_id(clerk_user_id)

    # Get exam
    exam = supabase.table("exams")\
        .select("*")\
        .eq("id", exam_id)\
        .eq("user_id", user['id'])\
        .single()\
        .execute()

    if not exam.data:
        raise HTTPException(status_code=404, detail="Exam not found")

    # If exam is in progress, return full session with questions
    if exam.data['status'] == "in_progress":
        # Get all questions for this exam
        exam_questions = supabase.table("exam_question_answers")\
            .select("*, ai_generated_questions(*)")\
            .eq("exam_id", exam_id)\
            .order("question_order")\
            .execute()

        questions = [
            QuestionResponse(
                id=eq['question_id'],
                question_text=eq['ai_generated_questions']['question_text'],
                option_a=eq['ai_generated_questions']['option_a'],
                option_b=eq['ai_generated_questions']['option_b'],
                option_c=eq['ai_generated_questions']['option_c'],
                option_d=eq['ai_generated_questions']['option_d'],
                option_e=eq['ai_generated_questions']['option_e'],
                topic=eq['ai_generated_questions']['topic'],
                sub_topic=eq['ai_generated_questions'].get('sub_topic'),
                difficulty_level=eq['ai_generated_questions']['difficulty_level'],
                image_url=eq['ai_generated_questions'].get('image_url')
            )
            for eq in exam_questions.data
        ]

        # Determine time limit
        time_limit = None
        if exam.data['exam_type'] == "full_simulation":
            time_limit = 60

        # Get previous answers
        previous_answers = [
            PreviousAnswer(
                question_id=eq['question_id'],
                user_answer=eq.get('user_answer'),
                time_taken_seconds=eq.get('time_taken_seconds') or 0
            )
            for eq in exam_questions.data
        ]

        return ExamResponse(
            exam_id=exam.data['id'],
            exam_type=exam.data['exam_type'],
            total_questions=exam.data['total_questions'],
            questions=questions,
            started_at=exam.data['started_at'],
            time_limit_minutes=time_limit,
            previous_answers=previous_answers
        )

    # Otherwise return basic details
    # Count answered questions
    answers = supabase.table("exam_question_answers")\
        .select("user_answer")\
        .eq("exam_id", exam_id)\
        .not_.is_("user_answer", "null")\
        .execute()

    answered_count = len(answers.data)

    # Determine time limit based on exam type
    time_limit = None
    if exam.data['exam_type'] == "full_simulation":
        time_limit = 60  # 60 minutes for full simulation

    return ExamDetailsResponse(
        id=exam.data['id'],
        exam_type=exam.data['exam_type'],
        status=exam.data['status'],
        started_at=exam.data['started_at'],
        completed_at=exam.data.get('completed_at'),
        total_questions=exam.data['total_questions'],
        answered_questions=answered_count,
        current_question=answered_count + 1,
        time_limit_minutes=time_limit
    )


@router.post("/{exam_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    exam_id: str,
    request: SubmitAnswerRequest,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """Submit an answer to a question"""
    user = get_user_by_clerk_id(clerk_user_id)

    # Verify exam belongs to user and is in progress
    exam = supabase.table("exams")\
        .select("*")\
        .eq("id", exam_id)\
        .eq("user_id", user['id'])\
        .eq("status", "in_progress")\
        .single()\
        .execute()

    if not exam.data:
        raise HTTPException(status_code=404, detail="Exam not found or not in progress")

    # Verify question belongs to this exam
    exam_question = supabase.table("exam_question_answers")\
        .select("*")\
        .eq("exam_id", exam_id)\
        .eq("question_id", request.question_id)\
        .single()\
        .execute()

    if not exam_question.data:
        raise HTTPException(status_code=400, detail="Question does not belong to this exam")

    # Prevent submitting answer twice
    if exam_question.data.get('user_answer'):
        raise HTTPException(status_code=400, detail="Answer already submitted for this question")

    # Get the question to check correct answer
    question = supabase.table("ai_generated_questions")\
        .select("*")\
        .eq("id", request.question_id)\
        .single()\
        .execute()

    if not question.data:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if answer is correct
    is_correct = request.user_answer.upper() == question.data['correct_answer'].upper()

    # Update the exam_question_answers record
    update_data = {
        "user_answer": request.user_answer.upper(),
        "is_correct": is_correct,
        "time_taken_seconds": request.time_taken_seconds,
        "answered_at": datetime.now().isoformat()
    }

    supabase.table("exam_question_answers")\
        .update(update_data)\
        .eq("exam_id", exam_id)\
        .eq("question_id", request.question_id)\
        .execute()

    # Update user_question_history (aggregate stats)
    # Check if record exists
    existing = supabase.table("user_question_history")\
        .select("*")\
        .eq("user_id", user['id'])\
        .eq("question_id", request.question_id)\
        .execute()

    if existing.data:
        # Update existing record
        record = existing.data[0]
        new_times_seen = record['times_seen'] + 1
        new_times_correct = record['times_correct'] + (1 if is_correct else 0)
        new_times_wrong = record['times_wrong'] + (0 if is_correct else 1)

        # Calculate new average time
        old_avg = float(record['average_time_seconds']) if record['average_time_seconds'] else 0
        new_avg = ((old_avg * record['times_seen']) + request.time_taken_seconds) / new_times_seen

        supabase.table("user_question_history")\
            .update({
                "times_seen": new_times_seen,
                "times_correct": new_times_correct,
                "times_wrong": new_times_wrong,
                "last_seen_at": datetime.now().isoformat(),
                "average_time_seconds": new_avg
            })\
            .eq("id", record['id'])\
            .execute()
    else:
        # Insert new record
        supabase.table("user_question_history").insert({
            "user_id": user['id'],
            "question_id": request.question_id,
            "times_seen": 1,
            "times_correct": 1 if is_correct else 0,
            "times_wrong": 0 if is_correct else 1,
            "first_seen_at": datetime.now().isoformat(),
            "last_seen_at": datetime.now().isoformat(),
            "average_time_seconds": request.time_taken_seconds
        }).execute()

    # If incorrect, add/update mistakes
    if not is_correct:
        # Check if mistake record exists
        existing_mistake = supabase.table("user_mistakes")\
            .select("*")\
            .eq("user_id", user['id'])\
            .eq("question_id", request.question_id)\
            .execute()

        if existing_mistake.data:
            # Update existing mistake record
            record = existing_mistake.data[0]
            supabase.table("user_mistakes")\
                .update({
                    "times_wrong": record['times_wrong'] + 1,
                    "last_wrong_at": datetime.now().isoformat(),
                    "exam_id": exam_id
                })\
                .eq("id", record['id'])\
                .execute()
        else:
            # Insert new mistake record
            supabase.table("user_mistakes").insert({
                "user_id": user['id'],
                "question_id": request.question_id,
                "exam_id": exam_id,
                "times_wrong": 1,
                "first_wrong_at": datetime.now().isoformat(),
                "last_wrong_at": datetime.now().isoformat(),
                "reviewed": False,
                "marked_for_review": False
            }).execute()

    # Prepare response based on exam type
    immediate_feedback = exam.data['exam_type'] == "practice"

    return AnswerResponse(
        is_correct=is_correct,
        correct_answer=question.data['correct_answer'] if immediate_feedback else None,
        explanation=question.data['explanation'] if immediate_feedback else None,
        immediate_feedback=immediate_feedback
    )


@router.post("/{exam_id}/answers/batch")
async def submit_answers_batch(
    exam_id: str,
    request: BatchAnswerRequest,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Submit multiple answers at once (for simulation exams)

    This allows users to answer all questions and submit at the end,
    enabling them to change answers before final submission.
    """
    try:
        user = get_user_by_clerk_id(clerk_user_id)
    except Exception as e:
        print(f"❌ Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

    # Verify exam belongs to user and is in progress
    exam = supabase.table("exams")\
        .select("*")\
        .eq("id", exam_id)\
        .eq("user_id", user['id'])\
        .single()\
        .execute()

    if not exam.data:
        raise HTTPException(status_code=404, detail="Exam not found")

    if exam.data['status'] != "in_progress":
        raise HTTPException(
            status_code=400,
            detail=f"Exam already {exam.data['status']}. Cannot submit answers."
        )

    # OPTIMIZED: Fetch all exam questions and AI questions in bulk (2 queries instead of 50)
    question_ids = [answer.question_id for answer in request.answers]

    # Get all exam questions for this exam in one query
    exam_questions = supabase.table("exam_question_answers")\
        .select("*")\
        .eq("exam_id", exam_id)\
        .in_("question_id", question_ids)\
        .execute()

    exam_question_map = {eq['question_id']: eq for eq in exam_questions.data}

    # Get all AI questions in one query
    ai_questions = supabase.table("ai_generated_questions")\
        .select("*")\
        .in_("id", question_ids)\
        .execute()

    ai_question_map = {q['id']: q for q in ai_questions.data}

    # Get all existing user_question_history in one query
    existing_history = supabase.table("user_question_history")\
        .select("*")\
        .eq("user_id", user['id'])\
        .in_("question_id", question_ids)\
        .execute()

    history_map = {h['question_id']: h for h in existing_history.data}

    # Get all existing mistakes in one query
    existing_mistakes = supabase.table("user_mistakes")\
        .select("*")\
        .eq("user_id", user['id'])\
        .in_("question_id", question_ids)\
        .execute()

    mistakes_map = {m['question_id']: m for m in existing_mistakes.data}

    # Prepare bulk updates and inserts
    exam_answer_updates = []
    history_updates = []
    history_inserts = []
    mistake_updates = []
    mistake_inserts = []
    results = []

    now = datetime.now().isoformat()

    # Process answers in memory
    for answer in request.answers:
        if answer.question_id not in exam_question_map or answer.question_id not in ai_question_map:
            continue

        question = ai_question_map[answer.question_id]
        is_correct = answer.user_answer.upper() == question['correct_answer'].upper()

        # Prepare exam answer update
        exam_answer_updates.append({
            "exam_id": exam_id,
            "question_id": answer.question_id,
            "user_answer": answer.user_answer.upper(),
            "is_correct": is_correct,
            "time_taken_seconds": answer.time_taken_seconds,
            "answered_at": now
        })

        # Prepare history update/insert
        if answer.question_id in history_map:
            record = history_map[answer.question_id]
            new_times_seen = record['times_seen'] + 1
            new_times_correct = record['times_correct'] + (1 if is_correct else 0)
            new_times_wrong = record['times_wrong'] + (0 if is_correct else 1)
            old_avg = float(record['average_time_seconds']) if record['average_time_seconds'] else 0
            new_avg = ((old_avg * record['times_seen']) + answer.time_taken_seconds) / new_times_seen

            history_updates.append({
                "id": record['id'],
                "question_id": answer.question_id,
                "times_seen": new_times_seen,
                "times_correct": new_times_correct,
                "times_wrong": new_times_wrong,
                "last_seen_at": now,
                "average_time_seconds": new_avg,
                "first_seen_at": record['first_seen_at']
            })
        else:
            history_inserts.append({
                "user_id": user['id'],
                "question_id": answer.question_id,
                "times_seen": 1,
                "times_correct": 1 if is_correct else 0,
                "times_wrong": 0 if is_correct else 1,
                "first_seen_at": now,
                "last_seen_at": now,
                "average_time_seconds": answer.time_taken_seconds
            })

        # Prepare mistake update/insert if incorrect
        if not is_correct:
            if answer.question_id in mistakes_map:
                record = mistakes_map[answer.question_id]
                mistake_updates.append({
                    "id": record['id'],
                    "question_id": answer.question_id,
                    "times_wrong": record['times_wrong'] + 1,
                    "last_wrong_at": now,
                    "exam_id": exam_id,
                    "first_wrong_at": record['first_wrong_at'],
                    "reviewed": record['reviewed'],
                    "marked_for_review": record['marked_for_review']
                })
            else:
                mistake_inserts.append({
                    "user_id": user['id'],
                    "question_id": answer.question_id,
                    "exam_id": exam_id,
                    "times_wrong": 1,
                    "first_wrong_at": now,
                    "last_wrong_at": now,
                    "reviewed": False,
                    "marked_for_review": False
                })

        results.append({
            "question_id": answer.question_id,
            "is_correct": is_correct
        })

    # Execute bulk operations using PostgreSQL upsert for maximum performance
    # Update exam answers using upsert (ON CONFLICT DO UPDATE)
    for update in exam_answer_updates:
        supabase.table("exam_question_answers")\
            .update({
                "user_answer": update["user_answer"],
                "is_correct": update["is_correct"],
                "time_taken_seconds": update["time_taken_seconds"],
                "answered_at": update["answered_at"]
            })\
            .eq("exam_id", update["exam_id"])\
            .eq("question_id", update["question_id"])\
            .execute()

    # Upsert history (insert new + update existing in single operation)
    all_history = history_inserts.copy()
    for update in history_updates:
        all_history.append({
            "user_id": user['id'],
            "question_id": update["question_id"],
            "times_seen": update["times_seen"],
            "times_correct": update["times_correct"],
            "times_wrong": update["times_wrong"],
            "last_seen_at": update["last_seen_at"],
            "average_time_seconds": update["average_time_seconds"],
            "first_seen_at": update["first_seen_at"]
        })

    if all_history:
        try:
            # Use upsert to insert or update in one operation
            print(f"📝 Upserting {len(all_history)} history records...")
            supabase.table("user_question_history").upsert(all_history, on_conflict="user_id,question_id").execute()
            print(f"✅ History upserted successfully")
        except Exception as e:
            print(f"❌ Error upserting history: {str(e)}")
            print(f"Sample history data: {all_history[0] if all_history else 'None'}")
            raise HTTPException(status_code=500, detail=f"Error saving history: {str(e)}")

    # Upsert mistakes (insert new + update existing in single operation)
    all_mistakes = mistake_inserts.copy()
    for update in mistake_updates:
        all_mistakes.append({
            "user_id": user['id'],
            "question_id": update["question_id"],
            "exam_id": update["exam_id"],
            "times_wrong": update["times_wrong"],
            "last_wrong_at": update["last_wrong_at"],
            "first_wrong_at": update["first_wrong_at"],
            "reviewed": update["reviewed"],
            "marked_for_review": update["marked_for_review"]
        })

    if all_mistakes:
        try:
            # Use upsert to insert or update in one operation
            print(f"📝 Upserting {len(all_mistakes)} mistakes...")
            supabase.table("user_mistakes").upsert(all_mistakes, on_conflict="user_id,question_id").execute()
            print(f"✅ Mistakes upserted successfully")
        except Exception as e:
            print(f"❌ Error upserting mistakes: {str(e)}")
            print(f"Sample mistake data: {all_mistakes[0] if all_mistakes else 'None'}")
            raise HTTPException(status_code=500, detail=f"Error saving mistakes: {str(e)}")

    return {
        "status": "success",
        "answers_submitted": len(results),
        "message": "Answers saved. Call submit endpoint to finalize exam."
    }


@router.post("/{exam_id}/submit", response_model=SubmitExamResponse)
async def submit_exam(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """Submit final exam and get results"""
    user = get_user_by_clerk_id(clerk_user_id)

    # Verify exam belongs to user
    exam = supabase.table("exams")\
        .select("*")\
        .eq("id", exam_id)\
        .eq("user_id", user['id'])\
        .single()\
        .execute()

    if not exam.data:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Prevent re-submitting completed/abandoned exams
    if exam.data['status'] != "in_progress":
        raise HTTPException(
            status_code=400,
            detail=f"Exam already {exam.data['status']}. Cannot submit again."
        )

    # Calculate results
    results = calculate_exam_results(exam_id, user['id'])

    # Update exam record
    update_data = {
        "status": "completed",
        "completed_at": datetime.now().isoformat(),
        "score_percentage": results['score_percentage'],
        "passed": results['passed']
    }
    supabase.table("exams").update(update_data).eq("id", exam_id).execute()

    # Update user statistics
    supabase.rpc(
        "increment_user_stats",
        {
            "p_user_id": user['id'],
            "p_questions_answered": results['correct_answers'] + results['wrong_answers'],
            "p_exams_taken": 1
        }
    ).execute()

    return SubmitExamResponse(
        exam_id=exam_id,
        score_percentage=results['score_percentage'],
        passed=results['passed'],
        correct_answers=results['correct_answers'],
        wrong_answers=results['wrong_answers'],
        time_taken_seconds=results['time_taken_seconds'],
        weak_topics=results['weak_topics'],
        strong_topics=results['strong_topics']
    )


@router.delete("/{exam_id}")
async def abandon_exam(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """Abandon an in-progress exam"""
    user = get_user_by_clerk_id(clerk_user_id)

    # Verify exam belongs to user and is in progress
    exam = supabase.table("exams")\
        .select("*")\
        .eq("id", exam_id)\
        .eq("user_id", user['id'])\
        .eq("status", "in_progress")\
        .single()\
        .execute()

    if not exam.data:
        raise HTTPException(status_code=404, detail="Exam not found or not in progress")

    # Update exam status to abandoned
    supabase.table("exams")\
        .update({"status": "abandoned", "completed_at": datetime.now().isoformat()})\
        .eq("id", exam_id)\
        .execute()

    return {"status": "success", "message": "Exam abandoned", "exam_id": exam_id}


@router.get("/{exam_id}/results", response_model=ExamResultsResponse)
async def get_exam_results(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """Get detailed exam results with all questions and answers"""
    user = get_user_by_clerk_id(clerk_user_id)

    # Get exam
    exam = supabase.table("exams")\
        .select("*")\
        .eq("id", exam_id)\
        .eq("user_id", user['id'])\
        .single()\
        .execute()

    if not exam.data:
        raise HTTPException(status_code=404, detail="Exam not found")

    if exam.data['status'] != "completed":
        raise HTTPException(status_code=400, detail="Exam not completed yet")

    # Get all questions and answers
    answers = supabase.table("exam_question_answers")\
        .select("*, ai_generated_questions(*)")\
        .eq("exam_id", exam_id)\
        .order("question_order")\
        .execute()

    # Format questions with results
    questions = [
        DetailedQuestionResult(
            question_id=answer['question_id'],
            question_text=answer['ai_generated_questions']['question_text'],
            option_a=answer['ai_generated_questions']['option_a'],
            option_b=answer['ai_generated_questions']['option_b'],
            option_c=answer['ai_generated_questions']['option_c'],
            option_d=answer['ai_generated_questions']['option_d'],
            option_e=answer['ai_generated_questions']['option_e'],
            user_answer=answer['user_answer'] or "Not answered",
            correct_answer=answer['ai_generated_questions']['correct_answer'],
            is_correct=answer.get('is_correct') if answer.get('is_correct') is not None else False,
            time_taken_seconds=answer.get('time_taken_seconds') or 0,
            topic=answer['ai_generated_questions']['topic'],
            difficulty_level=answer['ai_generated_questions']['difficulty_level'],
            explanation=answer['ai_generated_questions']['explanation']
        )
        for answer in answers.data
    ]

    # Calculate analytics
    results = calculate_exam_results(exam_id, user['id'])

    analytics = {
        "time_per_question": results['time_taken_seconds'] / len(questions) if questions else 0,
        "accuracy_by_topic": results['topic_accuracy'],
        "difficulty_breakdown": {
            level: sum(1 for q in questions if q.difficulty_level == level)
            for level in ['easy', 'medium', 'hard']
        }
    }

    # Get exam details
    answered_count = sum(1 for a in answers.data if a.get('user_answer'))

    exam_details = ExamDetailsResponse(
        id=exam.data['id'],
        exam_type=exam.data['exam_type'],
        status=exam.data['status'],
        started_at=exam.data['started_at'],
        completed_at=exam.data.get('completed_at'),
        total_questions=exam.data['total_questions'],
        answered_questions=answered_count,
        current_question=answered_count,
        time_limit_minutes=exam.data.get('time_limit_minutes')
    )

    return ExamResultsResponse(
        exam=exam_details,
        questions=questions,
        analytics=analytics
    )
