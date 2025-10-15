#!/usr/bin/env python3
"""
Script to check user subscription status in Supabase
"""
import sys
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

from supabase import create_client, Client

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# User to check
CLERK_USER_ID = 'user_343m3D84HDYRtuVsYVQJpwGYML9'

print(f"Checking subscription for user: {CLERK_USER_ID}")
print()

try:
    # Get user from database
    response = supabase.table("users").select("*").eq("clerk_user_id", CLERK_USER_ID).execute()

    if not response.data or len(response.data) == 0:
        print(f"❌ Error: User with clerk_user_id '{CLERK_USER_ID}' not found")
        sys.exit(1)

    user = response.data[0]

    print("✅ User found!")
    print()
    print("Subscription Details:")
    print(f"  - Email: {user.get('email', 'N/A')}")
    print(f"  - Full Name: {user.get('full_name', 'N/A')}")
    print(f"  - Subscription Status: {user.get('subscription_status', 'none')}")
    print(f"  - Subscription Period: {user.get('subscription_period', 'N/A')}")
    print(f"  - Expires At: {user.get('subscription_expires_at', 'N/A')}")
    print(f"  - Will Renew: {user.get('subscription_will_renew', False)}")
    print(f"  - Is In Trial: {user.get('is_in_trial', False)}")

    # Calculate days remaining
    if user.get('subscription_expires_at'):
        try:
            from datetime import timezone
            expires_at = datetime.fromisoformat(user['subscription_expires_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_remaining = (expires_at - now).days
            print(f"  - Days Remaining: {days_remaining}")
        except Exception as e:
            print(f"  - Days Remaining: Error calculating ({str(e)})")

except Exception as e:
    print(f"❌ Error checking subscription: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
