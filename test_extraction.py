#!/usr/bin/env python3
"""
Quick test script to verify all 25 questions are extracted
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from ingestion.llm_exam_parser import LLMExamParser

def main():
    pdf_path = "SecuritiesEthic2024.pdf"

    print(f"Testing extraction on {pdf_path}...\n")

    parser = LLMExamParser()
    result = parser.parse_pdf(pdf_path, verbose=True)

    print(f"\n{'='*70}")
    print(f"📊 EXTRACTION RESULTS")
    print(f"{'='*70}")
    print(f"Total questions extracted: {len(result['questions'])}")
    print(f"Questions with answers: {result['metadata']['questions_with_answers']}")

    # Check for Question 13 specifically
    q13 = next((q for q in result['questions'] if q.get('question_number') == 13), None)
    if q13:
        print(f"\n✅ Question 13 found!")
        print(f"   Text: {q13['question_text'][:100]}...")
    else:
        print(f"\n❌ Question 13 MISSING!")

    # Check for "נתונים לשאלות" in questions 22-23
    for q_num in [22, 23]:
        q = next((q for q in result['questions'] if q.get('question_number') == q_num), None)
        if q:
            has_context = 'נתונים לשאלות' in q['question_text']
            print(f"\n{'✅' if has_context else '⚠️'} Question {q_num}:")
            print(f"   Has context: {has_context}")
            print(f"   Text preview: {q['question_text'][:150]}...")

    # Show low confidence questions
    low_conf = [
        q for q in result['questions']
        if q.get('semantic_validation', {}).get('confidence', 1.0) < 0.7
    ]

    if low_conf:
        print(f"\n⚠️  {len(low_conf)} questions with low confidence:")
        for q in low_conf:
            conf = q.get('semantic_validation', {}).get('confidence', 0)
            reason = q.get('semantic_validation', {}).get('reason', '')
            print(f"   Q{q.get('question_number')}: {conf:.1%} - {reason}")

    print(f"\n{'='*70}")

if __name__ == "__main__":
    main()
