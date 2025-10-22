"""
User Management API Routes

Handles user CRUD operations, Clerk webhook, and user statistics

OPTIMIZED: Week 2 - Migrated to async database queries for non-blocking operations
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from svix.webhooks import Webhook, WebhookVerificationError
from api.auth_simple import get_current_user_id
from api.utils.cache import get_cached, set_cached, delete_pattern, CacheTTL
from api.utils.database import fetch_one, fetch_all, execute_query, dict_to_set_clause

# Router
router = APIRouter(prefix="/api/users", tags=["Users"])

# Clerk Webhook Secret
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET", "")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class UserProfile(BaseModel):
    """User profile response"""
    id: str
    clerk_user_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    created_at: str
    last_login_at: Optional[str]
    onboarding_completed: bool = False
    subscription_status: str
    subscription_expires_at: Optional[str]
    total_questions_answered: int
    total_exams_taken: int
    average_score: Optional[float]
    preferred_difficulty: str
    is_admin: bool = False


class UpdateUserRequest(BaseModel):
    """Update user profile request"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    preferred_difficulty: Optional[str] = Field(
        None,
        description="Preferred difficulty level",
        pattern="^(easy|medium|hard|adaptive)$"
    )


class OnboardingRequest(BaseModel):
    """Complete onboarding request"""
    exam_date: str = Field(..., description="Exam date in ISO format (YYYY-MM-DD)")
    study_hours: list[int] = Field(..., description="Array of hours (0-23) for study reminders")
    expo_push_token: Optional[str] = Field(None, description="Expo push notification token")
    notification_preferences: Optional[dict] = Field(
        default_factory=lambda: {
            "study_reminders_enabled": True,
            "exam_countdown_enabled": True,
            "achievement_notifications_enabled": True
        }
    )


class UserStats(BaseModel):
    """User statistics response"""
    total_questions_answered: int
    total_exams_taken: int
    average_score: Optional[float]
    exams_passed: int
    exams_failed: int
    current_streak: int
    weak_topics: list
    strong_topics: list
    recent_activity: list


# ============================================================================
# CLERK WEBHOOK
# ============================================================================

@router.post("/webhook")
async def clerk_webhook(request: Request):
    """
    Clerk webhook endpoint for user events

    Handles:
    - user.created: Create new user in database
    - user.updated: Update user in database
    - user.deleted: Delete user from database

    Webhook signature is verified using Svix

    OPTIMIZED: Using async database queries
    """
    # Get headers and body
    headers = dict(request.headers)
    body = await request.body()

    # Verify webhook signature
    if CLERK_WEBHOOK_SECRET:
        wh = Webhook(CLERK_WEBHOOK_SECRET)
        try:
            payload = wh.verify(body, headers)
        except WebhookVerificationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid webhook signature: {str(e)}")
    else:
        # For development without webhook secret
        payload = json.loads(body)

    # Get event type and data
    event_type = payload.get("type")
    data = payload.get("data", {})

    try:
        if event_type == "user.created":
            # Create new user
            clerk_user_id = data["id"]
            email = data["email_addresses"][0]["email_address"] if data.get("email_addresses") else None
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            phone = data.get("phone_numbers", [{}])[0].get("phone_number") if data.get("phone_numbers") else None
            now = datetime.now()  # Use datetime object, not string

            # Async INSERT
            result = await execute_query(
                """
                INSERT INTO users (clerk_user_id, email, first_name, last_name, phone, created_at, last_login_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                clerk_user_id, email, first_name, last_name, phone, now, now
            )

            # Get the created user ID
            user = await fetch_one("SELECT id FROM users WHERE clerk_user_id = $1", clerk_user_id)

            return {
                "status": "success",
                "event": "user.created",
                "user_id": user["id"] if user else None
            }

        elif event_type == "user.updated":
            # Update existing user
            clerk_user_id = data["id"]
            email = data["email_addresses"][0]["email_address"] if data.get("email_addresses") else None
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            phone = data.get("phone_numbers", [{}])[0].get("phone_number") if data.get("phone_numbers") else None
            now = datetime.now()  # Use datetime object, not string

            # Async UPDATE
            await execute_query(
                """
                UPDATE users
                SET email = $1, first_name = $2, last_name = $3, phone = $4, updated_at = $5
                WHERE clerk_user_id = $6
                """,
                email, first_name, last_name, phone, now, clerk_user_id
            )

            # Invalidate cache
            await delete_pattern(f"user:profile:{clerk_user_id}")

            return {
                "status": "success",
                "event": "user.updated"
            }

        elif event_type == "user.deleted":
            # Delete user (cascade will delete related data)
            clerk_user_id = data["id"]

            # Async DELETE
            await execute_query(
                "DELETE FROM users WHERE clerk_user_id = $1",
                clerk_user_id
            )

            # Invalidate all user caches
            await delete_pattern(f"user:*:{clerk_user_id}")

            return {
                "status": "success",
                "event": "user.deleted"
            }

        else:
            # Unknown event type
            return {
                "status": "ignored",
                "event": event_type,
                "message": "Event type not handled"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@router.get("/me", response_model=UserProfile)
async def get_current_user(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's profile (with caching)

    Requires: Authorization header with Clerk JWT token
    Cache: 15 minutes TTL

    OPTIMIZED: Async database query + caching
    """
    try:
        # Try to get from cache
        cache_key = f"user:profile:{clerk_user_id}"
        cached_user = await get_cached(cache_key)

        if cached_user:
            print(f"✅ Cache HIT: User profile for {clerk_user_id[:10]}...")
            return UserProfile(**cached_user)

        print(f"❌ Cache MISS: User profile for {clerk_user_id[:10]}...")

        # Cache miss - fetch from database (async)
        user = await fetch_one(
            "SELECT * FROM users WHERE clerk_user_id = $1",
            clerk_user_id
        )

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update last_login_at (async, fire-and-forget)
        await execute_query(
            "UPDATE users SET last_login_at = $1 WHERE clerk_user_id = $2",
            datetime.now(), clerk_user_id  # Use datetime object, not string
        )

        # Convert UUID and datetime objects to strings for Pydantic
        user_data = dict(user)
        user_data["id"] = str(user_data["id"])
        user_data["created_at"] = user_data["created_at"].isoformat() if user_data["created_at"] else None
        user_data["last_login_at"] = user_data["last_login_at"].isoformat() if user_data["last_login_at"] else None
        user_data["subscription_expires_at"] = user_data["subscription_expires_at"].isoformat() if user_data["subscription_expires_at"] else None

        # Cache for 15 minutes
        await set_cached(cache_key, user_data, ttl_seconds=CacheTTL.MEDIUM)

        return UserProfile(**user_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.patch("/me", response_model=UserProfile)
async def update_current_user(
    update_data: UpdateUserRequest,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Update current user's profile

    Requires: Authorization header with Clerk JWT token

    Updatable fields:
    - first_name
    - last_name
    - phone
    - preferred_difficulty

    OPTIMIZED: Async database query
    """
    try:
        # Build update dict (only include non-None fields)
        updates = {k: v for k, v in update_data.dict().items() if v is not None}

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates["updated_at"] = datetime.now()  # Use datetime object, not string

        # Build SET clause dynamically
        set_clause, values = dict_to_set_clause(updates)

        # Async UPDATE
        await execute_query(
            f"UPDATE users SET {set_clause} WHERE clerk_user_id = ${len(values) + 1}",
            *values, clerk_user_id
        )

        # Fetch updated user
        user = await fetch_one(
            "SELECT * FROM users WHERE clerk_user_id = $1",
            clerk_user_id
        )

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Invalidate cache
        cache_key = f"user:profile:{clerk_user_id}"
        await delete_pattern(cache_key)
        await delete_pattern(f"user:stats:{clerk_user_id}")
        print(f"🗑️  Cache invalidated for user {clerk_user_id[:10]}...")

        return UserProfile(**user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


@router.delete("/me")
async def delete_current_user(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Delete current user's account

    Requires: Authorization header with Clerk JWT token

    WARNING: This will delete all user data including:
    - Exam history
    - Question history
    - Mistakes
    - Chat sessions

    OPTIMIZED: Async database query
    """
    try:
        # Async DELETE
        await execute_query(
            "DELETE FROM users WHERE clerk_user_id = $1",
            clerk_user_id
        )

        # Invalidate all user caches
        await delete_pattern(f"user:*:{clerk_user_id}")

        return {
            "status": "success",
            "message": "User account deleted successfully",
            "clerk_user_id": clerk_user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


# ============================================================================
# USER STATISTICS
# ============================================================================

@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's statistics (with caching)

    Requires: Authorization header with Clerk JWT token
    Cache: 5 minutes TTL

    Returns:
    - Total questions answered
    - Total exams taken
    - Average score
    - Pass/fail counts
    - Weak/strong topics
    - Recent activity

    OPTIMIZED: Async database queries + caching
    """
    try:
        # Try to get from cache
        cache_key = f"user:stats:{clerk_user_id}"
        cached_stats = await get_cached(cache_key)

        if cached_stats:
            print(f"✅ Cache HIT: User stats for {clerk_user_id[:10]}...")
            return UserStats(**cached_stats)

        print(f"❌ Cache MISS: User stats for {clerk_user_id[:10]}...")

        # Get user (async)
        user = await fetch_one(
            "SELECT * FROM users WHERE clerk_user_id = $1",
            clerk_user_id
        )

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user["id"]

        # Get exam statistics (async)
        exams = await fetch_all(
            "SELECT * FROM exams WHERE user_id = $1 AND status = $2",
            user_id, "completed"
        )

        # Calculate pass/fail
        exams_passed = sum(1 for exam in exams if exam.get("passed", False))
        exams_failed = len(exams) - exams_passed

        # Get topic performance (async)
        topics = await fetch_all(
            "SELECT * FROM user_topic_performance WHERE user_id = $1",
            user_id
        )

        weak_topics = [
            {"topic": t["topic"], "accuracy": t["accuracy_percentage"]}
            for t in topics if t.get("strength_level") == "weak"
        ]

        strong_topics = [
            {"topic": t["topic"], "accuracy": t["accuracy_percentage"]}
            for t in topics if t.get("strength_level") == "strong"
        ]

        # Get recent exams (last 5)
        recent_exams = sorted(
            exams,
            key=lambda x: x.get("completed_at", ""),
            reverse=True
        )[:5]

        recent_activity = [
            {
                "exam_type": exam["exam_type"],
                "score": exam.get("score_percentage"),
                "passed": exam.get("passed"),
                "completed_at": exam.get("completed_at")
            }
            for exam in recent_exams
        ]

        # Calculate current streak (simplified - consecutive passed exams)
        current_streak = 0
        for exam in recent_exams:
            if exam.get("passed"):
                current_streak += 1
            else:
                break

        stats_data = {
            "total_questions_answered": user.get("total_questions_answered", 0),
            "total_exams_taken": user.get("total_exams_taken", 0),
            "average_score": user.get("average_score"),
            "exams_passed": exams_passed,
            "exams_failed": exams_failed,
            "current_streak": current_streak,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "recent_activity": recent_activity
        }

        # Cache for 5 minutes
        await set_cached(cache_key, stats_data, ttl_seconds=CacheTTL.SHORT)

        return UserStats(**stats_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


# ============================================================================
# ONBOARDING
# ============================================================================

@router.post("/me/onboarding")
async def complete_onboarding(
    onboarding_data: OnboardingRequest,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Save user's onboarding data

    Requires: Authorization header with Clerk JWT token

    Saves:
    - Exam date
    - Study hours for reminders
    - Expo push token (for server-side notifications)
    - Notification preferences
    - Onboarding completion status

    OPTIMIZED: Async database queries
    """
    try:
        # Validate study hours
        if not all(0 <= hour <= 23 for hour in onboarding_data.study_hours):
            raise HTTPException(status_code=400, detail="Study hours must be between 0-23")

        # Parse exam date
        try:
            exam_date = datetime.fromisoformat(onboarding_data.exam_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid exam date format. Use ISO format (YYYY-MM-DD)")

        # Prepare update data
        now = datetime.now()  # Use datetime object, not string
        exam_date_obj = exam_date.date()  # Use date object, not string
        study_hours_json = json.dumps(onboarding_data.study_hours)
        preferences_json = json.dumps(onboarding_data.notification_preferences)

        print(f"[ONBOARDING] Updating user with clerk_user_id: {clerk_user_id}")

        # Check if user exists (async)
        user = await fetch_one(
            "SELECT id, clerk_user_id FROM users WHERE clerk_user_id = $1",
            clerk_user_id
        )

        if not user:
            # User doesn't exist - create them
            print(f"[ONBOARDING] User not found, creating new user...")

            # Build insert query
            if onboarding_data.expo_push_token:
                await execute_query(
                    """
                    INSERT INTO users (
                        clerk_user_id, email, created_at, last_login_at,
                        onboarding_completed, exam_date, study_hours,
                        notification_preferences, expo_push_token
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    clerk_user_id, f"{clerk_user_id}@placeholder.local", now, now,
                    True, exam_date_obj, study_hours_json, preferences_json,
                    onboarding_data.expo_push_token
                )
            else:
                await execute_query(
                    """
                    INSERT INTO users (
                        clerk_user_id, email, created_at, last_login_at,
                        onboarding_completed, exam_date, study_hours,
                        notification_preferences
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    clerk_user_id, f"{clerk_user_id}@placeholder.local", now, now,
                    True, exam_date_obj, study_hours_json, preferences_json
                )

            # Fetch created user
            user = await fetch_one(
                "SELECT * FROM users WHERE clerk_user_id = $1",
                clerk_user_id
            )

            print(f"[ONBOARDING] User created successfully: {user['id']}")

            return {
                "status": "success",
                "message": "Onboarding completed successfully",
                "user_id": user["id"],
                "exam_date": exam_date_obj.isoformat(),  # Convert back to string for JSON response
                "study_hours": onboarding_data.study_hours,
                "push_token_saved": bool(onboarding_data.expo_push_token)
            }

        # User exists - update
        if onboarding_data.expo_push_token:
            await execute_query(
                """
                UPDATE users
                SET onboarding_completed = $1, exam_date = $2, study_hours = $3,
                    notification_preferences = $4, expo_push_token = $5, updated_at = $6
                WHERE clerk_user_id = $7
                """,
                True, exam_date_obj, study_hours_json, preferences_json,
                onboarding_data.expo_push_token, now, clerk_user_id
            )
        else:
            await execute_query(
                """
                UPDATE users
                SET onboarding_completed = $1, exam_date = $2, study_hours = $3,
                    notification_preferences = $4, updated_at = $5
                WHERE clerk_user_id = $6
                """,
                True, exam_date_obj, study_hours_json, preferences_json,
                now, clerk_user_id
            )

        # Invalidate cache
        await delete_pattern(f"user:profile:{clerk_user_id}")

        return {
            "status": "success",
            "message": "Onboarding completed successfully",
            "user_id": user["id"],
            "exam_date": exam_date_obj.isoformat(),  # Convert back to string for JSON response
            "study_hours": onboarding_data.study_hours,
            "push_token_saved": bool(onboarding_data.expo_push_token)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing onboarding: {str(e)}")
