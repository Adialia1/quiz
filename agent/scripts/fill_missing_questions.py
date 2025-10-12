"""
Fill Missing AI Questions

This script analyzes the generation stats and fills in missing questions
to reach the target distribution of 500 questions.

Usage:
    python fill_missing_questions.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent.agents.quiz_generator import QuizGeneratorAgent
from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client, Client
from datetime import datetime
import json
from typing import List, Dict, Tuple

# ============================================================
# Configuration
# ============================================================

TOTAL_QUESTIONS = 500
QUESTIONS_PER_TOPIC = 27  # Target per topic

# Target distribution per topic
TARGET_DISTRIBUTION = {
    "easy": 11,
    "medium": 11,
    "hard": 5
}

# Missing questions (from stats file)
MISSING_QUESTIONS = {
    "מבוא ודיני יסוד": {"easy": 0, "medium": 11, "hard": 0},
    "חוק ניירות ערך - עבירות": {"easy": 0, "medium": 12, "hard": 0},
    "חוק השקעות משותפות בנאמנות": {"easy": 0, "medium": 0, "hard": 5},
    "חוק איסור הלבנת הון": {"easy": 0, "medium": 12, "hard": 0},
    "עקרונות אתיים כלליים": {"easy": 0, "medium": 0, "hard": 5},
    "אי־תלות של היועץ": {"easy": 10, "medium": 12, "hard": 0},
}

# ============================================================
# Database Setup
# ============================================================

def init_supabase() -> Client:
    """Initialize Supabase client"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("Missing Supabase credentials. Check .env file.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ============================================================
# Question Generation
# ============================================================

def generate_questions_with_retry(
    generator: QuizGeneratorAgent,
    topic: str,
    difficulty: str,
    target_count: int,
    max_attempts: int = 5
) -> List[Dict]:
    """
    Generate questions with multiple attempts to reach target count

    Args:
        generator: QuizGeneratorAgent instance
        topic: Topic name
        difficulty: Difficulty level
        target_count: Target number of questions
        max_attempts: Maximum generation attempts

    Returns:
        List of generated questions
    """
    all_questions = []
    attempt = 1

    while len(all_questions) < target_count and attempt <= max_attempts:
        needed = target_count - len(all_questions)
        # Request 3x what we need to account for validation
        request_count = needed * 3

        print(f"    Attempt {attempt}/{max_attempts}: Requesting {request_count} questions (need {needed} more)")

        try:
            result = generator.generate_quiz(
                question_count=request_count,
                topic=topic,
                difficulty=difficulty,
                focus_areas=None
            )

            questions = result.get('questions', [])
            print(f"    Generated {len(questions)} questions after validation")

            all_questions.extend(questions)
            attempt += 1

        except Exception as e:
            print(f"    Error: {e}")
            attempt += 1

    # Take only what we need
    final_questions = all_questions[:target_count]
    print(f"    ✅ Got {len(final_questions)}/{target_count} questions")

    return final_questions

# ============================================================
# Database Insertion
# ============================================================

def insert_question_to_db(supabase: Client, question: Dict, topic: str) -> bool:
    """Insert a single question into ai_generated_questions table"""
    try:
        db_question = {
            "question_text": question.get("question_text"),
            "option_a": question.get("options", {}).get("A"),
            "option_b": question.get("options", {}).get("B"),
            "option_c": question.get("options", {}).get("C"),
            "option_d": question.get("options", {}).get("D"),
            "option_e": question.get("options", {}).get("E"),
            "correct_answer": question.get("correct_answer"),
            "explanation": question.get("explanation"),
            "topic": topic,
            "sub_topic": question.get("topic"),
            "difficulty_level": question.get("difficulty"),
            "legal_reference": question.get("legal_reference"),
            "is_active": True,
            "generated_by": "quiz_generator",
            "expert_validated": question.get("expert_validation", {}).get("validated", False),
            "expert_validation_data": json.dumps(question.get("expert_validation", {})) if question.get("expert_validation") else None
        }

        result = supabase.table("ai_generated_questions").insert(db_question).execute()
        return bool(result.data)

    except Exception as e:
        print(f"    ❌ Database error: {e}")
        return False

# ============================================================
# Main Fill Loop
# ============================================================

def fill_missing_questions():
    """Fill in missing questions to reach target of 500"""

    print("=" * 80)
    print("🔧 Fill Missing AI Questions")
    print("=" * 80)

    # Calculate total missing
    total_missing = sum(
        sum(difficulties.values())
        for difficulties in MISSING_QUESTIONS.values()
    )

    print(f"Target: 500 questions")
    print(f"Current: 418 questions")
    print(f"Missing: {total_missing} questions")
    print(f"Topics to fill: {len(MISSING_QUESTIONS)}")
    print("=" * 80)
    print()

    # Initialize
    print("🔧 Initializing...")
    generator = QuizGeneratorAgent()
    supabase = init_supabase()
    print("✅ Initialization complete")
    print()

    # Statistics
    stats = {
        "total_generated": 0,
        "total_inserted": 0,
        "by_topic": {},
        "by_difficulty": {"easy": 0, "medium": 0, "hard": 0},
        "failed": 0
    }

    # Fill each topic
    for topic_idx, (topic, missing) in enumerate(MISSING_QUESTIONS.items(), 1):
        # Check if this topic needs anything
        total_needed = sum(missing.values())
        if total_needed == 0:
            continue

        print(f"📚 Topic {topic_idx}/{len(MISSING_QUESTIONS)}: {topic}")
        print(f"   Need: {missing['easy']}E, {missing['medium']}M, {missing['hard']}H")
        print("-" * 80)

        topic_stats = {"easy": 0, "medium": 0, "hard": 0}

        # Generate for each difficulty that needs questions
        for difficulty, count in missing.items():
            if count == 0:
                continue

            print(f"  🔧 Generating {count} {difficulty} questions...")

            # Generate with retry
            questions = generate_questions_with_retry(
                generator=generator,
                topic=topic,
                difficulty=difficulty,
                target_count=count,
                max_attempts=5
            )

            # Insert each question
            inserted_count = 0
            for question in questions:
                if insert_question_to_db(supabase, question, topic):
                    inserted_count += 1
                    stats["total_inserted"] += 1
                    stats["by_difficulty"][difficulty] += 1
                    topic_stats[difficulty] += 1
                else:
                    stats["failed"] += 1

            stats["total_generated"] += len(questions)
            print(f"     💾 Inserted {inserted_count}/{count} {difficulty} questions")

        # Topic summary
        stats["by_topic"][topic] = topic_stats
        print(f"  ✅ Topic complete: {sum(topic_stats.values())} questions inserted")
        print()

    # Final summary
    print("=" * 80)
    print("📊 FILL COMPLETE")
    print("=" * 80)
    print(f"Total Generated: {stats['total_generated']}")
    print(f"Total Inserted: {stats['total_inserted']}")
    print(f"Failed: {stats['failed']}")
    print()
    print("By Difficulty:")
    print(f"  Easy:   {stats['by_difficulty']['easy']}")
    print(f"  Medium: {stats['by_difficulty']['medium']}")
    print(f"  Hard:   {stats['by_difficulty']['hard']}")
    print()
    print("By Topic:")
    for topic, counts in stats["by_topic"].items():
        total = sum(counts.values())
        print(f"  {topic}: {total} ({counts['easy']}E, {counts['medium']}M, {counts['hard']}H)")
    print("=" * 80)

    # Calculate new total
    new_total = 418 + stats['total_inserted']
    print(f"📊 New Total: {new_total}/500 questions")
    print()

    # Save stats
    stats_file = Path(__file__).parent / f"fill_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"📄 Stats saved to: {stats_file}")
    print()
    print("✅ All done!")

# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    try:
        fill_missing_questions()
    except KeyboardInterrupt:
        print("\n\n⚠️  Fill interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
