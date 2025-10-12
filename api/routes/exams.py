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


class ExamResponse(BaseModel):
    exam_id: str
    exam_type: str
    total_questions: int
    questions: List[QuestionResponse]
    started_at: str
    time_limit_minutes: Optional[int]


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

    # Calculate time taken
    total_time = sum(a.get('time_taken_seconds', 0) for a in answers.data)

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

    # Determine time limit based on exam type
    time_limit_minutes = None
    if request.exam_type == "full_simulation":
        time_limit_minutes = 60  # 60 minutes for full simulation

    # Create exam record
    exam_data = {
        "user_id": user['id'],
        "exam_type": request.exam_type,
        "status": "in_progress",
        "started_at": datetime.now().isoformat(),
        "total_questions": len(questions),
        "time_limit_minutes": time_limit_minutes
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

    return ExamResponse(
        exam_id=exam['id'],
        exam_type=exam['exam_type'],
        total_questions=exam['total_questions'],
        questions=question_responses,
        started_at=exam['started_at'],
        time_limit_minutes=time_limit_minutes
    )


@router.get("/{exam_id}", response_model=ExamDetailsResponse)
async def get_exam(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """Get exam details and progress"""
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

    # Count answered questions
    answers = supabase.table("exam_question_answers")\
        .select("user_answer")\
        .eq("exam_id", exam_id)\
        .not_.is_("user_answer", "null")\
        .execute()

    answered_count = len(answers.data)

    return ExamDetailsResponse(
        id=exam.data['id'],
        exam_type=exam.data['exam_type'],
        status=exam.data['status'],
        started_at=exam.data['started_at'],
        completed_at=exam.data.get('completed_at'),
        total_questions=exam.data['total_questions'],
        answered_questions=answered_count,
        current_question=answered_count + 1,
        time_limit_minutes=exam.data.get('time_limit_minutes')
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

    # Update user_question_history
    history_data = {
        "user_id": user['id'],
        "question_id": request.question_id,
        "user_answer": request.user_answer.upper(),
        "is_correct": is_correct,
        "time_taken_seconds": request.time_taken_seconds,
        "context": f"exam_{exam_id}"
    }
    supabase.table("user_question_history").insert(history_data).execute()

    # If incorrect, add to mistakes
    if not is_correct:
        mistake_data = {
            "user_id": user['id'],
            "question_id": request.question_id,
            "user_answer": request.user_answer.upper(),
            "correct_answer": question.data['correct_answer'],
            "exam_id": exam_id,
            "is_resolved": False
        }
        supabase.table("user_mistakes").insert(mistake_data).execute()

    # Prepare response based on exam type
    immediate_feedback = exam.data['exam_type'] == "practice"

    return AnswerResponse(
        is_correct=is_correct,
        correct_answer=question.data['correct_answer'] if immediate_feedback else None,
        explanation=question.data['explanation'] if immediate_feedback else None,
        immediate_feedback=immediate_feedback
    )


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
            user_answer=answer['user_answer'] or "Not answered",
            correct_answer=answer['ai_generated_questions']['correct_answer'],
            is_correct=answer.get('is_correct', False),
            time_taken_seconds=answer.get('time_taken_seconds', 0),
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
