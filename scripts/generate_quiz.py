#!/usr/bin/env python3
"""
Quiz Generation Script
Generate personalized exam questions using Quiz Generator Agent

Usage:
    # Generate 10 general questions (mixed difficulty)
    python scripts/generate_quiz.py

    # Generate 15 questions on specific topic
    python scripts/generate_quiz.py --count 15 --topic "מידע פנים"

    # Generate 20 easy questions
    python scripts/generate_quiz.py --count 20 --difficulty easy

    # Focus on weak areas
    python scripts/generate_quiz.py --count 25 --focus "מידע פנים" "חובות גילוי" "מניפולציה"
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from agents.quiz_generator import QuizGeneratorAgent


def main():
    parser = argparse.ArgumentParser(
        description='Generate personalized exam questions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10 general questions
  python scripts/generate_quiz.py

  # Generate 15 questions on insider trading
  python scripts/generate_quiz.py --count 15 --topic "מידע פנים"

  # Generate 20 easy questions
  python scripts/generate_quiz.py --count 20 --difficulty easy

  # Focus on specific weak areas
  python scripts/generate_quiz.py --count 25 --focus "מידע פנים" "חובות גילוי"

  # Generate hard questions on manipulation
  python scripts/generate_quiz.py --count 10 --topic "מניפולציה" --difficulty hard
        """
    )

    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of questions to generate (default: 10)'
    )
    parser.add_argument(
        '--topic',
        type=str,
        help='Specific topic to focus on (e.g., "מידע פנים", "חובות גילוי")'
    )
    parser.add_argument(
        '--difficulty',
        choices=['easy', 'medium', 'hard'],
        help='Difficulty level (default: mixed)'
    )
    parser.add_argument(
        '--focus',
        nargs='+',
        help='List of focus areas/weak points (multiple topics)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path (default: generated_quiz_TIMESTAMP.json)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'text', 'both', 'pdf', 'all'],
        default='all',
        help='Output format (default: all - json, text, and pdf)'
    )

    parser.add_argument(
        '--no-pdf',
        action='store_true',
        help='Skip PDF generation'
    )

    args = parser.parse_args()

    print("="*70)
    print("🎓 QUIZ GENERATOR")
    print("="*70)
    print(f"\n📝 Configuration:")
    print(f"   Questions: {args.count}")
    print(f"   Topic: {args.topic or 'General (all topics)'}")
    print(f"   Difficulty: {args.difficulty or 'Mixed'}")
    print(f"   Focus areas: {args.focus or 'None'}")
    print(f"\n{'='*70}\n")

    # Initialize agent
    print("🤖 Initializing Quiz Generator Agent...")
    agent = QuizGeneratorAgent()
    print()

    # Generate quiz
    print("🔄 Generating quiz (this may take 1-2 minutes)...\n")

    result = agent.generate_quiz(
        question_count=args.count,
        topic=args.topic,
        difficulty=args.difficulty,
        focus_areas=args.focus
    )

    questions = result['questions']
    metadata = result['metadata']

    # Print results
    print("="*70)
    print("📊 GENERATION COMPLETE")
    print("="*70)
    print(f"\n✅ Generated: {len(questions)}/{args.count} questions")
    print(f"📖 Topic: {metadata['topic']}")
    print(f"📈 Difficulty: {metadata['difficulty']}")

    if not questions:
        print("\n❌ No questions were generated. Please try again.")
        return

    # Show summary by difficulty
    difficulty_counts = {}
    topic_counts = {}

    for q in questions:
        diff = q.get('difficulty', 'medium')
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

        topic = q.get('topic', 'Unknown')
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    print(f"\n📊 Breakdown by difficulty:")
    for diff in ['easy', 'medium', 'hard']:
        count = difficulty_counts.get(diff, 0)
        print(f"   {diff.capitalize()}: {count}")

    print(f"\n📚 Breakdown by topic:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"   {topic}: {count}")

    # Save outputs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Determine base path for outputs
    base_path = args.output.rsplit('.', 1)[0] if args.output else f"generated_quiz_{timestamp}"
    json_path = None

    # JSON output
    if args.format in ['json', 'both', 'all']:
        json_path = args.output or f"{base_path}.json"

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Saved JSON: {json_path}")

    # Text output
    if args.format in ['text', 'both', 'all']:
        text_path = f"{base_path}.txt"

        with open(text_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write(f"מבחן נוצר אוטומטית - {metadata['generated_at']}\n")
            f.write("="*70 + "\n\n")
            f.write(f"נושא: {metadata['topic']}\n")
            f.write(f"רמת קושי: {metadata['difficulty']}\n")
            f.write(f"מספר שאלות: {len(questions)}\n")
            f.write("="*70 + "\n\n")

            for i, q in enumerate(questions, 1):
                f.write(f"\nשאלה {i}:\n")
                f.write(f"{q['question_text']}\n\n")

                for opt_key in ['A', 'B', 'C', 'D', 'E']:
                    opt_text = q['options'].get(opt_key, '')
                    f.write(f"  {opt_key}. {opt_text}\n")

                f.write(f"\n✓ תשובה נכונה: {q['correct_answer']}\n")

                if q.get('explanation'):
                    f.write(f"\n💡 הסבר:\n{q['explanation']}\n")

                if q.get('legal_reference'):
                    f.write(f"\n📖 מקור משפטי:\n{q['legal_reference']}\n")

                f.write(f"\n🏷️ נושא: {q.get('topic', 'לא ידוע')}\n")
                f.write(f"📊 רמת קושי: {q.get('difficulty', 'medium')}\n")
                f.write("\n" + "-"*70 + "\n")

        print(f"💾 Saved Text: {text_path}")

    # PDF output
    if args.format in ['pdf', 'all'] and not args.no_pdf and json_path:
        try:
            # Use HTML-based PDF (perfect Hebrew support)
            from scripts.quiz_to_pdf import create_quiz_pdf_html

            pdf_path = f"{base_path}.pdf"
            print(f"\n📄 Generating PDF...")
            create_quiz_pdf_html(json_path, pdf_path)
        except ImportError as e:
            print(f"\n⚠️  Could not generate PDF: {e}")
            print("   Install required package: pip install weasyprint")
        except Exception as e:
            print(f"\n⚠️  PDF generation failed: {e}")

    # Print sample question
    if questions:
        print(f"\n{'='*70}")
        print("📝 SAMPLE QUESTION")
        print(f"{'='*70}\n")

        sample = questions[0]
        print(f"שאלה: {sample['question_text']}\n")

        for opt_key in ['A', 'B', 'C', 'D', 'E']:
            opt_text = sample['options'].get(opt_key, '')
            print(f"  {opt_key}. {opt_text}")

        print(f"\n✓ תשובה נכונה: {sample['correct_answer']}")
        print(f"\n💡 הסבר (first 200 chars):")
        print(f"   {sample.get('explanation', '')[:200]}...")
        print(f"\n🏷️ נושא: {sample.get('topic', 'לא ידוע')}")
        print(f"📊 רמת קושי: {sample.get('difficulty', 'medium')}")

    print(f"\n{'='*70}\n")
    print("✅ Quiz generation complete!")
    print(f"📁 Files saved in current directory")


if __name__ == "__main__":
    main()
