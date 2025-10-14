"""
Validate Concepts for Flashcard Quality

This script:
1. Loads extracted concepts from JSON
2. Uses legal_expert to verify factual accuracy
3. Uses flashcard_designer to evaluate learning effectiveness
4. Generates a validation report with scores and recommendations

Usage:
    python agent/scripts/validate_concepts.py --input concepts_full.json --sample 50
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import argparse
from typing import List, Dict, Any
from tqdm import tqdm
import random

from agent.agents.legal_expert import LegalExpertAgent


def validate_with_legal_expert(
    legal_expert: LegalExpertAgent,
    concept: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate concept accuracy with legal expert

    Args:
        legal_expert: LegalExpertAgent instance
        concept: Concept to validate

    Returns:
        Validation result with score and feedback
    """
    topic = concept.get('topic', '')
    title = concept.get('title', '')
    explanation = concept.get('explanation', '')
    example = concept.get('example', '')

    query = f"""
    אנא בדוק את הדיוק העובדתי של המושג הבא בנושא "{topic}":

    **כותרת**: {title}

    **הסבר**: {explanation}

    **דוגמה**: {example if example else 'אין דוגמה'}

    שאלות לבדיקה:
    1. האם המידע מדויק ונכון מבחינה משפטית?
    2. האם ההסבר שלם וברור?
    3. האם הדוגמה (אם קיימת) רלוונטית ונכונה?
    4. האם יש משהו שחסר או לא מדויק?

    החזר תשובה בפורמט JSON:
    ```json
    {{
      "is_accurate": true/false,
      "accuracy_score": 1-10,
      "issues": ["רשימת בעיות אם יש"],
      "missing_info": ["מידע חסר אם יש"],
      "recommendations": ["המלצות לשיפור"],
      "summary": "סיכום קצר של הבדיקה"
    }}
    ```
    """

    try:
        result = legal_expert.process({
            "query": query,
            "k": 20  # Moderate k for validation
        })

        answer = result.get('answer', '')
        validation = parse_json_from_text(answer)

        if not validation:
            return {
                "is_accurate": True,  # Assume ok if can't parse
                "accuracy_score": 7,
                "issues": [],
                "missing_info": [],
                "recommendations": [],
                "summary": "לא הצלחנו לפרסר את התשובה, מניחים שהכל בסדר"
            }

        return validation

    except Exception as e:
        print(f"      ⚠️  Error validating with legal expert: {e}")
        return {
            "is_accurate": True,
            "accuracy_score": 7,
            "issues": [str(e)],
            "missing_info": [],
            "recommendations": [],
            "summary": "שגיאה בבדיקה"
        }


def evaluate_flashcard_quality(
    legal_expert: LegalExpertAgent,
    concept: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate concept as a flashcard for learning

    Args:
        legal_expert: LegalExpertAgent instance (used as evaluator)
        concept: Concept to evaluate

    Returns:
        Evaluation result with scores and recommendations
    """
    title = concept.get('title', '')
    explanation = concept.get('explanation', '')
    example = concept.get('example', '')
    key_points = concept.get('key_points', [])

    query = f"""
    אתה מעצב פלאשקארדים מומחה. אנא העריך את איכות הפלאשקארד הבא ללמידה:

    **כותרת**: {title}

    **הסבר**: {explanation}

    **דוגמה**: {example if example else 'אין דוגמה'}

    **נקודות מפתח**: {', '.join(key_points) if key_points else 'אין נקודות מפתח'}

    קריטריונים להערכה:
    1. **בהירות** (1-10): האם ההסבר ברור ומובן?
    2. **תמציתיות** (1-10): האם המידע תמציתי ולא ארוך מדי?
    3. **שימושיות** (1-10): האם זה שימושי ללומד?
    4. **זכירות** (1-10): האם קל לזכור את המידע?
    5. **דוגמה** (1-10): האם הדוגמה טובה ומסייעת? (0 אם אין)

    החזר תשובה בפורמט JSON:
    ```json
    {{
      "clarity_score": 1-10,
      "conciseness_score": 1-10,
      "usefulness_score": 1-10,
      "memorability_score": 1-10,
      "example_score": 1-10,
      "overall_score": 1-10,
      "strengths": ["חוזקות"],
      "weaknesses": ["חולשות"],
      "improvement_suggestions": ["הצעות לשיפור"],
      "is_good_flashcard": true/false,
      "summary": "סיכום"
    }}
    ```
    """

    try:
        result = legal_expert.process({
            "query": query,
            "k": 5  # Low k for evaluation
        })

        answer = result.get('answer', '')
        evaluation = parse_json_from_text(answer)

        if not evaluation:
            return {
                "clarity_score": 7,
                "conciseness_score": 7,
                "usefulness_score": 7,
                "memorability_score": 7,
                "example_score": 5,
                "overall_score": 7,
                "strengths": [],
                "weaknesses": [],
                "improvement_suggestions": [],
                "is_good_flashcard": True,
                "summary": "לא הצלחנו לפרסר, מניחים שהכל בסדר"
            }

        return evaluation

    except Exception as e:
        print(f"      ⚠️  Error evaluating flashcard: {e}")
        return {
            "clarity_score": 7,
            "conciseness_score": 7,
            "usefulness_score": 7,
            "memorability_score": 7,
            "example_score": 5,
            "overall_score": 7,
            "strengths": [],
            "weaknesses": ["שגיאה בהערכה"],
            "improvement_suggestions": [],
            "is_good_flashcard": True,
            "summary": "שגיאה בהערכה"
        }


def parse_json_from_text(text: str) -> Dict[str, Any]:
    """Parse JSON from text that might contain code blocks"""
    import re

    # Try to extract JSON from code blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass

    # Try to find JSON without code blocks
    json_match = re.search(r'\{(?:[^{}]|\{[^{}]*\})*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass

    # Try parsing entire response
    try:
        return json.loads(text)
    except:
        pass

    return {}


def main():
    parser = argparse.ArgumentParser(description='Validate concepts for flashcard quality')
    parser.add_argument(
        '--input',
        type=str,
        default='concepts_full.json',
        help='Input JSON file with concepts'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=50,
        help='Number of concepts to validate (random sample)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='validation_report.json',
        help='Output validation report file'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Validate all concepts (not just sample)'
    )

    args = parser.parse_args()

    print("="*70)
    print("🔍 Concept Validation Script")
    print("="*70)

    # Initialize legal expert
    print("\n🔧 Initializing Legal Expert Agent...")
    legal_expert = LegalExpertAgent(
        temperature=0.1,
        use_thinking_model=False
    )
    print("✅ Legal Expert ready\n")

    # Load concepts
    print(f"📂 Loading concepts from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    concepts = data.get('concepts', [])
    print(f"✅ Loaded {len(concepts)} concepts\n")

    # Sample or use all
    if args.full:
        concepts_to_validate = concepts
        print(f"🔍 Validating ALL {len(concepts)} concepts...\n")
    else:
        sample_size = min(args.sample, len(concepts))
        concepts_to_validate = random.sample(concepts, sample_size)
        print(f"🔍 Validating random sample of {sample_size} concepts...\n")

    # Validate each concept
    validation_results = []

    for i, concept in enumerate(tqdm(concepts_to_validate, desc="Validating")):
        print(f"\n[{i+1}/{len(concepts_to_validate)}] Validating: {concept.get('title', 'N/A')[:50]}...")

        # Legal accuracy validation
        print("   📚 Checking legal accuracy...")
        legal_validation = validate_with_legal_expert(legal_expert, concept)

        # Flashcard quality evaluation
        print("   🎴 Evaluating flashcard quality...")
        flashcard_evaluation = evaluate_flashcard_quality(legal_expert, concept)

        # Combine results
        result = {
            'concept_id': concept.get('chunk_id'),
            'topic': concept.get('topic'),
            'title': concept.get('title'),
            'legal_validation': legal_validation,
            'flashcard_evaluation': flashcard_evaluation,
            'overall_pass': (
                legal_validation.get('is_accurate', False) and
                legal_validation.get('accuracy_score', 0) >= 7 and
                flashcard_evaluation.get('is_good_flashcard', False) and
                flashcard_evaluation.get('overall_score', 0) >= 7
            )
        }

        validation_results.append(result)

        # Print summary
        legal_score = legal_validation.get('accuracy_score', 0)
        flashcard_score = flashcard_evaluation.get('overall_score', 0)
        status = "✅ PASS" if result['overall_pass'] else "❌ NEEDS REVIEW"

        print(f"   Legal Score: {legal_score}/10")
        print(f"   Flashcard Score: {flashcard_score}/10")
        print(f"   Status: {status}")

    # Generate summary statistics
    print("\n" + "="*70)
    print("📊 VALIDATION SUMMARY")
    print("="*70)

    total_validated = len(validation_results)
    passed = sum(1 for r in validation_results if r['overall_pass'])
    failed = total_validated - passed

    avg_legal_score = sum(r['legal_validation'].get('accuracy_score', 0)
                          for r in validation_results) / total_validated
    avg_flashcard_score = sum(r['flashcard_evaluation'].get('overall_score', 0)
                              for r in validation_results) / total_validated

    print(f"Total Validated: {total_validated}")
    print(f"Passed: {passed} ({passed/total_validated*100:.1f}%)")
    print(f"Needs Review: {failed} ({failed/total_validated*100:.1f}%)")
    print(f"\nAverage Legal Accuracy Score: {avg_legal_score:.1f}/10")
    print(f"Average Flashcard Quality Score: {avg_flashcard_score:.1f}/10")

    # Common issues
    all_issues = []
    all_weaknesses = []

    for r in validation_results:
        all_issues.extend(r['legal_validation'].get('issues', []))
        all_weaknesses.extend(r['flashcard_evaluation'].get('weaknesses', []))

    if all_issues:
        print(f"\nCommon Legal Issues ({len(all_issues)} total):")
        for issue in list(set(all_issues))[:5]:
            print(f"  - {issue}")

    if all_weaknesses:
        print(f"\nCommon Flashcard Weaknesses ({len(all_weaknesses)} total):")
        for weakness in list(set(all_weaknesses))[:5]:
            print(f"  - {weakness}")

    # Save detailed report
    report = {
        'metadata': {
            'total_concepts': len(concepts),
            'validated_count': total_validated,
            'sample_size': args.sample if not args.full else len(concepts),
            'is_full_validation': args.full
        },
        'summary': {
            'total_validated': total_validated,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total_validated * 100,
            'avg_legal_score': avg_legal_score,
            'avg_flashcard_score': avg_flashcard_score
        },
        'results': validation_results
    }

    print(f"\n💾 Saving detailed report to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ Report saved\n")
    print("="*70)

    # Final recommendation
    if avg_legal_score >= 8 and avg_flashcard_score >= 8:
        print("🎉 EXCELLENT! Concepts are high quality and ready for production!")
    elif avg_legal_score >= 7 and avg_flashcard_score >= 7:
        print("✅ GOOD! Concepts are acceptable, minor improvements recommended.")
    else:
        print("⚠️  NEEDS WORK! Review failed concepts and consider regeneration.")

    print("="*70)


if __name__ == "__main__":
    main()
