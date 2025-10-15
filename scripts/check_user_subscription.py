#!/usr/bin/env python3
"""
Script to check user subscription status in Supabase
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client, Client

def check_user_subscription(clerk_user_id: str):
    """
    Check subscription status for a user

    Args:
        clerk_user_id: The Clerk user ID to look up
    """
    # Initialize Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print(f"\n🔍 Checking subscription for user: {clerk_user_id}")
    print("=" * 80)

    try:
        # Query the users table
        response = supabase.table("users").select(
            "clerk_user_id, subscription_status, subscription_period, "
            "subscription_expires_at, subscription_will_renew, is_in_trial, "
            "email, full_name, created_at, updated_at"
        ).eq("clerk_user_id", clerk_user_id).execute()

        if not response.data or len(response.data) == 0:
            print(f"❌ User not found with clerk_user_id: {clerk_user_id}")
            return

        user = response.data[0]

        print(f"\n✅ User Found:")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   Full Name: {user.get('full_name', 'N/A')}")
        print(f"   Created: {user.get('created_at', 'N/A')}")
        print(f"   Updated: {user.get('updated_at', 'N/A')}")

        print(f"\n📋 Subscription Details:")
        print(f"   Status: {user.get('subscription_status', 'none')}")
        print(f"   Period: {user.get('subscription_period', 'N/A')}")
        print(f"   Expires At: {user.get('subscription_expires_at', 'N/A')}")
        print(f"   Will Renew: {user.get('subscription_will_renew', False)}")
        print(f"   In Trial: {user.get('is_in_trial', False)}")

        # Determine if subscription is active
        status = user.get('subscription_status', 'none')
        if status in ['active', 'trial']:
            print(f"\n✅ Subscription is ACTIVE")
        else:
            print(f"\n❌ Subscription is NOT ACTIVE (status: {status})")

        print("\n" + "=" * 80)

        # Return the data for programmatic use
        return user

    except Exception as e:
        print(f"❌ Error querying database: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Check the specific user
    user_id = "user_343m3D84HDYRtuVsYVQJpwGYML9"
    check_user_subscription(user_id)
