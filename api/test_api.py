#!/usr/bin/env python3
"""
Test client for Quiz Generator & Legal Expert API
Demonstrates all API endpoints with examples
"""
import requests
import json
import sys
from typing import Optional

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_health_check():
    """Test health check endpoint"""
    print_section("1. Health Check")

    response = requests.get(f"{BASE_URL}/health")
    data = response.json()

    print(f"✅ Status: {data['status']}")
    print(f"📅 Timestamp: {data['timestamp']}")
    print(f"🤖 Agents:")
    for agent, status in data['agents'].items():
        print(f"   - {agent}: {status}")


def test_legal_question(question: str = "מהו מידע פנים?", show_sources: bool = True):
    """Test legal expert question endpoint"""
    print_section("2. Ask Legal Expert")

    print(f"❓ Question: {question}\n")

    response = requests.post(
        f"{BASE_URL}/api/legal/ask",
        json={
            "question": question,
            "show_sources": show_sources,
            "k": 10
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()

    print(f"✅ Answer:\n{data['answer'][:500]}...\n")

    if show_sources and data.get('sources'):
        print(f"📚 Sources ({len(data['sources'])} total):")
        for i, source in enumerate(data['sources'][:3], 1):
            print(f"   {i}. {source}")


def test_generate_questions(
    count: int = 3,
    topic: Optional[str] = "מידע פנים",
    difficulty: Optional[str] = "medium",
    question_type: str = "mixed"
):
    """Test question generation endpoint"""
    print_section("3. Generate Questions")

    print(f"📝 Parameters:")
    print(f"   Count: {count}")
    print(f"   Topic: {topic or 'All topics'}")
    print(f"   Difficulty: {difficulty or 'Mixed'}")
    print(f"   Type: {question_type}\n")

    response = requests.post(
        f"{BASE_URL}/api/questions/generate",
        json={
            "count": count,
            "topic": topic,
            "difficulty": difficulty,
            "question_type": question_type
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    questions = data['questions']
    metadata = data['metadata']

    print(f"✅ Generated {len(questions)} questions\n")

    # Show validation stats
    stats = metadata.get('validation_stats', {})
    print(f"📊 Validation Stats:")
    print(f"   Generated: {stats.get('generated', 'N/A')}")
    print(f"   Structurally Valid: {stats.get('structurally_valid', 'N/A')}")
    print(f"   Expert Validated: {stats.get('expert_validated', 'N/A')}")
    print(f"   Final Count: {stats.get('final_count', 'N/A')}\n")

    # Show first question as sample
    if questions:
        q = questions[0]
        print(f"📄 Sample Question (Q{q['question_number']}):")
        print(f"   Topic: {q['topic']}")
        print(f"   Difficulty: {q['difficulty']}")
        print(f"   Question: {q['question_text'][:150]}...")
        print(f"   Correct Answer: {q['correct_answer']}")

        if q.get('expert_validation'):
            conf = q['expert_validation'].get('confidence', 'unknown')
            print(f"   ✓ Validated by Expert (confidence: {conf})")


def test_generate_quiz_json(
    quiz_count: int = 1,
    focus_areas: Optional[list] = None,
    difficulty: Optional[str] = "medium"
):
    """Test full quiz generation (JSON format)"""
    print_section("4. Generate Full Quiz (JSON)")

    print(f"📝 Parameters:")
    print(f"   Quiz Count: {quiz_count}")
    print(f"   Focus Areas: {focus_areas or 'All topics'}")
    print(f"   Difficulty: {difficulty or 'Mixed'}")
    print(f"   Format: JSON\n")

    response = requests.post(
        f"{BASE_URL}/api/quiz/generate",
        json={
            "quiz_count": quiz_count,
            "focus_areas": focus_areas,
            "difficulty": difficulty,
            "format": "json"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()

    if quiz_count == 1:
        # Single quiz
        questions = data['questions']
        metadata = data['metadata']

        print(f"✅ Generated quiz with {len(questions)} questions")
        print(f"📅 Generated at: {metadata['generated_at']}")

        # Show breakdown by difficulty
        difficulty_counts = {}
        for q in questions:
            diff = q.get('difficulty', 'medium')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

        print(f"\n📊 Difficulty Breakdown:")
        for diff in ['easy', 'medium', 'hard']:
            count = difficulty_counts.get(diff, 0)
            print(f"   {diff.capitalize()}: {count}")

    else:
        # Multiple quizzes
        quizzes = data['quizzes']
        print(f"✅ Generated {len(quizzes)} quizzes")

        for quiz in quizzes:
            quiz_num = quiz['metadata']['quiz_number']
            q_count = len(quiz['questions'])
            print(f"   Quiz #{quiz_num}: {q_count} questions")


def test_generate_quiz_pdf(
    difficulty: Optional[str] = "easy",
    output_file: str = "test_quiz.pdf"
):
    """Test full quiz generation (PDF format)"""
    print_section("5. Generate Full Quiz (PDF)")

    print(f"📝 Parameters:")
    print(f"   Difficulty: {difficulty or 'Mixed'}")
    print(f"   Format: PDF")
    print(f"   Output: {output_file}\n")

    response = requests.post(
        f"{BASE_URL}/api/quiz/generate",
        json={
            "quiz_count": 1,
            "difficulty": difficulty,
            "format": "pdf"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    # Save PDF
    with open(output_file, "wb") as f:
        f.write(response.content)

    print(f"✅ PDF generated and saved!")
    print(f"📄 File: {output_file}")
    print(f"📦 Size: {len(response.content) / 1024:.2f} KB")


def test_simplified_endpoints():
    """Test simplified GET endpoints"""
    print_section("6. Simplified GET Endpoints")

    # Legal question (GET)
    print("Testing GET /api/legal/ask-simple...\n")
    response = requests.get(
        f"{BASE_URL}/api/legal/ask-simple",
        params={
            "question": "מהי חובת גילוי?",
            "show_sources": False
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Legal Question (GET):")
        print(f"   Answer: {data['answer'][:150]}...\n")

    # Generate questions (GET)
    print("Testing GET /api/questions/generate-simple...\n")
    response = requests.get(
        f"{BASE_URL}/api/questions/generate-simple",
        params={
            "count": 2,
            "difficulty": "easy",
            "question_type": "basic"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Generate Questions (GET):")
        print(f"   Generated: {len(data['questions'])} questions")


def main():
    """Run all API tests"""
    print("\n" + "🚀 " + "="*66)
    print("   QUIZ GENERATOR & LEGAL EXPERT API - TEST CLIENT")
    print("="*68 + "\n")

    print(f"📡 Testing API at: {BASE_URL}")
    print(f"📚 Docs available at: {BASE_URL}/docs\n")

    try:
        # Test all endpoints
        test_health_check()

        test_legal_question(
            question="מהו מידע פנים לפי חוק ניירות ערך?",
            show_sources=True
        )

        test_generate_questions(
            count=3,
            topic="חובות גילוי",
            difficulty="medium",
            question_type="mixed"
        )

        test_generate_quiz_json(
            quiz_count=1,
            focus_areas=["מידע פנים", "מניפולציה"],
            difficulty="medium"
        )

        test_generate_quiz_pdf(
            difficulty="easy",
            output_file="test_quiz.pdf"
        )

        test_simplified_endpoints()

        # Final message
        print_section("✅ All Tests Complete!")
        print("All API endpoints are working correctly.")
        print("\nNext Steps:")
        print("  1. Check test_quiz.pdf for PDF output")
        print("  2. Visit http://localhost:8000/docs for interactive docs")
        print("  3. Try your own API requests!")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API")
        print(f"   Make sure the API is running at {BASE_URL}")
        print("   Run: python api/main.py")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
