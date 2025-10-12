"""
Generate Initial AI Questions and Store in Database

This script generates 500 AI questions covering all syllabus topics evenly.
Each topic gets questions with 40% easy, 40% medium, 20% hard distribution.

Usage:
    python generate_initial_questions.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent.agents.quiz_generator import QuizGeneratorAgent
from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client, Client
from datetime import datetime
import json
from typing import List, Dict

# ============================================================
# Topic Definitions (from syllabus)
# ============================================================

TOPICS = [
    # Part A - Securities Law
    "מבוא ודיני יסוד",  # Introduction and foundations
    "חוק ניירות ערך - הגדרות",  # Securities Law - Definitions
    "חוק ניירות ערך - חובות גילוי",  # Securities Law - Disclosure obligations
    "חוק ניירות ערך - עבירות",  # Securities Law - Offenses
    "חוק השקעות משותפות בנאמנות",  # Mutual Funds Law
    "דיני חברות רלוונטיים",  # Relevant Corporate Law
    "אחריות משפטית",  # Legal Liability
    "חוק איסור הלבנת הון",  # Anti-Money Laundering Law
    "רגולציה נוספת ושינויים",  # Additional Regulations

    # Part B - Professional Ethics
    "עקרונות אתיים כלליים",  # General Ethical Principles
    "הקוד האתי לשוק ההון",  # Ethical Code for Capital Markets
    "שירות הוגן ללקוחות",  # Fair Service to Clients
    "הבחנה בין ייעוץ לשיווק",  # Distinction between Advice and Marketing
    "חובת הנאמנות לאינטרס הלקוח",  # Fiduciary Duty
    "אי־תלות של היועץ",  # Independence of Advisor
    "חובות גילוי ללקוח",  # Disclosure Obligations to Client
    "התנהגות שאינה הולמת",  # Misconduct and Market Manipulation
    "סטנדרטים אתיים למקצוענות",  # Professional Ethical Standards
]

# ============================================================
# Configuration
# ============================================================

TOTAL_QUESTIONS = 500
QUESTIONS_PER_TOPIC = TOTAL_QUESTIONS // len(TOPICS)  # ~27-28 per topic

# Difficulty distribution
DIFFICULTY_DISTRIBUTION = {
    "easy": 0.40,    # 40%
    "medium": 0.40,  # 40%
    "hard": 0.20,    # 20%
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

def generate_questions_for_topic(
    generator: QuizGeneratorAgent,
    topic: str,
    difficulty: str,
    count: int
) -> List[Dict]:
    """
    Generate questions for a specific topic and difficulty

    Args:
        generator: QuizGeneratorAgent instance
        topic: Topic name
        difficulty: Difficulty level (easy/medium/hard)
        count: Number of questions to generate

    Returns:
        List of generated questions
    """
    print(f"  🔧 Generating {count} {difficulty} questions for: {topic}")

    try:
        result = generator.generate_quiz(
            question_count=count,
            topic=topic,
            difficulty=difficulty,
            focus_areas=None
        )

        questions = result.get('questions', [])
        print(f"     ✅ Generated {len(questions)} questions (validation passed)")

        return questions

    except Exception as e:
        print(f"     ❌ Error: {e}")
        return []

# ============================================================
# Database Insertion
# ============================================================

def insert_question_to_db(supabase: Client, question: Dict, topic: str) -> bool:
    """
    Insert a single question into ai_generated_questions table

    Args:
        supabase: Supabase client
        question: Question data from quiz_generator
        topic: Topic name

    Returns:
        True if successful, False otherwise
    """
    try:
        # Map quiz_generator format to database schema
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
            "sub_topic": question.get("topic"),  # quiz_generator's topic goes to sub_topic
            "difficulty_level": question.get("difficulty"),
            "legal_reference": question.get("legal_reference"),
            "is_active": True,
            "generated_by": "quiz_generator",
            "expert_validated": question.get("expert_validation", {}).get("validated", False),
            "expert_validation_data": json.dumps(question.get("expert_validation", {})) if question.get("expert_validation") else None
        }

        # Insert into database
        result = supabase.table("ai_generated_questions").insert(db_question).execute()

        if result.data:
            return True
        else:
            print(f"     ⚠️  No data returned from insert")
            return False

    except Exception as e:
        print(f"     ❌ Database error: {e}")
        return False

# ============================================================
# Main Generation Loop
# ============================================================

def generate_all_questions():
    """Main function to generate and store all questions"""

    print("=" * 80)
    print("🚀 AI Question Generation - Initial Dataset")
    print("=" * 80)
    print(f"Target: {TOTAL_QUESTIONS} questions")
    print(f"Topics: {len(TOPICS)}")
    print(f"Questions per topic: ~{QUESTIONS_PER_TOPIC}")
    print(f"Difficulty distribution: 40% easy, 40% medium, 20% hard")
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

    # Generate for each topic
    for topic_idx, topic in enumerate(TOPICS, 1):
        print(f"📚 Topic {topic_idx}/{len(TOPICS)}: {topic}")
        print("-" * 80)

        topic_stats = {"easy": 0, "medium": 0, "hard": 0}

        # Calculate questions per difficulty for this topic
        difficulty_counts = {
            "easy": int(QUESTIONS_PER_TOPIC * DIFFICULTY_DISTRIBUTION["easy"]),
            "medium": int(QUESTIONS_PER_TOPIC * DIFFICULTY_DISTRIBUTION["medium"]),
            "hard": int(QUESTIONS_PER_TOPIC * DIFFICULTY_DISTRIBUTION["hard"])
        }

        # Adjust for rounding (make sure we hit exactly QUESTIONS_PER_TOPIC)
        total = sum(difficulty_counts.values())
        if total < QUESTIONS_PER_TOPIC:
            difficulty_counts["medium"] += (QUESTIONS_PER_TOPIC - total)

        # Generate for each difficulty level
        for difficulty, count in difficulty_counts.items():
            if count == 0:
                continue

            # Generate questions (generator returns fewer after validation)
            # So we request 2x and take what we need
            questions = generate_questions_for_topic(
                generator=generator,
                topic=topic,
                difficulty=difficulty,
                count=count * 2  # Request 2x due to validation
            )

            # Take only what we need
            questions = questions[:count]

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
    print("📊 GENERATION COMPLETE")
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

    # Save stats to file
    stats_file = Path(__file__).parent / f"generation_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
        generate_all_questions()
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
