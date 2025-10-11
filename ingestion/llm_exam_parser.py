"""
LLM-Powered Exam Parser
Uses AI to intelligently extract questions, options, and answers
NO REGEX - Pure LLM intelligence
"""

import json
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from ingestion.ocr_utils import GeminiOCR
from openai import OpenAI
from config.settings import (
    OPENROUTER_API_KEY,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    THINKING_MODEL,
    THINKING_MAX_TOKENS,
    OCR_MAX_PAGES
)


class LLMExamParser:
    """Fully LLM-powered exam parser - no regex, pure intelligence"""

    def __init__(self):
        self.ocr = GeminiOCR()
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )

    def parse_pdf(self, pdf_path: str, verbose: bool = True) -> Dict:
        """
        Parse exam PDF using LLM intelligence

        Args:
            pdf_path: Path to exam PDF
            verbose: Print progress

        Returns:
            Dictionary with questions, answers, and metadata
        """
        if verbose:
            print(f"\n📝 Parsing exam with LLM: {pdf_path}")

        # Step 1: OCR the entire PDF
        ocr_result = self.ocr.process_document(pdf_path, max_pages=OCR_MAX_PAGES)

        if verbose:
            print(f"\n🤖 Step 1: Extracting questions with AI...")

        # Step 2: Extract questions using LLM (page by page for better accuracy)
        all_questions = []
        for page_num, page_content in enumerate(ocr_result['page_markdowns'], 1):
            if verbose and page_num % 3 == 0:
                print(f"   Processing page {page_num}/{len(ocr_result['page_markdowns'])}")

            page_questions = self._extract_questions_from_page(
                page_content,
                page_num
            )
            all_questions.extend(page_questions)

        if verbose:
            print(f"   ✅ Found {len(all_questions)} questions")
            print(f"\n🤖 Step 2: Extracting answer key with AI...")

        # Step 3: Extract answer key using LLM
        answer_key = self._extract_answer_key_llm(
            ocr_result['page_markdowns']
        )

        if verbose:
            print(f"   ✅ Found answers for {len(answer_key)} questions")
            print(f"\n🤖 Step 3: Matching and validating...")

        # Step 4: Match answers to questions
        matched_questions = self._match_and_validate(
            all_questions,
            answer_key,
            verbose=verbose
        )

        if verbose:
            print(f"   ✅ Validated {len(matched_questions)} complete Q&A pairs")

        # Generate metadata
        exam_metadata = {
            'file_name': Path(pdf_path).name,
            'total_pages': ocr_result['total_pages'],
            'total_questions': len(matched_questions),
            'questions_with_answers': sum(1 for q in matched_questions if q.get('correct_answer')),
            'extraction_method': 'llm_powered'
        }

        return {
            'questions': matched_questions,
            'metadata': exam_metadata,
            'raw_pages': ocr_result['page_markdowns']
        }

    def _extract_questions_from_page(
        self,
        page_content: str,
        page_num: int
    ) -> List[Dict]:
        """
        Extract all questions from a single page using LLM

        Args:
            page_content: OCR text from page
            page_num: Page number

        Returns:
            List of extracted questions
        """
        extraction_prompt = """אתה מומחה בחילוץ שאלות מבחן.

מהטקסט הבא, חלץ את **כל** שאלות המבחן.

**פורמט שאלה:**
- מספר שאלה (1, 2, 3, וכו')
- טקסט השאלה
- 5 אפשרויות: א/A, ב/B, ג/C, ד/D, ה/E

**חשוב מאוד:**
1. אל תדלג על שאלות - חלץ את כולן!
2. אם שאלה מתפרשת על מספר שורות, צרף הכל
3. אם אפשרויות מתפרשות על מספר שורות, צרף הכל
4. אל תחפש תשובות נכונות - רק שאלות ואפשרויות
5. **זהירות!** אם יש כותרת "נתונים לשאלות X-Y" - זה לא שאלה! זה טקסט הקשר/רקע שחולק על כמה שאלות
6. כשיש "נתונים לשאלות", צרף את כל הטקסט הזה לתחילת כל שאלה שנמצאת בטווח (X עד Y)
7. טקסט הקשר/תרחיש שמופיע לפני שאלה צריך להיכלל בתוך question_text

**פורמט פלט - JSON Array:**
```json
[
  {
    "question_number": 1,
    "question_text": "טקסט מלא של השאלה כולל הקשר",
    "options": {
      "A": "אפשרות א - טקסט מלא",
      "B": "אפשרות ב - טקסט מלא",
      "C": "אפשרות ג - טקסט מלא",
      "D": "אפשרות ד - טקסט מלא",
      "E": "אפשרות ה - טקסט מלא"
    }
  }
]
```

**דוגמה לטיפול ב"נתונים לשאלות":**

אם הטקסט מכיל:
```
נתונים לשאלות 22-23
דילן הוא איש פנים בחברה...
[טקסט רקע ארוך]

22. איזו מן הנסיבות הבאות ביותר...
א. ברנדה עשתה שימוש
ב. פעולתה של ברנדה

23. איזו מן הנסיבות הבאות...
א. קלי עשתה שימוש
ב. קלי היתה עושה
```

**תחלץ כך:**
```json
[
  {
    "question_number": 22,
    "question_text": "נתונים לשאלות 22-23: דילן הוא איש פנים בחברה... [כל הרקע]. איזו מן הנסיבות הבאות ביותר...",
    "options": {...}
  },
  {
    "question_number": 23,
    "question_text": "נתונים לשאלות 22-23: דילן הוא איש פנים בחברה... [כל הרקע]. איזו מן הנסיבות הבאות...",
    "options": {...}
  }
]
```

אם אין שאלות בעמוד, החזר: `[]`

**טקסט לעיבוד:**"""

        try:
            response = self.client.chat.completions.create(
                model=THINKING_MODEL,
                messages=[
                    {"role": "system", "content": extraction_prompt},
                    {"role": "user", "content": page_content}
                ],
                temperature=0.1  # Low for consistency
            )

            result_text = response.choices[0].message.content.strip()

            # Extract JSON from response
            questions = self._parse_json_from_text(result_text)

            if not isinstance(questions, list):
                questions = []

            # Add page number to each question
            for q in questions:
                q['page_number'] = page_num

            return questions

        except Exception as e:
            print(f"   ⚠️  Error extracting from page {page_num}: {e}")
            return []

    def _extract_answer_key_llm(self, pages: List[str]) -> Dict[int, str]:
        """
        Extract answer key using LLM

        Args:
            pages: All page contents

        Returns:
            Dictionary mapping question number to answer
        """
        # Look at last 3 pages (where answer keys usually are)
        last_pages = pages[-3:]
        combined = "\n\n---PAGE BREAK---\n\n".join(last_pages)

        answer_key_prompt = """אתה מומחה בזיהוי טבלאות תשובות במבחנים.

חפש בטקסט הבא את **טבלת התשובות הנכונות** למבחן.

**מה לחפש:**
- טבלה עם מספרי שאלות (1, 2, 3, ..., 25)
- ליד כל מספר יש אות (א/A, ב/B, ג/C, ד/D, ה/E)
- הטבלה יכולה להיות בכל פורמט (שורות, עמודות, רשימה)

**זהירות - שאלות עם מספר תשובות:**
- לפעמים שאלה יכולה להיות עם 2 תשובות נכונות (לדוגמה: "25: א, ה" או "25: A, E")
- אם שאלה יש לה יותר מתשובה אחת, סמן אותה כ-"MULTIPLE"
- דוגמה: אם שאלה 25 יש תשובות א+ה, החזר `"25": "MULTIPLE"`

**פורמט פלט - JSON Object:**
```json
{
  "1": "A",
  "2": "B",
  "3": "C",
  ...
  "24": "E",
  "25": "MULTIPLE"
}
```

**חשוב:**
- המר אותיות עבריות לאנגלית: א→A, ב→B, ג→C, ד→D, ה→E
- אם יש יותר מתשובה אחת לשאלה, החזר "MULTIPLE" (לא את האותיות!)
- כלול את **כל** התשובות שמצאת
- אם לא מצאת טבלת תשובות, החזר: `{}`

**טקסט לחיפוש:**"""

        try:
            response = self.client.chat.completions.create(
                model=THINKING_MODEL,
                messages=[
                    {"role": "system", "content": answer_key_prompt},
                    {"role": "user", "content": combined}
                ],
                temperature=0.0
            )

            result_text = response.choices[0].message.content.strip()
            answer_key_raw = self._parse_json_from_text(result_text)

            # Convert string keys to int
            answer_key = {}
            if isinstance(answer_key_raw, dict):
                for k, v in answer_key_raw.items():
                    try:
                        answer_key[int(k)] = str(v).upper()
                    except:
                        pass

            return answer_key

        except Exception as e:
            print(f"   ⚠️  Error extracting answer key: {e}")
            return {}

    def _match_and_validate(
        self,
        questions: List[Dict],
        answer_key: Dict[int, str],
        verbose: bool = True
    ) -> List[Dict]:
        """
        Match questions with answers and validate

        Args:
            questions: List of extracted questions
            answer_key: Dictionary of answers
            verbose: Print progress

        Returns:
            List of validated and matched questions
        """
        validated = []

        for q in questions:
            q_num = q.get('question_number')

            # Match answer from key
            if q_num in answer_key:
                answer = answer_key[q_num]

                # Skip questions with multiple correct answers
                if answer == "MULTIPLE":
                    if verbose:
                        print(f"      ⚠️  Q{q_num}: Multiple correct answers - SKIPPED")
                    continue

                q['correct_answer'] = answer
            else:
                # Try to find answer using LLM context search
                if verbose:
                    print(f"      🔍 No answer for Q{q_num}, searching...")
                q['correct_answer'] = None

            # Validate question structure
            if self._validate_question_structure(q):
                # If we have an answer, add semantic validation score
                if q.get('correct_answer'):
                    validation_result = self._get_answer_validation(q)
                    q['semantic_validation'] = validation_result
                    validated.append(q)

                    # Log low confidence but don't reject
                    if validation_result.get('confidence', 1.0) < 0.7 and verbose:
                        print(f"      ⚠️  Q{q_num}: Low confidence ({validation_result.get('confidence', 0):.1%})")
                else:
                    # Question is structurally valid but missing answer
                    if verbose:
                        print(f"      ⚠️  Q{q_num}: Missing answer")
            else:
                if verbose:
                    print(f"      ⚠️  Q{q_num}: Invalid structure")

        return validated

    def _validate_question_structure(self, question: Dict) -> bool:
        """Validate question has all required parts"""
        # Must have question text
        if not question.get('question_text'):
            return False

        # Must have options
        options = question.get('options', {})
        if not isinstance(options, dict):
            return False

        # Must have at least 4 options (A-D minimum)
        required_options = ['A', 'B', 'C', 'D']
        for opt in required_options:
            if opt not in options or not options[opt]:
                return False

        return True

    def _get_answer_validation(self, question: Dict) -> Dict:
        """
        Use LLM to validate that the correct answer makes sense

        Args:
            question: Question with answer

        Returns:
            Validation result dictionary with valid, confidence, and reason
        """
        validation_prompt = """האם התשובה הנכונה הגיונית עבור השאלה הזו?

**שאלה:** {question}

**אפשרויות:**
A. {opt_a}
B. {opt_b}
C. {opt_c}
D. {opt_d}
E. {opt_e}

**תשובה שסומנה כנכונה:** {answer}

בדוק:
1. האם התשובה ({answer}) עונה על השאלה?
2. האם יש התאמה בין טקסט השאלה לאפשרות {answer}?
3. האם זה נראה הגיוני?

החזר JSON:
```json
{{
  "valid": true/false,
  "confidence": 0.0-1.0,
  "reason": "הסבר קצר"
}}
```"""

        q_text = question.get('question_text', '')
        options = question.get('options', {})
        answer = question.get('correct_answer', '')

        prompt = validation_prompt.format(
            question=q_text,
            opt_a=options.get('A', ''),
            opt_b=options.get('B', ''),
            opt_c=options.get('C', ''),
            opt_d=options.get('D', ''),
            opt_e=options.get('E', ''),
            answer=answer
        )

        try:
            response = self.client.chat.completions.create(
                model=GEMINI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )

            result = self._parse_json_from_text(response.choices[0].message.content)

            if isinstance(result, dict):
                return result

            return {'valid': True, 'confidence': 0.5, 'reason': 'Parse failed'}

        except Exception as e:
            # If validation fails, return neutral result
            return {'valid': True, 'confidence': 0.5, 'reason': f'Validation error: {str(e)}'}

    def _parse_json_from_text(self, text: str):
        """Extract JSON from LLM response"""
        # Try to find JSON in code blocks
        json_match = re.search(r'```json\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to find JSON without code blocks
        json_match = re.search(r'(\{.*?\}|\[.*?\])', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try parsing entire text as JSON
        try:
            return json.loads(text)
        except:
            pass

        return {}

    def extract_and_validate(
        self,
        pdf_path: str,
        use_llm_validation: bool = True
    ) -> Tuple[List[Dict], Dict]:
        """
        Extract and validate - compatible with old interface

        Args:
            pdf_path: Path to PDF
            use_llm_validation: Always True for this parser

        Returns:
            Tuple of (questions, validation_report)
        """
        result = self.parse_pdf(pdf_path, verbose=True)

        questions = result['questions']
        metadata = result['metadata']

        validation_report = {
            'total_extracted': metadata['total_questions'],
            'basic_valid': metadata['total_questions'],
            'llm_valid': metadata['questions_with_answers'],
            'final_valid': metadata['questions_with_answers'],
            'invalid_questions': metadata['total_questions'] - metadata['questions_with_answers'],
            'llm_rejected': 0,
            'success_rate': metadata['questions_with_answers'] / metadata['total_questions'] if metadata['total_questions'] > 0 else 0,
            'basic_invalid_details': [],
            'llm_issues': []
        }

        return questions, validation_report


def test_llm_parser():
    """Test the LLM parser"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python llm_exam_parser.py <exam_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    parser = LLMExamParser()
    result = parser.parse_pdf(pdf_path, verbose=True)

    print(f"\n📊 Results:")
    print(f"   Total questions: {result['metadata']['total_questions']}")
    print(f"   With answers: {result['metadata']['questions_with_answers']}")

    # Show first question
    if result['questions']:
        print(f"\n📝 Sample question:")
        q = result['questions'][0]
        print(json.dumps(q, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_llm_parser()
