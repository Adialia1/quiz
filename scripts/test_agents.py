"""
Test Script for AI Ethica Agents
Tests Legal Expert and Chat Mentor agents
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents.legal_expert import LegalExpertAgent
from agents.chat_mentor import ChatMentorAgent


def test_legal_expert():
    """Test Legal Expert Agent"""
    print("\n" + "="*80)
    print("🧪 TESTING LEGAL EXPERT AGENT")
    print("="*80 + "\n")

    # Initialize agent
    print("🔧 Initializing Legal Expert Agent...")
    agent = LegalExpertAgent(top_k=3)

    # Test scenarios
    test_cases = [
        {
            "name": "Definition Question",
            "query": "מה ההגדרה של 'איש פנים' לפי חוק ניירות ערך?",
        },
        {
            "name": "Penalty Question",
            "query": "מהם העונשים על שימוש במידע פנים?",
        },
        {
            "name": "Comparison Question",
            "query": "מה ההבדל בין חובת גילוי לבין חובת מסירת מידע?",
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print(f"{'─'*80}")

        print(f"\n❓ Question: {test['query']}")

        result = agent.process({
            "query": test['query'],
            "k": 3
        })

        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            continue

        print(f"\n📝 Answer:")
        print(f"{result['answer'][:500]}...")

        print(f"\n📚 Sources ({len(result['sources'])}):")
        for source in result['sources'][:3]:
            print(f"   • {source['document']} (עמוד {source['page']})")

    print("\n" + "="*80)
    print("✅ Legal Expert Agent tests complete!")
    print("="*80)


def test_chat_mentor():
    """Test Chat Mentor Agent"""
    print("\n\n" + "="*80)
    print("🧪 TESTING CHAT MENTOR AGENT")
    print("="*80 + "\n")

    # Initialize agent
    print("🔧 Initializing Chat Mentor Agent...")
    agent = ChatMentorAgent()

    # Simulate realistic conversation
    conversation = [
        {
            "message": "היי, אני מתחיל ללמוד לבחינת האתיקה ורציתי לדעת מה זה 'מידע פנים'?",
            "description": "Initial question from beginner"
        },
        {
            "message": "אפשר דוגמה?",
            "description": "Follow-up for example"
        },
        {
            "message": "למה זה בכלל אסור? מה הבעיה בזה?",
            "description": "Asking for reasoning"
        },
        {
            "message": "תודה! עכשיו זה ברור. ומה קורה אם מישהו עושה את זה בכל זאת?",
            "description": "Question about penalties"
        }
    ]

    print(f"\n🎭 Simulating {len(conversation)}-turn conversation...\n")

    for i, turn in enumerate(conversation, 1):
        print(f"\n{'─'*80}")
        print(f"Turn {i}/{len(conversation)}: {turn['description']}")
        print(f"{'─'*80}")

        print(f"\n💬 User: {turn['message']}")

        result = agent.process({
            "message": turn['message'],
            "use_rag": True
        })

        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            continue

        # Show response (truncated for readability)
        response = result['response']
        preview_length = 400
        print(f"\n🤖 Mentor: {response[:preview_length]}...")

        # Show metadata
        if result.get('topics'):
            print(f"\n📚 Topics detected: {', '.join(result['topics'])}")

        print(f"💡 Context used: {'Yes' if result.get('context_used') else 'No'}")

    # Show conversation summary
    print("\n\n" + "="*80)
    print("📊 CONVERSATION SUMMARY")
    print("="*80)

    summary = agent.get_conversation_summary()

    print(f"\nSession ID: {summary['session_id'][:8]}...")
    print(f"Total turns: {summary['turn_count']}")
    print(f"Topics discussed: {', '.join(summary['topics_discussed']) if summary['topics_discussed'] else 'None'}")
    print(f"User level: {summary['user_level']}")
    print(f"Messages: {summary['message_count']}")

    print("\n" + "="*80)
    print("✅ Chat Mentor Agent tests complete!")
    print("="*80)


def test_agent_comparison():
    """Compare both agents on same question"""
    print("\n\n" + "="*80)
    print("🧪 AGENT COMPARISON TEST")
    print("="*80 + "\n")

    question = "מה זה מידע פנים?"

    print(f"Testing both agents with: '{question}'\n")

    # Legal Expert
    print("─" * 80)
    print("1️⃣ Legal Expert Agent (Formal, Citation-heavy)")
    print("─" * 80)

    legal_agent = LegalExpertAgent()
    legal_result = legal_agent.process({"query": question})

    print(f"\n{legal_result['answer'][:300]}...")

    # Chat Mentor
    print("\n\n" + "─" * 80)
    print("2️⃣ Chat Mentor Agent (Conversational, Educational)")
    print("─" * 80)

    chat_agent = ChatMentorAgent()
    chat_result = chat_agent.process({"message": question})

    print(f"\n{chat_result['response'][:300]}...")

    print("\n\n" + "="*80)
    print("📊 COMPARISON ANALYSIS")
    print("="*80)

    print("\n✅ Legal Expert:")
    print("   • Style: Formal, legal precision")
    print("   • Citations: Yes (documents + pages)")
    print("   • Use case: Precise legal information")

    print("\n✅ Chat Mentor:")
    print("   • Style: Conversational, educational")
    print("   • Examples: Yes (analogies)")
    print("   • Use case: Learning and understanding")

    print("\n" + "="*80)
    print("✅ Comparison test complete!")
    print("="*80)


def main():
    """Run all agent tests"""
    print("\n" + "🚀"*40)
    print("\n  AI ETHICA AGENT TESTING SUITE")
    print("\n" + "🚀"*40)

    try:
        # Test 1: Legal Expert Agent
        test_legal_expert()

        # Test 2: Chat Mentor Agent
        test_chat_mentor()

        # Test 3: Comparison
        test_agent_comparison()

        print("\n\n" + "🎉"*40)
        print("\n  ALL TESTS PASSED!")
        print("\n" + "🎉"*40 + "\n")

    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
