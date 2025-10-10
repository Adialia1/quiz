"""
Supabase Setup - Simple Verification Script

This script verifies your Supabase setup is complete.
To create tables, run the SQL script manually in Supabase dashboard.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY, validate_config

def verify_setup():
    """Verify Supabase setup"""

    print("\n" + "="*70)
    print("🔍 AI Ethica - Supabase Setup Verification")
    print("="*70 + "\n")

    # Validate config
    try:
        validate_config()
        print("✅ Configuration valid")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

    # Connect to Supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(f"✅ Connected to Supabase: {SUPABASE_URL}\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    # Check required tables
    required_tables = [
        'legal_doc_chunks',
        'exam_questions',
        'users',
        'user_performance',
        'chat_messages',
        'study_sessions',
        'topic_mastery'
    ]

    print("Checking tables...")
    print("-" * 70)

    all_exist = True
    for table in required_tables:
        try:
            # Try to query the table
            response = supabase.table(table).select('id').limit(1).execute()
            print(f"✅ {table}")
        except Exception as e:
            print(f"❌ {table} - NOT FOUND")
            all_exist = False

    print("-" * 70)

    if all_exist:
        print("\n🎉 All tables exist! Setup is complete.")

        # Show counts
        print("\nCurrent data:")
        try:
            legal_count = supabase.table('legal_doc_chunks').select('id', count='exact').execute().count
            exam_count = supabase.table('exam_questions').select('id', count='exact').execute().count

            print(f"   Legal chunks: {legal_count}")
            print(f"   Exam questions: {exam_count}")
        except:
            pass

        return True
    else:
        print("\n⚠️  Some tables are missing!")
        print("\nTo create tables:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Click 'SQL Editor' in left menu")
        print("4. Click 'New Query'")
        print("5. Copy contents of scripts/schema.sql")
        print("6. Paste and click 'Run'")
        print("\nOr open: scripts/schema.sql\n")

        return False


if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
