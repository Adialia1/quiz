"""
Progress Tracking API Routes

Handles user progress statistics, exam history, topic performance, and trends
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client, Client
from api.auth_simple import get_current_user_id

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Router
router = APIRouter(prefix="/api/progress", tags=["Progress"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ProgressOverview(BaseModel):
    """Progress overview statistics"""
    total_exams: int
    total_questions_answered: int
    average_score: Optional[float]
    exam_date: Optional[str]
    days_until_exam: Optional[int]
    study_streak_days: int
    exams_this_week: int
    exams_this_month: int
    exams_passed: int
    exams_failed: int


class ExamHistoryItem(BaseModel):
    """Single exam history entry"""
    id: str
    date: str
    exam_type: str
    score: Optional[float]
    passed: Optional[bool]
    time_taken_minutes: Optional[int]
    total_questions: int
    correct_answers: int
    wrong_answers: int
    skipped_answers: int


class TopicPerformance(BaseModel):
    """Topic performance statistics"""
    topic: str
    accuracy: Optional[float]
    strength_level: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    last_practiced: Optional[str]


class ScoreTrendPoint(BaseModel):
    """Single point in score trend"""
    date: str
    score: Optional[float]


class WeeklyActivityPoint(BaseModel):
    """Weekly activity data"""
    week: str
    exams: int


class PerformanceTrends(BaseModel):
    """Performance trends over time"""
    score_trend: List[ScoreTrendPoint]
    weekly_activity: List[WeeklyActivityPoint]
    best_day_of_week: Optional[str]
    best_day_score: Optional[float]


class TopMistakeTopic(BaseModel):
    """Topic with most mistakes"""
    topic: str
    count: int


class MistakeInsights(BaseModel):
    """Mistake analysis"""
    total_mistakes: int
    resolved_mistakes: int
    unresolved_mistakes: int
    top_mistake_topics: List[TopMistakeTopic]


class MasteryLevel(BaseModel):
    """Question mastery breakdown"""
    mastered: int
    practicing: int
    learning: int
    not_seen: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_id_from_clerk(clerk_user_id: str) -> str:
    """Get internal user ID from Clerk user ID"""
    result = supabase.table("users")\
        .select("id")\
        .eq("clerk_user_id", clerk_user_id)\
        .single()\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    return result.data["id"]


def calculate_study_streak(user_id: str) -> int:
    """Calculate consecutive days with completed exams"""
    try:
        # Get all completed exams ordered by date descending
        result = supabase.table("exams")\
            .select("completed_at")\
            .eq("user_id", user_id)\
            .eq("status", "completed")\
            .order("completed_at", desc=True)\
            .execute()

        if not result.data:
            return 0

        # Extract dates
        exam_dates = set()
        for exam in result.data:
            if exam.get("completed_at"):
                date_obj = datetime.fromisoformat(exam["completed_at"].replace('Z', '+00:00'))
                exam_dates.add(date_obj.date())

        if not exam_dates:
            return 0

        # Sort dates
        sorted_dates = sorted(exam_dates, reverse=True)

        # Calculate streak
        streak = 0
        expected_date = datetime.now().date()

        for exam_date in sorted_dates:
            if exam_date == expected_date or exam_date == expected_date - timedelta(days=1):
                streak += 1
                expected_date = exam_date - timedelta(days=1)
            else:
                break

        return streak
    except Exception:
        return 0


def get_best_day_of_week(user_id: str) -> tuple:
    """Get day of week with best average performance"""
    try:
        result = supabase.table("exams")\
            .select("completed_at, score_percentage")\
            .eq("user_id", user_id)\
            .eq("status", "completed")\
            .execute()

        if not result.data:
            return None, None

        # Group by day of week
        day_scores = {}
        day_names = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]

        for exam in result.data:
            if exam.get("completed_at") and exam.get("score_percentage") is not None:
                date_obj = datetime.fromisoformat(exam["completed_at"].replace('Z', '+00:00'))
                day_of_week = date_obj.weekday()  # 0 = Monday
                # Convert to Israeli week (Sunday = 0)
                israeli_day = (day_of_week + 1) % 7

                if israeli_day not in day_scores:
                    day_scores[israeli_day] = []
                day_scores[israeli_day].append(exam["score_percentage"])

        if not day_scores:
            return None, None

        # Calculate average for each day
        day_averages = {day: sum(scores) / len(scores) for day, scores in day_scores.items()}

        # Find best day
        best_day = max(day_averages, key=day_averages.get)
        best_score = day_averages[best_day]

        return day_names[best_day], best_score
    except Exception:
        return None, None


# ============================================================================
# PROGRESS ENDPOINTS
# ============================================================================

@router.get("/overview", response_model=ProgressOverview)
async def get_progress_overview(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get progress overview statistics

    Returns:
    - Total exams completed
    - Total questions answered
    - Average score
    - Days until exam
    - Study streak
    - Weekly/monthly activity
    """
    try:
        user_id = get_user_id_from_clerk(clerk_user_id)

        # Get user data
        user_result = supabase.table("users")\
            .select("*")\
            .eq("id", user_id)\
            .single()\
            .execute()

        user = user_result.data

        # Get completed exams
        exams_result = supabase.table("exams")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "completed")\
            .execute()

        exams = exams_result.data or []

        # Calculate pass/fail
        exams_passed = sum(1 for exam in exams if exam.get("passed", False))
        exams_failed = len(exams) - exams_passed

        # Calculate days until exam and format exam_date
        days_until_exam = None
        exam_date_str = None
        if user.get("exam_date"):
            try:
                exam_date = datetime.fromisoformat(str(user["exam_date"]))
                days_until_exam = (exam_date.date() - datetime.now().date()).days
                exam_date_str = exam_date.strftime("%Y-%m-%d")
            except Exception:
                pass

        # Calculate this week's exams
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        exams_this_week = sum(
            1 for exam in exams
            if exam.get("completed_at") and
            datetime.fromisoformat(exam["completed_at"].replace('Z', '+00:00')) >= week_ago
        )

        # Calculate this month's exams
        month_ago = datetime.now(timezone.utc) - timedelta(days=30)
        exams_this_month = sum(
            1 for exam in exams
            if exam.get("completed_at") and
            datetime.fromisoformat(exam["completed_at"].replace('Z', '+00:00')) >= month_ago
        )

        # Calculate study streak
        streak = calculate_study_streak(user_id)

        return ProgressOverview(
            total_exams=user.get("total_exams_taken", 0),
            total_questions_answered=user.get("total_questions_answered", 0),
            average_score=float(user["average_score"]) if user.get("average_score") else None,
            exam_date=exam_date_str,
            days_until_exam=days_until_exam,
            study_streak_days=streak,
            exams_this_week=exams_this_week,
            exams_this_month=exams_this_month,
            exams_passed=exams_passed,
            exams_failed=exams_failed
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in get_progress_overview: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching overview: {str(e)}")


@router.get("/exam-history", response_model=List[ExamHistoryItem])
async def get_exam_history(
    clerk_user_id: str = Depends(get_current_user_id),
    limit: int = 20
):
    """
    Get user's exam history

    Returns list of completed exams ordered by date (newest first)
    """
    try:
        user_id = get_user_id_from_clerk(clerk_user_id)

        # Get completed exams
        result = supabase.table("exams")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "completed")\
            .order("completed_at", desc=True)\
            .limit(limit)\
            .execute()

        exams = result.data or []

        # Format response
        history = []
        for exam in exams:
            history.append(ExamHistoryItem(
                id=exam["id"],
                date=exam.get("completed_at", ""),
                exam_type=exam.get("exam_type", ""),
                score=float(exam["score_percentage"]) if exam.get("score_percentage") is not None else None,
                passed=exam.get("passed"),
                time_taken_minutes=exam.get("time_taken_seconds", 0) // 60 if exam.get("time_taken_seconds") else None,
                total_questions=exam.get("total_questions", 0),
                correct_answers=exam.get("correct_answers", 0),
                wrong_answers=exam.get("wrong_answers", 0),
                skipped_answers=exam.get("skipped_answers", 0)
            ))

        return history

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching exam history: {str(e)}")


@router.get("/topics", response_model=List[TopicPerformance])
async def get_topic_performance(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get performance breakdown by topic

    Returns list of topics with accuracy and strength level
    """
    try:
        user_id = get_user_id_from_clerk(clerk_user_id)

        # Get topic performance
        result = supabase.table("user_topic_performance")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("accuracy_percentage", desc=True)\
            .execute()

        topics = result.data or []

        # Format response
        performance = []
        for topic in topics:
            performance.append(TopicPerformance(
                topic=topic.get("topic", ""),
                accuracy=float(topic["accuracy_percentage"]) if topic.get("accuracy_percentage") is not None else None,
                strength_level=topic.get("strength_level", "average"),
                total_questions=topic.get("total_questions", 0),
                correct_answers=topic.get("correct_answers", 0),
                wrong_answers=topic.get("wrong_answers", 0),
                last_practiced=topic.get("last_practiced_at")
            ))

        return performance

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching topic performance: {str(e)}")


@router.get("/trends", response_model=PerformanceTrends)
async def get_performance_trends(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get performance trends over time

    Returns:
    - Score trend (weekly averages)
    - Weekly activity (exams per week)
    - Best day of week
    """
    try:
        user_id = get_user_id_from_clerk(clerk_user_id)

        # Get all completed exams
        result = supabase.table("exams")\
            .select("completed_at, score_percentage")\
            .eq("user_id", user_id)\
            .eq("status", "completed")\
            .order("completed_at", desc=False)\
            .execute()

        exams = result.data or []

        # Group by week for score trend
        weekly_scores = {}
        weekly_counts = {}

        for exam in exams:
            if exam.get("completed_at"):
                date_obj = datetime.fromisoformat(exam["completed_at"].replace('Z', '+00:00'))
                # Get week string (YYYY-Www)
                week_str = date_obj.strftime("%Y-W%U")

                if week_str not in weekly_scores:
                    weekly_scores[week_str] = []
                    weekly_counts[week_str] = 0

                if exam.get("score_percentage") is not None:
                    weekly_scores[week_str].append(exam["score_percentage"])

                weekly_counts[week_str] += 1

        # Calculate score trend
        score_trend = []
        for week in sorted(weekly_scores.keys())[-12:]:  # Last 12 weeks
            avg_score = sum(weekly_scores[week]) / len(weekly_scores[week]) if weekly_scores[week] else None
            # Get first day of week for display
            year, week_num = week.split('-W')
            date_obj = datetime.strptime(f"{year}-W{week_num}-1", "%Y-W%U-%w")
            score_trend.append(ScoreTrendPoint(
                date=date_obj.strftime("%Y-%m-%d"),
                score=avg_score
            ))

        # Weekly activity
        weekly_activity = []
        for week in sorted(weekly_counts.keys())[-12:]:  # Last 12 weeks
            weekly_activity.append(WeeklyActivityPoint(
                week=week,
                exams=weekly_counts[week]
            ))

        # Get best day of week
        best_day, best_score = get_best_day_of_week(user_id)

        return PerformanceTrends(
            score_trend=score_trend,
            weekly_activity=weekly_activity,
            best_day_of_week=best_day,
            best_day_score=best_score
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")


@router.get("/mistakes", response_model=MistakeInsights)
async def get_mistake_insights(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get mistake analysis

    Returns:
    - Total mistakes
    - Resolved vs unresolved
    - Top topics with mistakes
    """
    try:
        user_id = get_user_id_from_clerk(clerk_user_id)

        # Get all mistakes
        result = supabase.table("user_mistakes")\
            .select("*, ai_generated_questions(topic)")\
            .eq("user_id", user_id)\
            .execute()

        mistakes = result.data or []

        # Count resolved/unresolved
        resolved = sum(1 for m in mistakes if m.get("is_resolved", False))
        total = len(mistakes)
        unresolved = total - resolved

        # Count by topic
        topic_counts = {}
        for mistake in mistakes:
            # Access nested topic data
            question_data = mistake.get("ai_generated_questions")
            if question_data and isinstance(question_data, dict):
                topic = question_data.get("topic", "Unknown")
            else:
                topic = "Unknown"

            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Get top 5 topics
        top_topics = [
            TopMistakeTopic(topic=topic, count=count)
            for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return MistakeInsights(
            total_mistakes=total,
            resolved_mistakes=resolved,
            unresolved_mistakes=unresolved,
            top_mistake_topics=top_topics
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mistakes: {str(e)}")


@router.get("/mastery", response_model=MasteryLevel)
async def get_mastery_level(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get question mastery breakdown

    Returns count of questions by mastery level:
    - mastered
    - practicing
    - learning
    - not_seen
    """
    try:
        user_id = get_user_id_from_clerk(clerk_user_id)

        # Get question history
        result = supabase.table("user_question_history")\
            .select("mastery_level")\
            .eq("user_id", user_id)\
            .execute()

        questions = result.data or []

        # Count by mastery level
        mastered = sum(1 for q in questions if q.get("mastery_level") == "mastered")
        practicing = sum(1 for q in questions if q.get("mastery_level") == "practicing")
        learning = sum(1 for q in questions if q.get("mastery_level") == "learning")
        not_seen = sum(1 for q in questions if q.get("mastery_level") == "not_seen")

        return MasteryLevel(
            mastered=mastered,
            practicing=practicing,
            learning=learning,
            not_seen=not_seen
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mastery: {str(e)}")
