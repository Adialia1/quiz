#!/usr/bin/env python3
"""
Improve Hebrew text quality using LLM

Uses a Hebrew language model to:
1. Fix grammar and style
2. Improve clarity and readability
3. Ensure professional Hebrew
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
from openai import OpenAI
from config.settings import OPENROUTER_API_KEY

# You can switch this to the Hugging Face model later
HEBREW_MODEL = "google/gemini-2.0-flash-001"  # Fast and good with Hebrew


def improve_hebrew_text(text: str, context: str = "exam question") -> str:
    """
    Improve Hebrew text quality

    Args:
        text: Hebrew text to improve
        context: Context (e.g., "exam question", "explanation")

    Returns:
        Improved Hebrew text
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )

    prompt = f"""אתה עורך טקסט מקצועי בעברית. תפקידך לשפר את הטקסט הבא ולוודא שהוא כתוב בעברית תקנית, ברורה ומקצועית.

**הקשר:** {context}

**טקסט לשיפור:**
{text}

**הנחיות:**
1. שמור על המשמעות המדויקת - אל תשנה תוכן משפטי או עובדתי
2. תקן שגיאות דקדוק, כתיב וניסוח
3. שפר את הבהירות והקריאות
4. השתמש בעברית פורמלית ומקצועית
5. ודא שהמשפטים זורמים טוב

**החזר רק את הטקסט המשופר, ללא הסברים או הערות.**"""

    try:
        response = client.chat.completions.create(
            model=HEBREW_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Low temperature for consistency
        )

        improved = response.choices[0].message.content.strip()
        return improved

    except Exception as e:
        print(f"⚠️  Hebrew improvement failed: {e}")
        return text  # Return original if fails


def improve_quiz_hebrew(json_file: str, output_file: str = None):
    """
    Improve Hebrew in all quiz questions

    Args:
        json_file: Input JSON file
        output_file: Output JSON file (optional)
    """
    # Load quiz
    with open(json_file, 'r', encoding='utf-8') as f:
        quiz_data = json.load(f)

    questions = quiz_data.get('questions', [])

    print(f"🔧 Improving Hebrew for {len(questions)} questions...")
    print()

    for i, q in enumerate(questions, 1):
        print(f"📝 Question {i}/{len(questions)}...")

        # Improve question text
        if q.get('question_text'):
            original = q['question_text']
            improved = improve_hebrew_text(original, "שאלת מבחן")
            q['question_text'] = improved

            if len(improved) != len(original):
                print(f"   ✓ Question text improved")

        # Improve options
        if q.get('options'):
            for key in ['A', 'B', 'C', 'D', 'E']:
                if key in q['options']:
                    original = q['options'][key]
                    improved = improve_hebrew_text(original, "אפשרות תשובה")
                    q['options'][key] = improved

        # Improve explanation
        if q.get('explanation'):
            original = q['explanation']
            improved = improve_hebrew_text(original, "הסבר")
            q['explanation'] = improved

        print(f"   ✅ Question {i} Hebrew improved")

    # Save improved quiz
    output_file = output_file or json_file.replace('.json', '_improved.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(quiz_data, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ Improved quiz saved: {output_file}")
    print(f"   All Hebrew text has been professionally improved")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Improve Hebrew text quality in quiz')
    parser.add_argument('json_file', help='Input JSON file')
    parser.add_argument('--output', '-o', help='Output JSON file (optional)')

    args = parser.parse_args()

    if not Path(args.json_file).exists():
        print(f"❌ File not found: {args.json_file}")
        sys.exit(1)

    improve_quiz_hebrew(args.json_file, args.output)
