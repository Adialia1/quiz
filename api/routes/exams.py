"""
Exam Management API Routes

Handles exam sessions, question delivery, answer submission, and results.

OPTIMIZED: Week 2 - Migrated to async database queries
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID
import os

from api.auth_clerk import get_current_user_id
from api.utils.database import fetch_one, fetch_all, execute_query, fetch_val, batch_insert
from api.utils.cache import get_cached, set_cached, CacheTTL
from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client, Client

# Initialize Supabase client for batch operations
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

router = APIRouter(prefix="/api/exams", tags=["Exams"])

# ==================== Models ====================

class TopicInfo(BaseModel):
    name: str
    question_count: int

class PracticeTopicsResponse(BaseModel):
    topics: List[TopicInfo]
    difficulties: List[str]

class TopicMistake(BaseModel):
    name: str
    mistake_count: int
    accuracy_percentage: float
    priority: str  # high, medium, low
    priority_emoji: str  # 🔴, 🟡, 🟢
    last_mistake_date: str

class MistakeTopicsResponse(BaseModel):
    topics: List[TopicMistake]
    total_mistakes: int
    total_resolved: int

class MistakeAnalytics(BaseModel):
    total_mistakes: int
    resolved: int
    unresolved: int
    improvement_rate: float
    weak_concepts: List[str]
    progress_this_week: Dict

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

async def get_user_by_clerk_id(clerk_user_id: str):
    """Get user from database by Clerk user ID"""
    user = await fetch_one(
        "SELECT * FROM users WHERE clerk_user_id = $1",
        clerk_user_id
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_user_weak_topics(user_id: str, limit: int = 5) -> List[str]:
    """
    Get user's weakest topics based on performance

    Returns list of topic names ordered by weakness (worst first)
    """
    # Get topic performance, ordered by accuracy (weakest first)
    results = await fetch_all(
        """
        SELECT topic, accuracy_percentage
        FROM user_topic_performance
        WHERE user_id = $1
        ORDER BY accuracy_percentage ASC
        LIMIT $2
        """,
        user_id, limit
    )

    if results:
        return [item['topic'] for item in results]

    # If user has no history, return empty list (will use random questions)
    return []


async def select_questions_for_exam(
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
        # Get questions user got wrong with question details
        results = await fetch_all(
            """
            SELECT q.*
            FROM user_mistakes um
            INNER JOIN ai_generated_questions q ON um.question_id = q.id
            WHERE um.user_id = $1 AND um.is_resolved = FALSE
            LIMIT $2
            """,
            user_id, question_count
        )
        questions = results
    else:
        # Get all questions user has seen (for full_simulation filtering)
        seen_question_ids = []
        if exam_type == "full_simulation" and user_id:
            # Get all question IDs from user's history
            history = await fetch_all(
                "SELECT question_id FROM user_question_history WHERE user_id = $1",
                user_id
            )
            seen_question_ids = [str(item['question_id']) for item in history]

        questions = []

        # ADAPTIVE SELECTION: If no topics specified, use smart topic selection
        if not topics and user_id:
            weak_topics = await get_user_weak_topics(user_id, limit=5)

            if weak_topics:
                # 60% from weak topics, 40% from others
                weak_count = int(question_count * 0.6)
                other_count = question_count - weak_count

                # Get questions from weak topics
                weak_sql = "SELECT * FROM ai_generated_questions WHERE is_active = TRUE AND topic = ANY($1)"
                weak_params = [weak_topics]

                if difficulty:
                    weak_sql += " AND difficulty_level = $2"
                    weak_params.append(difficulty)
                    param_offset = 3
                else:
                    param_offset = 2

                if exam_type == "full_simulation" and seen_question_ids:
                    weak_sql += f" AND id::text != ALL(${param_offset})"
                    weak_params.append(seen_question_ids)
                    param_offset += 1

                weak_sql += f" LIMIT ${param_offset}"
                weak_params.append(weak_count * 2)

                weak_questions = await fetch_all(weak_sql, *weak_params)

                # Get questions from other topics
                other_sql = "SELECT * FROM ai_generated_questions WHERE is_active = TRUE AND topic != ALL($1)"
                other_params = [weak_topics]

                if difficulty:
                    other_sql += " AND difficulty_level = $2"
                    other_params.append(difficulty)
                    param_offset = 3
                else:
                    param_offset = 2

                if exam_type == "full_simulation" and seen_question_ids:
                    other_sql += f" AND id::text != ALL(${param_offset})"
                    other_params.append(seen_question_ids)
                    param_offset += 1

                other_sql += f" LIMIT ${param_offset}"
                other_params.append(other_count * 2)

                other_questions = await fetch_all(other_sql, *other_params)

                # Randomly select from each pool
                selected_weak = random.sample(weak_questions, min(weak_count, len(weak_questions)))
                selected_other = random.sample(other_questions, min(other_count, len(other_questions)))

                # Combine and shuffle
                questions = selected_weak + selected_other
                random.shuffle(questions)

        # STANDARD SELECTION: Topics specified or no adaptive selection
        if not questions:
            sql = "SELECT * FROM ai_generated_questions WHERE is_active = TRUE"
            params = []

            if topics:
                sql += " AND topic = ANY($1)"
                params.append(topics)
                param_offset = 2
            else:
                param_offset = 1

            if difficulty:
                sql += f" AND difficulty_level = ${param_offset}"
                params.append(difficulty)
                param_offset += 1

            # For full_simulation: exclude questions user has seen
            if exam_type == "full_simulation" and seen_question_ids:
                sql += f" AND id::text != ALL(${param_offset})"
                params.append(seen_question_ids)
                param_offset += 1

            # Get more questions than needed for random selection
            sql += f" LIMIT ${param_offset}"
            params.append(question_count * 3)

            all_questions = await fetch_all(sql, *params)

            # Randomly select question_count questions
            questions = all_questions
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


async def calculate_exam_results(exam_id: str, user_id: str) -> Dict:
    """Calculate comprehensive exam results"""
    # Get all answers for this exam with question details
    answers = await fetch_all(
        """
        SELECT
            eqa.*,
            q.topic,
            q.sub_topic,
            q.difficulty_level
        FROM exam_question_answers eqa
        INNER JOIN ai_generated_questions q ON eqa.question_id = q.id
        WHERE eqa.exam_id = $1
        """,
        exam_id
    )

    if not answers:
        raise HTTPException(status_code=404, detail="No answers found for this exam")

    total_questions = len(answers)
    correct_answers = sum(1 for a in answers if a['is_correct'])
    wrong_answers = total_questions - correct_answers
    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    passed = score_percentage >= 70  # 70% passing grade

    # Calculate time taken (handle None values)
    total_time = sum((a.get('time_taken_seconds') or 0) for a in answers)

    # Analyze topics
    topic_performance = {}
    for answer in answers:
        topic = answer.get('topic')
        if topic:
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


# ==================== Helper Functions for Mistakes ====================

def calculate_priority(mistake_count: int, accuracy_percentage: float) -> tuple[str, str]:
    """
    Calculate priority for topic review

    Priority Score = (mistake_count * 2) + (100 - accuracy) / 10

    Thresholds:
    - >= 15: HIGH (🔴)
    - 10-14: MEDIUM (🟡)
    - < 10: LOW (🟢)
    """
    score = (mistake_count * 2) + (100 - accuracy_percentage) / 10

    if score >= 15:
        return "high", "🔴"
    elif score >= 10:
        return "medium", "🟡"
    else:
        return "low", "🟢"


# ==================== Endpoints ====================

@router.get("/mistakes/topics", response_model=MistakeTopicsResponse)
async def get_mistake_topics(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get topics where user has unresolved mistakes
    Ordered by priority (most urgent first)

    OPTIMIZED: Async database with JOIN query
    """
    try:
        user = await get_user_by_clerk_id(clerk_user_id)

        # Get all unresolved mistakes with topic info (async with JOIN)
        mistakes = await fetch_all(
            """
            SELECT
                um.last_wrong_at,
                q.topic
            FROM user_mistakes um
            INNER JOIN ai_generated_questions q ON um.question_id = q.id
            WHERE um.user_id = $1 AND um.is_resolved = FALSE
            """,
            user['id']
        )

        # Group by topic manually
        topic_data = {}
        for mistake in mistakes:
            topic = mistake['topic']
            if topic not in topic_data:
                topic_data[topic] = {
                    'count': 0,
                    'last_date': mistake['last_wrong_at']
                }
            topic_data[topic]['count'] += 1
            if mistake['last_wrong_at'] > topic_data[topic]['last_date']:
                topic_data[topic]['last_date'] = mistake['last_wrong_at']

        # Get topic performance for accuracy (async)
        topic_performance = await fetch_all(
            "SELECT topic, accuracy_percentage FROM user_topic_performance WHERE user_id = $1",
            user['id']
        )

        performance_map = {
            item['topic']: item['accuracy_percentage']
            for item in topic_performance
        } if topic_performance else {}

        # Build topic list with priorities
        topics = []
        for topic, data in topic_data.items():
            accuracy = performance_map.get(topic, 50.0)  # Default 50% if no data
            priority, emoji = calculate_priority(data['count'], accuracy)

            topics.append(TopicMistake(
                name=topic,
                mistake_count=data['count'],
                accuracy_percentage=round(accuracy, 1),
                priority=priority,
                priority_emoji=emoji,
                last_mistake_date=data['last_date'].isoformat() if data['last_date'] else datetime.now().isoformat()
            ))

        # Sort by priority score (descending)
        topics.sort(
            key=lambda t: (t.mistake_count * 2) + (100 - t.accuracy_percentage) / 10,
            reverse=True
        )

        # Get total counts
        total_mistakes = sum(t.mistake_count for t in topics)

        # Get resolved count (async)
        total_resolved = await fetch_val(
            "SELECT COUNT(*) FROM user_mistakes WHERE user_id = $1 AND is_resolved = TRUE",
            user['id']
        )

        return MistakeTopicsResponse(
            topics=topics,
            total_mistakes=total_mistakes,
            total_resolved=total_resolved or 0
        )

    except Exception as e:
        print(f"Error fetching mistake topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch mistake topics: {str(e)}")


@router.get("/mistakes/analytics", response_model=MistakeAnalytics)
async def get_mistake_analytics(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get detailed analytics about user's mistakes and improvement

    OPTIMIZED: Async database with aggregation queries
    """
    try:
        user = await get_user_by_clerk_id(clerk_user_id)

        # Get all mistakes counts (async with single aggregation query)
        mistake_counts = await fetch_one(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_resolved = TRUE THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN is_resolved = FALSE THEN 1 ELSE 0 END) as unresolved
            FROM user_mistakes
            WHERE user_id = $1
            """,
            user['id']
        )

        total = mistake_counts['total'] if mistake_counts else 0
        resolved = mistake_counts['resolved'] if mistake_counts else 0
        unresolved = mistake_counts['unresolved'] if mistake_counts else 0

        # Calculate improvement rate
        improvement_rate = (resolved / total * 100) if total > 0 else 0

        # Get weak concepts (topics with < 60% accuracy) (async)
        topic_performance = await fetch_all(
            """
            SELECT topic
            FROM user_topic_performance
            WHERE user_id = $1 AND accuracy_percentage < 60
            ORDER BY accuracy_percentage ASC
            LIMIT 5
            """,
            user['id']
        )

        weak_concepts = [item['topic'] for item in topic_performance] if topic_performance else []

        # Get progress this week (async)
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)  # Keep as datetime object, not string

        recent_resolved = await fetch_val(
            """
            SELECT COUNT(*)
            FROM user_mistakes
            WHERE user_id = $1 AND is_resolved = TRUE AND resolved_at >= $2
            """,
            user['id'], week_ago
        )

        recent_attempts = await fetch_val(
            """
            SELECT COUNT(*)
            FROM user_question_history
            WHERE user_id = $1 AND last_seen_at >= $2
            """,
            user['id'], week_ago
        )

        progress_this_week = {
            "questions_reviewed": recent_attempts or 0,
            "newly_resolved": recent_resolved or 0
        }

        return MistakeAnalytics(
            total_mistakes=total,
            resolved=resolved,
            unresolved=unresolved,
            improvement_rate=round(improvement_rate, 1),
            weak_concepts=weak_concepts,
            progress_this_week=progress_this_week
        )

    except Exception as e:
        print(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")


@router.get("/practice/topics", response_model=PracticeTopicsResponse)
async def get_practice_topics(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get available topics and difficulties for practice mode

    Returns all unique topics from the questions database with their question counts,
    and the list of available difficulty levels.

    OPTIMIZED: Async database with aggregation query
    """
    try:
        # Get all topics with their question counts (async with GROUP BY)
        topics_result = await fetch_all(
            """
            SELECT topic, COUNT(*) as count
            FROM ai_generated_questions
            WHERE is_active = TRUE
            GROUP BY topic
            ORDER BY topic
            """
        )

        topics = [
            TopicInfo(name=item['topic'], question_count=item['count'])
            for item in topics_result
        ]

        # Standard difficulty levels
        difficulties = ["קל", "בינוני", "קשה"]

        return PracticeTopicsResponse(
            topics=topics,
            difficulties=difficulties
        )

    except Exception as e:
        print(f"Error fetching topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch topics: {str(e)}")


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

    OPTIMIZED: Async database with batch insert
    """
    # Get user from database (async)
    user = await get_user_by_clerk_id(clerk_user_id)

    # Validate exam type
    valid_types = ["practice", "full_simulation", "review_mistakes"]
    if request.exam_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exam_type. Must be one of: {valid_types}"
        )

    # Select questions (async)
    questions = await select_questions_for_exam(
        question_count=request.question_count or 20,
        topics=request.topics,
        difficulty=request.difficulty,
        exam_type=request.exam_type,
        user_id=user['id']
    )

    # Create exam record (async)
    exam = await fetch_one(
        """
        INSERT INTO exams (user_id, exam_type, status, started_at, total_questions)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        user['id'],
        request.exam_type,
        "in_progress",
        datetime.now(),  # Use datetime object, not string
        len(questions)
    )

    # Link questions to exam - OPTIMIZED: Async batch insert
    link_data_batch = [
        (exam['id'], str(question['id']), idx + 1)
        for idx, question in enumerate(questions)
    ]

    await batch_insert(
        "exam_question_answers",
        ["exam_id", "question_id", "question_order"],
        link_data_batch
    )
    print(f"✅ Optimized: Created exam with {len(questions)} questions in single async batch")

    # Prepare response (without correct answers or explanations)
    question_responses = [
        QuestionResponse(
            id=str(q['id']),
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
        time_limit = 150  # 150 minutes (2 hours 30 min) for full simulation

    return ExamResponse(
        exam_id=str(exam['id']),
        exam_type=exam['exam_type'],
        total_questions=exam['total_questions'],
        questions=question_responses,
        started_at=exam['started_at'].isoformat() if exam['started_at'] else None,  # Convert datetime to string
        time_limit_minutes=time_limit
    )


@router.get("/history", response_model=ExamHistoryResponse)
async def get_exam_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None, description="Filter by exam type"),
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get user's exam history (excluding archived exams)

    OPTIMIZED: Async database with single query for data and count
    """
    user = await get_user_by_clerk_id(clerk_user_id)

    # Build query with optional type filter
    if type:
        # Get paginated results with type filter (async)
        result = await fetch_all(
            """
            SELECT * FROM exams
            WHERE user_id = $1 AND is_archived = FALSE AND exam_type = $2
            ORDER BY started_at DESC
            LIMIT $3 OFFSET $4
            """,
            user['id'], type, limit, offset
        )

        # Get total count with type filter (async)
        total_count = await fetch_val(
            "SELECT COUNT(*) FROM exams WHERE user_id = $1 AND is_archived = FALSE AND exam_type = $2",
            user['id'], type
        )
    else:
        # Get paginated results without type filter (async)
        result = await fetch_all(
            """
            SELECT * FROM exams
            WHERE user_id = $1 AND is_archived = FALSE
            ORDER BY started_at DESC
            LIMIT $2 OFFSET $3
            """,
            user['id'], limit, offset
        )

        # Get total count without type filter (async)
        total_count = await fetch_val(
            "SELECT COUNT(*) FROM exams WHERE user_id = $1 AND is_archived = FALSE",
            user['id']
        )

    # Calculate average score
    completed_exams = [e for e in result if e.get('score_percentage') is not None]
    average_score = None
    if completed_exams:
        average_score = sum(e['score_percentage'] for e in completed_exams) / len(completed_exams)

    # Format response
    exams = [
        ExamHistoryItem(
            id=str(exam['id']),
            exam_type=exam['exam_type'],
            status=exam['status'],
            score_percentage=exam.get('score_percentage'),
            passed=exam.get('passed'),
            started_at=exam['started_at'].isoformat() if exam['started_at'] else None,  # Convert datetime to string
            completed_at=exam['completed_at'].isoformat() if exam.get('completed_at') else None,  # Convert datetime to string
            total_questions=exam['total_questions']
        )
        for exam in result
    ]

    return ExamHistoryResponse(
        exams=exams,
        total_count=total_count or 0,
        average_score=round(average_score, 2) if average_score else None
    )


@router.get("/{exam_id}")
async def get_exam(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get exam details and progress. Returns full exam session if in_progress, otherwise details only.

    OPTIMIZED: Async database with JOIN query
    """
    user = await get_user_by_clerk_id(clerk_user_id)

    # Get exam (async)
    exam = await fetch_one(
        "SELECT * FROM exams WHERE id = $1 AND user_id = $2",
        exam_id, user['id']
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # If exam is in progress, return full session with questions
    if exam['status'] == "in_progress":
        # Get all questions for this exam with JOIN (async)
        exam_questions = await fetch_all(
            """
            SELECT
                eqa.*,
                q.question_text,
                q.option_a,
                q.option_b,
                q.option_c,
                q.option_d,
                q.option_e,
                q.topic,
                q.sub_topic,
                q.difficulty_level,
                q.image_url
            FROM exam_question_answers eqa
            INNER JOIN ai_generated_questions q ON eqa.question_id = q.id
            WHERE eqa.exam_id = $1
            ORDER BY eqa.question_order
            """,
            exam_id
        )

        questions = [
            QuestionResponse(
                id=str(eq['question_id']),
                question_text=eq['question_text'],
                option_a=eq['option_a'],
                option_b=eq['option_b'],
                option_c=eq['option_c'],
                option_d=eq['option_d'],
                option_e=eq['option_e'],
                topic=eq['topic'],
                sub_topic=eq.get('sub_topic'),
                difficulty_level=eq['difficulty_level'],
                image_url=eq.get('image_url')
            )
            for eq in exam_questions
        ]

        # Determine time limit
        time_limit = None
        if exam['exam_type'] == "full_simulation":
            time_limit = 60

        # Get previous answers
        previous_answers = [
            PreviousAnswer(
                question_id=str(eq['question_id']),
                user_answer=eq.get('user_answer'),
                time_taken_seconds=eq.get('time_taken_seconds') or 0
            )
            for eq in exam_questions
        ]

        return ExamResponse(
            exam_id=str(exam['id']),
            exam_type=exam['exam_type'],
            total_questions=exam['total_questions'],
            questions=questions,
            started_at=exam['started_at'].isoformat() if exam['started_at'] else None,  # Convert datetime to string
            time_limit_minutes=time_limit,
            previous_answers=previous_answers
        )

    # Otherwise return basic details
    # Count answered questions (async)
    answered_count = await fetch_val(
        "SELECT COUNT(*) FROM exam_question_answers WHERE exam_id = $1 AND user_answer IS NOT NULL",
        exam_id
    )

    # Determine time limit based on exam type
    time_limit = None
    if exam['exam_type'] == "full_simulation":
        time_limit = 150  # 150 minutes (2 hours 30 min) for full simulation

    return ExamDetailsResponse(
        id=str(exam['id']),
        exam_type=exam['exam_type'],
        status=exam['status'],
        started_at=exam['started_at'].isoformat() if exam['started_at'] else None,  # Convert datetime to string
        completed_at=exam['completed_at'].isoformat() if exam.get('completed_at') else None,  # Convert datetime to string
        total_questions=exam['total_questions'],
        answered_questions=answered_count or 0,
        current_question=(answered_count or 0) + 1,
        time_limit_minutes=time_limit
    )


@router.post("/{exam_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    exam_id: str,
    request: SubmitAnswerRequest,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Submit an answer to a question

    OPTIMIZED: Async database with upsert operations
    """
    user = await get_user_by_clerk_id(clerk_user_id)

    # Verify exam belongs to user and is in progress (async)
    exam = await fetch_one(
        "SELECT * FROM exams WHERE id = $1 AND user_id = $2 AND status = $3",
        exam_id, user['id'], "in_progress"
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found or not in progress")

    # Verify question belongs to this exam (async)
    exam_question = await fetch_one(
        "SELECT * FROM exam_question_answers WHERE exam_id = $1 AND question_id = $2",
        exam_id, request.question_id
    )

    if not exam_question:
        raise HTTPException(status_code=400, detail="Question does not belong to this exam")

    # Prevent submitting answer twice
    if exam_question.get('user_answer'):
        raise HTTPException(status_code=400, detail="Answer already submitted for this question")

    # Get the question to check correct answer (async)
    question = await fetch_one(
        "SELECT * FROM ai_generated_questions WHERE id = $1",
        request.question_id
    )

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if answer is correct
    is_correct = request.user_answer.upper() == question['correct_answer'].upper()
    now = datetime.now()  # Use datetime object, not string

    # Update the exam_question_answers record (async)
    await execute_query(
        """
        UPDATE exam_question_answers
        SET user_answer = $1, is_correct = $2, time_taken_seconds = $3, answered_at = $4
        WHERE exam_id = $5 AND question_id = $6
        """,
        request.user_answer.upper(), is_correct, request.time_taken_seconds, now,
        exam_id, request.question_id
    )

    # Get existing history record (async)
    existing = await fetch_one(
        "SELECT * FROM user_question_history WHERE user_id = $1 AND question_id = $2",
        user['id'], request.question_id
    )

    if existing:
        # Update existing record with calculated values
        new_times_seen = existing['times_seen'] + 1
        new_times_correct = existing['times_correct'] + (1 if is_correct else 0)
        new_times_wrong = existing['times_wrong'] + (0 if is_correct else 1)
        old_avg = float(existing['average_time_seconds']) if existing['average_time_seconds'] else 0
        new_avg = ((old_avg * existing['times_seen']) + request.time_taken_seconds) / new_times_seen

        await execute_query(
            """
            UPDATE user_question_history
            SET times_seen = $1, times_correct = $2, times_wrong = $3,
                last_seen_at = $4, average_time_seconds = $5
            WHERE user_id = $6 AND question_id = $7
            """,
            new_times_seen, new_times_correct, new_times_wrong,
            now, new_avg, user['id'], request.question_id
        )
    else:
        # Insert new record (async)
        await execute_query(
            """
            INSERT INTO user_question_history
            (user_id, question_id, times_seen, times_correct, times_wrong,
             first_seen_at, last_seen_at, average_time_seconds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            user['id'], request.question_id, 1,
            1 if is_correct else 0, 0 if is_correct else 1,
            now, now, request.time_taken_seconds
        )

    # Handle mistakes (async)
    if not is_correct:
        # Get existing mistake record
        existing_mistake = await fetch_one(
            "SELECT * FROM user_mistakes WHERE user_id = $1 AND question_id = $2",
            user['id'], request.question_id
        )

        if existing_mistake:
            # Update existing mistake record
            await execute_query(
                """
                UPDATE user_mistakes
                SET times_wrong = $1, last_wrong_at = $2, exam_id = $3, is_resolved = FALSE
                WHERE user_id = $4 AND question_id = $5
                """,
                existing_mistake['times_wrong'] + 1, now, exam_id,
                user['id'], request.question_id
            )
        else:
            # Insert new mistake record
            await execute_query(
                """
                INSERT INTO user_mistakes
                (user_id, question_id, exam_id, times_wrong, first_wrong_at, last_wrong_at,
                 reviewed, marked_for_review, is_resolved)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                user['id'], request.question_id, exam_id, 1, now, now,
                False, False, False
            )
    else:
        # If correct and exam type is review_mistakes, mark as resolved
        if exam['exam_type'] == "review_mistakes":
            # Check if this was a mistake (async)
            existing_mistake = await fetch_one(
                "SELECT id FROM user_mistakes WHERE user_id = $1 AND question_id = $2",
                user['id'], request.question_id
            )

            if existing_mistake:
                # Mark as resolved!
                await execute_query(
                    "UPDATE user_mistakes SET is_resolved = TRUE, resolved_at = $1 WHERE id = $2",
                    now, existing_mistake['id']
                )

    # Prepare response based on exam type
    immediate_feedback = exam['exam_type'] in ["practice", "review_mistakes"]

    return AnswerResponse(
        is_correct=is_correct,
        correct_answer=question['correct_answer'] if immediate_feedback else None,
        explanation=question['explanation'] if immediate_feedback else None,
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

    OPTIMIZED: Async database (Week 2) + Batch operations (Week 1)
    """
    try:
        user = await get_user_by_clerk_id(clerk_user_id)
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

    now = datetime.now()
    now_iso = now.isoformat()  # Convert to ISO string for Supabase
    user_id_str = str(user['id'])  # Convert UUID to string for Supabase

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
            "answered_at": now_iso
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
                "last_seen_at": now_iso,
                "average_time_seconds": new_avg,
                "first_seen_at": record['first_seen_at']
            })
        else:
            history_inserts.append({
                "user_id": user_id_str,
                "question_id": answer.question_id,
                "times_seen": 1,
                "times_correct": 1 if is_correct else 0,
                "times_wrong": 0 if is_correct else 1,
                "first_seen_at": now_iso,
                "last_seen_at": now_iso,
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
                    "last_wrong_at": now_iso,
                    "exam_id": exam_id,
                    "first_wrong_at": record['first_wrong_at'],
                    "reviewed": record['reviewed'],
                    "marked_for_review": record['marked_for_review']
                })
            else:
                mistake_inserts.append({
                    "user_id": user_id_str,
                    "question_id": answer.question_id,
                    "exam_id": exam_id,
                    "times_wrong": 1,
                    "first_wrong_at": now_iso,
                    "last_wrong_at": now_iso,
                    "reviewed": False,
                    "marked_for_review": False
                })

        results.append({
            "question_id": answer.question_id,
            "is_correct": is_correct
        })

    # Execute bulk operations using PostgreSQL upsert for maximum performance
    # OPTIMIZED: Batch update all exam answers in one query using upsert
    if exam_answer_updates:
        print(f"✅ Optimized: Batch updating {len(exam_answer_updates)} exam answers...")
        # Note: Supabase Python client doesn't have native bulk update with WHERE conditions
        # We need to use upsert with on_conflict or use raw SQL for better performance
        # For now, batch the updates in smaller chunks to reduce latency
        try:
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
        except Exception as e:
            print(f"❌ Error updating exam answers: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error updating answers: {str(e)}")

    # Upsert history (insert new + update existing in single operation)
    all_history = history_inserts.copy()
    for update in history_updates:
        all_history.append({
            "user_id": user_id_str,
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
            "user_id": user_id_str,
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
    """
    Submit final exam and get results

    OPTIMIZED: Async database
    """
    user = await get_user_by_clerk_id(clerk_user_id)

    # Verify exam belongs to user (async)
    exam = await fetch_one(
        "SELECT * FROM exams WHERE id = $1 AND user_id = $2",
        exam_id, user['id']
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Prevent re-submitting completed/abandoned exams
    if exam['status'] != "in_progress":
        raise HTTPException(
            status_code=400,
            detail=f"Exam already {exam['status']}. Cannot submit again."
        )

    # Calculate results (async)
    results = await calculate_exam_results(exam_id, user['id'])

    # Update exam record (async)
    await execute_query(
        """
        UPDATE exams
        SET status = $1, completed_at = $2, score_percentage = $3, passed = $4
        WHERE id = $5
        """,
        "completed", datetime.now(),  # Use datetime object, not string
        results['score_percentage'], results['passed'], exam_id
    )

    # Update user statistics (async) - Using direct SQL instead of RPC
    await execute_query(
        """
        UPDATE users
        SET total_questions_answered = COALESCE(total_questions_answered, 0) + $1,
            total_exams_taken = COALESCE(total_exams_taken, 0) + $2
        WHERE id = $3
        """,
        results['correct_answers'] + results['wrong_answers'], 1, user['id']
    )

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


@router.patch("/{exam_id}/archive")
async def archive_exam(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Archive an exam (hide from history)

    OPTIMIZED: Async database
    """
    user = await get_user_by_clerk_id(clerk_user_id)

    # Verify exam belongs to user (async)
    exam = await fetch_one(
        "SELECT id FROM exams WHERE id = $1 AND user_id = $2",
        exam_id, user['id']
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Update exam to archived (async)
    await execute_query(
        "UPDATE exams SET is_archived = TRUE WHERE id = $1",
        exam_id
    )

    return {"status": "success", "message": "Exam archived", "exam_id": exam_id}


@router.delete("/{exam_id}")
async def abandon_exam(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Abandon an in-progress exam

    OPTIMIZED: Async database
    """
    user = await get_user_by_clerk_id(clerk_user_id)

    # Verify exam belongs to user and is in progress (async)
    exam = await fetch_one(
        "SELECT id FROM exams WHERE id = $1 AND user_id = $2 AND status = $3",
        exam_id, user['id'], "in_progress"
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found or not in progress")

    # Update exam status to abandoned (async)
    await execute_query(
        "UPDATE exams SET status = $1, completed_at = $2 WHERE id = $3",
        "abandoned", datetime.now(), exam_id  # Use datetime object, not string
    )

    return {"status": "success", "message": "Exam abandoned", "exam_id": exam_id}


@router.get("/{exam_id}/results", response_model=ExamResultsResponse)
async def get_exam_results(
    exam_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get detailed exam results with all questions and answers

    OPTIMIZED: Async database with JOIN query
    """
    user = await get_user_by_clerk_id(clerk_user_id)

    # Get exam (async)
    exam = await fetch_one(
        "SELECT * FROM exams WHERE id = $1 AND user_id = $2",
        exam_id, user['id']
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if exam['status'] != "completed":
        raise HTTPException(status_code=400, detail="Exam not completed yet")

    # Get all questions and answers with JOIN (async)
    answers = await fetch_all(
        """
        SELECT
            eqa.*,
            q.question_text,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.option_e,
            q.correct_answer,
            q.topic,
            q.difficulty_level,
            q.explanation
        FROM exam_question_answers eqa
        INNER JOIN ai_generated_questions q ON eqa.question_id = q.id
        WHERE eqa.exam_id = $1
        ORDER BY eqa.question_order
        """,
        exam_id
    )

    # Format questions with results
    questions = [
        DetailedQuestionResult(
            question_id=str(answer['question_id']),
            question_text=answer['question_text'],
            option_a=answer['option_a'],
            option_b=answer['option_b'],
            option_c=answer['option_c'],
            option_d=answer['option_d'],
            option_e=answer['option_e'],
            user_answer=answer['user_answer'] or "Not answered",
            correct_answer=answer['correct_answer'],
            is_correct=answer.get('is_correct') if answer.get('is_correct') is not None else False,
            time_taken_seconds=answer.get('time_taken_seconds') or 0,
            topic=answer['topic'],
            difficulty_level=answer['difficulty_level'],
            explanation=answer['explanation']
        )
        for answer in answers
    ]

    # Calculate analytics (async)
    results = await calculate_exam_results(exam_id, user['id'])

    analytics = {
        "time_per_question": results['time_taken_seconds'] / len(questions) if questions else 0,
        "accuracy_by_topic": results['topic_accuracy'],
        "difficulty_breakdown": {
            level: sum(1 for q in questions if q.difficulty_level == level)
            for level in ['easy', 'medium', 'hard']
        }
    }

    # Get exam details
    answered_count = sum(1 for a in answers if a.get('user_answer'))

    exam_details = ExamDetailsResponse(
        id=str(exam['id']),
        exam_type=exam['exam_type'],
        status=exam['status'],
        started_at=exam['started_at'].isoformat() if exam['started_at'] else None,  # Convert datetime to string
        completed_at=exam['completed_at'].isoformat() if exam.get('completed_at') else None,  # Convert datetime to string
        total_questions=exam['total_questions'],
        answered_questions=answered_count,
        current_question=answered_count,
        time_limit_minutes=exam.get('time_limit_minutes')
    )

    return ExamResultsResponse(
        exam=exam_details,
        questions=questions,
        analytics=analytics
    )
