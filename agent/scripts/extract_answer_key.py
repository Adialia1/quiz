"""
Extract Answer Key from JSON
Creates a simple question number -> correct answer mapping
"""

import json
import sys
from pathlib import Path


def extract_answer_key(json_file: str, output_format: str = "text"):
    """
    Extract answer key from validated questions JSON

    Args:
        json_file: Path to JSON file with questions
        output_format: 'text', 'table', or 'json'
    """
    # Read JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Sort by question number
    questions_sorted = sorted(questions, key=lambda q: q.get('question_number', 0))

    if output_format == 'text':
        # Simple text format
        print("\n" + "="*50)
        print("ANSWER KEY")
        print("="*50 + "\n")

        for q in questions_sorted:
            q_num = q.get('question_number', '?')
            answer = q.get('correct_answer', '?')
            print(f"Question number: {q_num}")
            print(f"Correct answer: {answer}")
            print()

    elif output_format == 'table':
        # Table format
        print("\n" + "="*50)
        print("ANSWER KEY")
        print("="*50)
        print(f"{'Question':<15} {'Correct Answer':<15}")
        print("-"*50)

        for q in questions_sorted:
            q_num = q.get('question_number', '?')
            answer = q.get('correct_answer', '?')
            print(f"{q_num:<15} {answer:<15}")

        print("="*50)

    elif output_format == 'compact':
        # Very compact format
        print("\nAnswer Key:")
        print("-" * 30)

        for q in questions_sorted:
            q_num = q.get('question_number', '?')
            answer = q.get('correct_answer', '?')
            print(f"{q_num:>2}. {answer}")

    elif output_format == 'json':
        # JSON output
        answer_key = {
            str(q.get('question_number', '?')): q.get('correct_answer', '?')
            for q in questions_sorted
        }
        print(json.dumps(answer_key, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_answer_key.py <json_file> [format]")
        print("Formats: text (default), table, compact, json")
        sys.exit(1)

    json_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else 'text'

    if not Path(json_file).exists():
        print(f"Error: File not found: {json_file}")
        sys.exit(1)

    extract_answer_key(json_file, output_format)


if __name__ == "__main__":
    main()
