#!/usr/bin/env python3
"""
Reset onboarding for all users (for testing)
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client

def reset_onboarding():
    """Reset onboarding_completed to False for all users"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        # Update all users to reset onboarding
        result = supabase.table("users")\
            .update({"onboarding_completed": False})\
            .neq("id", "00000000-0000-0000-0000-000000000000")\
            .execute()

        print(f"✅ Reset onboarding for {len(result.data)} users")

        # Show current state
        users = supabase.table("users")\
            .select("id, clerk_user_id, email, onboarding_completed")\
            .execute()

        print("\n📊 Current users:")
        for user in users.data:
            print(f"  - {user.get('email', 'No email')}: onboarding_completed={user['onboarding_completed']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_onboarding()
