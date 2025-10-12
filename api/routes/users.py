"""
User Management API Routes

Handles user CRUD operations, Clerk webhook, and user statistics
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

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client, Client
from svix.webhooks import Webhook, WebhookVerificationError
from api.auth import get_current_user_id

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

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
    subscription_status: str
    subscription_expires_at: Optional[str]
    total_questions_answered: int
    total_exams_taken: int
    average_score: Optional[float]
    preferred_difficulty: str


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
            user_data = {
                "clerk_user_id": data["id"],
                "email": data["email_addresses"][0]["email_address"] if data.get("email_addresses") else None,
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "phone": data.get("phone_numbers", [{}])[0].get("phone_number") if data.get("phone_numbers") else None,
                "created_at": datetime.now().isoformat(),
                "last_login_at": datetime.now().isoformat()
            }

            result = supabase.table("users").insert(user_data).execute()

            return {
                "status": "success",
                "event": "user.created",
                "user_id": result.data[0]["id"] if result.data else None
            }

        elif event_type == "user.updated":
            # Update existing user
            update_data = {
                "email": data["email_addresses"][0]["email_address"] if data.get("email_addresses") else None,
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "phone": data.get("phone_numbers", [{}])[0].get("phone_number") if data.get("phone_numbers") else None,
                "updated_at": datetime.now().isoformat()
            }

            result = supabase.table("users")\
                .update(update_data)\
                .eq("clerk_user_id", data["id"])\
                .execute()

            return {
                "status": "success",
                "event": "user.updated",
                "updated": len(result.data) if result.data else 0
            }

        elif event_type == "user.deleted":
            # Delete user (cascade will delete related data)
            result = supabase.table("users")\
                .delete()\
                .eq("clerk_user_id", data["id"])\
                .execute()

            return {
                "status": "success",
                "event": "user.deleted",
                "deleted": len(result.data) if result.data else 0
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
    Get current user's profile

    Requires: Authorization header with Clerk JWT token
    """
    try:
        result = supabase.table("users")\
            .select("*")\
            .eq("clerk_user_id", clerk_user_id)\
            .single()\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        # Update last_login_at
        supabase.table("users")\
            .update({"last_login_at": datetime.now().isoformat()})\
            .eq("clerk_user_id", clerk_user_id)\
            .execute()

        return UserProfile(**result.data)

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
    """
    try:
        # Build update dict (only include non-None fields)
        updates = {k: v for k, v in update_data.dict().items() if v is not None}

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates["updated_at"] = datetime.now().isoformat()

        # Update in database
        result = supabase.table("users")\
            .update(updates)\
            .eq("clerk_user_id", clerk_user_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        return UserProfile(**result.data[0])

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
    """
    try:
        result = supabase.table("users")\
            .delete()\
            .eq("clerk_user_id", clerk_user_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

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
    Get current user's statistics

    Requires: Authorization header with Clerk JWT token

    Returns:
    - Total questions answered
    - Total exams taken
    - Average score
    - Pass/fail counts
    - Weak/strong topics
    - Recent activity
    """
    try:
        # Get user
        user_result = supabase.table("users")\
            .select("*")\
            .eq("clerk_user_id", clerk_user_id)\
            .single()\
            .execute()

        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_result.data
        user_id = user["id"]

        # Get exam statistics
        exams_result = supabase.table("exams")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "completed")\
            .execute()

        exams = exams_result.data or []

        # Calculate pass/fail
        exams_passed = sum(1 for exam in exams if exam.get("passed", False))
        exams_failed = len(exams) - exams_passed

        # Get topic performance
        topic_perf_result = supabase.table("user_topic_performance")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()

        topics = topic_perf_result.data or []

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

        return UserStats(
            total_questions_answered=user.get("total_questions_answered", 0),
            total_exams_taken=user.get("total_exams_taken", 0),
            average_score=user.get("average_score"),
            exams_passed=exams_passed,
            exams_failed=exams_failed,
            current_streak=current_streak,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            recent_activity=recent_activity
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
