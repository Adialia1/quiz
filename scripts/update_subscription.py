#!/usr/bin/env python3
"""
Script to update user subscription in Supabase
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
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

# User to update
CLERK_USER_ID = 'user_343m3D84HDYRtuVsYVQJpwGYML9'

# Calculate 30 days from now
expires_at = datetime.now() + timedelta(days=30)
expires_at_iso = expires_at.isoformat()

print(f"Updating subscription for user: {CLERK_USER_ID}")
print(f"Expiration date: {expires_at_iso}")
print()

# Update data
update_data = {
    "subscription_status": "trial",
    "subscription_period": "monthly",
    "subscription_expires_at": expires_at_iso,
    "subscription_will_renew": True,
    "is_in_trial": True,
    "updated_at": datetime.now().isoformat()
}

try:
    # First, check if user exists
    check_response = supabase.table("users").select("*").eq("clerk_user_id", CLERK_USER_ID).execute()

    if not check_response.data or len(check_response.data) == 0:
        print(f"❌ Error: User with clerk_user_id '{CLERK_USER_ID}' not found")
        sys.exit(1)

    print("✅ User found in database")
    print(f"Current subscription status: {check_response.data[0].get('subscription_status', 'none')}")
    print()

    # Update user subscription
    response = supabase.table("users").update(update_data).eq("clerk_user_id", CLERK_USER_ID).execute()

    if response.data and len(response.data) > 0:
        print("✅ Subscription updated successfully!")
        print()
        print("Updated values:")
        print(f"  - subscription_status: {response.data[0].get('subscription_status')}")
        print(f"  - subscription_period: {response.data[0].get('subscription_period')}")
        print(f"  - subscription_expires_at: {response.data[0].get('subscription_expires_at')}")
        print(f"  - subscription_will_renew: {response.data[0].get('subscription_will_renew')}")
        print(f"  - is_in_trial: {response.data[0].get('is_in_trial')}")
    else:
        print("❌ Error: Update did not return data")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error updating subscription: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
