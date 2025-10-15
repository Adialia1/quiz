"""
Subscription Management API Routes

Handles RevenueCat webhook events and subscription status sync
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timedelta
import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client, Client
from api.auth import get_current_user_id

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Router
router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])

# RevenueCat Webhook Secret
REVENUECAT_WEBHOOK_SECRET = os.getenv("REVENUECAT_WEBHOOK_SECRET", "")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SubscriptionStatusRequest(BaseModel):
    """Update subscription status request"""
    subscription_status: Literal["active", "trial", "expired", "none"]
    subscription_period: Optional[Literal["monthly", "quarterly"]] = None
    subscription_expires_at: Optional[str] = None  # ISO format
    is_in_trial: bool = False
    will_renew: bool = False


class SubscriptionStatusResponse(BaseModel):
    """Subscription status response"""
    subscription_status: str
    subscription_period: Optional[str]
    subscription_expires_at: Optional[str]
    is_in_trial: bool
    will_renew: bool
    days_remaining: Optional[int]


class SubscriptionPurchaseRequest(BaseModel):
    """Track subscription purchase"""
    plan_id: str = Field(..., description="Plan ID (e.g., 'quiz_monthly_69')")
    price: float
    currency: str = "ILS"
    revenuecat_transaction_id: Optional[str] = None


# ============================================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================================

@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(user_id: str = Depends(get_current_user_id)):
    """
    Get current user's subscription status

    Returns subscription details including:
    - Status (active/trial/expired/none)
    - Period (monthly/quarterly)
    - Expiration date
    - Trial status
    - Renewal status
    - Days remaining
    """
    try:
        # Get user from database
        response = supabase.table("users").select("*").eq("clerk_user_id", user_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user = response.data[0]

        # Calculate days remaining
        days_remaining = None
        if user.get("subscription_expires_at"):
            try:
                expires_at = datetime.fromisoformat(user["subscription_expires_at"].replace('Z', '+00:00'))
                days_remaining = (expires_at - datetime.now()).days
                if days_remaining < 0:
                    days_remaining = 0
            except:
                pass

        return SubscriptionStatusResponse(
            subscription_status=user.get("subscription_status", "none"),
            subscription_period=user.get("subscription_period"),
            subscription_expires_at=user.get("subscription_expires_at"),
            is_in_trial=user.get("is_in_trial", False),
            will_renew=user.get("subscription_will_renew", False),
            days_remaining=days_remaining
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subscription status: {str(e)}")


@router.post("/status")
async def update_subscription_status(
    request: SubscriptionStatusRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update user's subscription status

    Called by the app after successful purchase or restore from RevenueCat
    """
    try:
        # Prepare update data
        update_data = {
            "subscription_status": request.subscription_status,
            "subscription_period": request.subscription_period,
            "is_in_trial": request.is_in_trial,
            "subscription_will_renew": request.will_renew,
            "updated_at": datetime.now().isoformat()
        }

        # Add expiration date if provided
        if request.subscription_expires_at:
            update_data["subscription_expires_at"] = request.subscription_expires_at

        # Update user in database
        response = supabase.table("users").update(update_data).eq("clerk_user_id", user_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "message": "Subscription status updated successfully",
            "data": response.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating subscription status: {str(e)}")


@router.post("/purchase")
async def track_subscription_purchase(
    request: SubscriptionPurchaseRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Track a subscription purchase

    Logs the purchase for analytics and updates user subscription
    """
    try:
        # Get user
        user_response = supabase.table("users").select("*").eq("clerk_user_id", user_id).execute()

        if not user_response.data or len(user_response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_response.data[0]

        # Calculate expiration based on plan
        if "monthly" in request.plan_id:
            period = "monthly"
            expires_at = datetime.now() + timedelta(days=30)
        elif "quarterly" in request.plan_id:
            period = "quarterly"
            expires_at = datetime.now() + timedelta(days=90)
        else:
            period = None
            expires_at = datetime.now() + timedelta(days=30)  # Default

        # Update user subscription
        update_data = {
            "subscription_status": "trial" if "trial" in request.plan_id else "active",
            "subscription_period": period,
            "subscription_expires_at": expires_at.isoformat(),
            "subscription_will_renew": True,
            "is_in_trial": "monthly" in request.plan_id,  # Monthly has 3-day trial
            "updated_at": datetime.now().isoformat()
        }

        supabase.table("users").update(update_data).eq("clerk_user_id", user_id).execute()

        # Create purchase record (optional - for analytics)
        purchase_data = {
            "user_id": user["id"],
            "plan_id": request.plan_id,
            "price": request.price,
            "currency": request.currency,
            "revenuecat_transaction_id": request.revenuecat_transaction_id,
            "purchased_at": datetime.now().isoformat()
        }

        # You can create a purchases table if needed for tracking
        # supabase.table("subscription_purchases").insert(purchase_data).execute()

        return {
            "success": True,
            "message": "Purchase tracked successfully",
            "subscription_status": update_data["subscription_status"],
            "expires_at": update_data["subscription_expires_at"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking purchase: {str(e)}")


@router.post("/webhook")
async def revenuecat_webhook(request: Request):
    """
    RevenueCat webhook endpoint for subscription events

    Handles events like:
    - INITIAL_PURCHASE
    - RENEWAL
    - CANCELLATION
    - EXPIRATION
    - BILLING_ISSUE

    Configure this webhook in RevenueCat dashboard:
    https://app.revenuecat.com/settings/integrations/webhooks
    """
    try:
        # Get raw body
        body = await request.body()

        # Verify webhook signature if secret is configured
        if REVENUECAT_WEBHOOK_SECRET:
            signature = request.headers.get("X-RevenueCat-Signature", "")
            # TODO: Implement signature verification
            # For now, we'll trust the webhook in development

        # Parse webhook data
        data = json.loads(body)

        # RevenueCat v2 API structure
        event_data = data.get("event", {})
        event_type = event_data.get("type", data.get("type"))
        app_user_id = event_data.get("app_user_id", data.get("app_user_id"))
        product_id = event_data.get("product_id", data.get("product_id"))

        print(f"[WEBHOOK] 📬 RevenueCat webhook received")
        print(f"[WEBHOOK] Event type: {event_type}")
        print(f"[WEBHOOK] App user ID: {app_user_id}")
        print(f"[WEBHOOK] Product ID: {product_id}")

        # Handle TEST events
        if event_type == "TEST":
            print(f"[WEBHOOK] ✅ Test event received successfully")
            return {
                "received": True,
                "note": "Test event received successfully",
                "event_type": event_type
            }

        if not app_user_id:
            print(f"[WEBHOOK] ⚠️ No app_user_id provided")
            return {"received": True, "note": "No app_user_id provided"}

        # Get user
        user_response = supabase.table("users").select("*").eq("clerk_user_id", app_user_id).execute()

        if not user_response.data or len(user_response.data) == 0:
            print(f"[WEBHOOK] ⚠️ User not found: {app_user_id}")
            return {"received": True, "note": "User not found", "app_user_id": app_user_id}

        # Handle different event types
        update_data = {"updated_at": datetime.now().isoformat()}

        if event_type == "INITIAL_PURCHASE":
            # New subscription
            update_data.update({
                "subscription_status": "active",
                "subscription_will_renew": True,
            })

        elif event_type == "RENEWAL":
            # Subscription renewed
            update_data.update({
                "subscription_status": "active",
                "subscription_will_renew": True,
                "is_in_trial": False,  # Trial is over after renewal
            })

        elif event_type == "CANCELLATION":
            # User cancelled (but may still have access until expiration)
            update_data.update({
                "subscription_will_renew": False,
            })

        elif event_type == "EXPIRATION":
            # Subscription expired
            update_data.update({
                "subscription_status": "expired",
                "subscription_will_renew": False,
                "is_in_trial": False,
            })

        elif event_type == "BILLING_ISSUE":
            # Payment failed
            update_data.update({
                "subscription_will_renew": False,
            })

        # Update expiration date if provided
        expiration_date = data.get("expiration_at_ms")
        if expiration_date:
            expires_at = datetime.fromtimestamp(expiration_date / 1000)
            update_data["subscription_expires_at"] = expires_at.isoformat()

        # Determine period from product_id
        if product_id:
            if "monthly" in product_id:
                update_data["subscription_period"] = "monthly"
            elif "quarterly" in product_id:
                update_data["subscription_period"] = "quarterly"

        # Update user in database
        result = supabase.table("users").update(update_data).eq("clerk_user_id", app_user_id).execute()

        print(f"[WEBHOOK] ✅ Updated subscription for user {app_user_id}")
        print(f"[WEBHOOK] Event: {event_type}")
        print(f"[WEBHOOK] Updates: {list(update_data.keys())}")

        return {
            "received": True,
            "event_type": event_type,
            "app_user_id": app_user_id,
            "updated_fields": list(update_data.keys())
        }

    except Exception as e:
        print(f"[WEBHOOK] ❌ Webhook error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return 200 even on error to prevent retries
        return {"received": True, "error": str(e)}


@router.delete("/cancel")
async def cancel_subscription(user_id: str = Depends(get_current_user_id)):
    """
    Mark subscription as cancelled (will not renew)

    Note: This doesn't actually cancel in RevenueCat.
    User should cancel through App Store/Google Play settings.
    This endpoint just marks it in our database.
    """
    try:
        update_data = {
            "subscription_will_renew": False,
            "updated_at": datetime.now().isoformat()
        }

        response = supabase.table("users").update(update_data).eq("clerk_user_id", user_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "message": "Subscription marked as cancelled. Access will continue until expiration date."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling subscription: {str(e)}")
