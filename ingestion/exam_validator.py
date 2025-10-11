"""
LLM-Based Exam Question Validator
Validates extracted questions by re-reading the original PDF context
"""

import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from openai import OpenAI

import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import OPENROUTER_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS


class ExamQuestionValidator:
    """Validates exam questions using LLM verification"""

    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )

        # Validation prompt
        self.validation_prompt = """אתה מומחה בבדיקת שאלות מבחן.

קיבלת שאלת מבחן עם 5 אפשרויות ותשובה נכונה.
**תפקידך**: לבדוק שהשאלה עקבית ונכונה.

בדוק:
1. ✅ השאלה מנוסחת בצורה ברורה וחד-משמעית
2. ✅ יש בדיוק 5 אפשרויות (א-ה או A-E)
3. ✅ כל אפשרות מלאה וברורה
4. ✅ התשובה הנכונה היא אחת מהאפשרויות
5. ✅ התשובה הנכונה הגיונית ונכונה עבור השאלה
6. ⚠️ אין אי-התאמה בין האפשרויות לתשובה

**החזר JSON בפורמט הבא**:
```json
{
  "valid": true/false,
  "issues": ["בעיה 1", "בעיה 2", ...],
  "confidence": 0.0-1.0,
  "correct_answer_valid": true/false,
  "suggested_fix": "הצעה לתיקון אם יש בעיה"
}
```

אם הכל תקין, החזר:
```json
{
  "valid": true,
  "issues": [],
  "confidence": 1.0,
  "correct_answer_valid": true
}
```"""

    def validate_question(
        self,
        question: Dict,
        original_context: str = None,
        search_adjacent_pages: bool = True,
        all_page_contexts: Dict[int, str] = None
    ) -> Dict:
        """
        Validate a single question using LLM with context search

        Args:
            question: Question dictionary with text, options, and answer
            original_context: Original PDF text around this question (optional)
            search_adjacent_pages: Search nearby pages for context
            all_page_contexts: All page contents for context search

        Returns:
            Validation result with issues and confidence
        """
        # Build question text for validation
        question_text = self._format_question_for_validation(question)

        # Add context if available
        if original_context:
            validation_input = f"**הקשר מהמקור:**\n{original_context}\n\n**השאלה שחולצה:**\n{question_text}"
        else:
            validation_input = question_text

        # Call LLM for validation
        try:
            response = self.client.chat.completions.create(
                model=GEMINI_MODEL,
                messages=[
                    {"role": "system", "content": self.validation_prompt},
                    {"role": "user", "content": validation_input}
                ],
                temperature=0.1  # Low temperature for consistent validation
            )

            result_text = response.choices[0].message.content.strip()

            # Extract JSON from response
            validation_result = self._parse_validation_result(result_text)

            # If validation failed and we have page contexts, try context search
            if (not validation_result['valid'] or validation_result['confidence'] < 0.7) \
                and search_adjacent_pages and all_page_contexts:

                print(f"      🔍 Searching for correct context for question {question.get('question_number')}...")

                context_fix = self._search_for_correct_context(
                    question,
                    all_page_contexts
                )

                if context_fix.get('found_better_context'):
                    validation_result['context_search'] = context_fix
                    validation_result['suggested_fix'] = context_fix.get('corrected_question')

            return validation_result

        except Exception as e:
            return {
                'valid': False,
                'issues': [f'Validation error: {str(e)}'],
                'confidence': 0.0,
                'correct_answer_valid': False
            }

    def _search_for_correct_context(
        self,
        question: Dict,
        all_page_contexts: Dict[int, str]
    ) -> Dict:
        """
        Search through page contexts to find the correct options for a question

        Args:
            question: The problematic question
            all_page_contexts: All page contents

        Returns:
            Dictionary with search results and suggested fix
        """
        q_num = question.get('question_number')
        q_text = question.get('question_text', '')
        current_page = question.get('page_number')

        # Pages to search (current + adjacent)
        pages_to_search = []
        if current_page:
            pages_to_search = [current_page - 1, current_page, current_page + 1]
        else:
            pages_to_search = list(all_page_contexts.keys())

        # Build search prompt
        search_prompt = f"""אני מחפש את האפשרויות הנכונות לשאלה הזו:

**מספר שאלה:** {q_num}
**טקסט השאלה:** {q_text}

חפש בעמודים הבאים את האפשרויות (א-ה או A-E) השייכות לשאלה מספר {q_num}.

החזר JSON:
```json
{{
  "found": true/false,
  "page_number": מספר העמוד,
  "options": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "...",
    "E": "..."
  }},
  "correct_answer": "התשובה הנכונה"
}}
```

אם לא מצאת, החזר `{{"found": false}}`."""

        # Combine relevant page contexts
        combined_context = "\n\n---PAGE BREAK---\n\n".join([
            f"**עמוד {page}:**\n{all_page_contexts.get(page, '')}"
            for page in pages_to_search
            if page in all_page_contexts
        ])

        try:
            response = self.client.chat.completions.create(
                model=GEMINI_MODEL,
                messages=[
                    {"role": "system", "content": search_prompt},
                    {"role": "user", "content": combined_context}
                ],
                temperature=0.1
            )

            result_text = response.choices[0].message.content.strip()
            search_result = self._parse_json_from_text(result_text)

            if search_result.get('found'):
                # Found better context!
                return {
                    'found_better_context': True,
                    'original_page': current_page,
                    'found_on_page': search_result.get('page_number'),
                    'corrected_question': {
                        'question_text': q_text,
                        'options': search_result.get('options', {}),
                        'correct_answer': search_result.get('correct_answer'),
                        'question_number': q_num
                    }
                }
            else:
                return {
                    'found_better_context': False,
                    'searched_pages': pages_to_search
                }

        except Exception as e:
            return {
                'found_better_context': False,
                'error': str(e)
            }

    def validate_batch(
        self,
        questions: List[Dict],
        page_contexts: Dict[int, str] = None,
        verbose: bool = True
    ) -> Tuple[List[Dict], Dict]:
        """
        Validate a batch of questions

        Args:
            questions: List of question dictionaries
            page_contexts: Dictionary of page_number -> page_content
            verbose: Print progress

        Returns:
            Tuple of (validated_questions, validation_report)
        """
        validated = []
        issues_found = []

        if verbose:
            print(f"\n🔍 Validating {len(questions)} questions...")

        for i, question in enumerate(questions, 1):
            if verbose and i % 5 == 0:
                print(f"   Progress: {i}/{len(questions)}")

            # Get context if available
            page_num = question.get('page_number')
            context = page_contexts.get(page_num) if page_contexts else None

            # Validate with context search enabled
            validation = self.validate_question(
                question,
                context,
                search_adjacent_pages=True,
                all_page_contexts=page_contexts
            )

            # Add validation to question
            question['validation'] = validation

            if validation['valid'] and validation['confidence'] >= 0.7:
                validated.append(question)
            else:
                issues_found.append({
                    'question_number': question.get('question_number'),
                    'issues': validation.get('issues', []),
                    'confidence': validation.get('confidence', 0),
                    'question_text': question.get('question_text', '')[:100] + '...'
                })

        # Generate report
        report = {
            'total_questions': len(questions),
            'valid_questions': len(validated),
            'invalid_questions': len(issues_found),
            'validation_rate': len(validated) / len(questions) if questions else 0,
            'issues': issues_found
        }

        if verbose:
            print(f"\n✅ Validation complete:")
            print(f"   Valid: {report['valid_questions']}/{report['total_questions']}")
            print(f"   Success rate: {report['validation_rate']:.1%}")

            if issues_found:
                print(f"\n⚠️  Found {len(issues_found)} problematic questions")

        return validated, report

    def deep_validate_with_reread(
        self,
        question: Dict,
        pdf_page_image_base64: str
    ) -> Dict:
        """
        Deep validation: Re-read the question from original PDF image

        Args:
            question: Extracted question
            pdf_page_image_base64: Base64 encoded image of the PDF page

        Returns:
            Enhanced validation with re-read comparison
        """
        # Re-read the specific question from the image
        reread_prompt = f"""מצא וחלץ את שאלה מספר {question.get('question_number')} מהעמוד הזה.

החזר JSON:
```json
{{
  "question_text": "...",
  "options": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "...",
    "E": "..."
  }}
}}
```

חלץ בדיוק את מה שכתוב בתמונה."""

        try:
            response = self.client.chat.completions.create(
                model=GEMINI_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": reread_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{pdf_page_image_base64}"
                            }
                        }
                    ]
                }],
                temperature=0.1
            )

            reread_text = response.choices[0].message.content.strip()
            reread_data = self._parse_json_from_text(reread_text)

            # Compare with original extraction
            comparison = self._compare_questions(question, reread_data)

            return {
                'valid': comparison['match'],
                'reread_data': reread_data,
                'comparison': comparison,
                'confidence': comparison.get('similarity', 0)
            }

        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'confidence': 0
            }

    def _format_question_for_validation(self, question: Dict) -> str:
        """Format question for validation prompt"""
        q_text = question.get('question_text', '')
        options = question.get('options', {})
        correct = question.get('correct_answer', '')

        formatted = f"**שאלה:** {q_text}\n\n"

        # Add options
        for opt in ['A', 'B', 'C', 'D', 'E']:
            opt_key = opt if opt in options else opt.lower()
            if opt_key in options:
                formatted += f"**{opt}.** {options[opt_key]}\n"
            else:
                opt_text = question.get(f'option_{opt.lower()}', '')
                if opt_text:
                    formatted += f"**{opt}.** {opt_text}\n"

        formatted += f"\n**תשובה נכונה:** {correct}"

        return formatted

    def _parse_validation_result(self, text: str) -> Dict:
        """Parse validation result from LLM response"""
        import json

        # Try to extract JSON
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to parse entire response as JSON
        try:
            return json.loads(text)
        except:
            pass

        # Fallback: Create basic validation result
        return {
            'valid': 'valid": true' in text.lower(),
            'issues': [],
            'confidence': 0.5,
            'correct_answer_valid': True
        }

    def _parse_json_from_text(self, text: str) -> Dict:
        """Extract JSON from text response"""
        import json

        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        try:
            return json.loads(text)
        except:
            return {}

    def _compare_questions(self, original: Dict, reread: Dict) -> Dict:
        """Compare original extraction with re-read"""
        issues = []

        # Compare question text
        orig_q = original.get('question_text', '').strip()
        reread_q = reread.get('question_text', '').strip()

        if orig_q != reread_q:
            similarity = self._text_similarity(orig_q, reread_q)
            if similarity < 0.8:
                issues.append(f"Question text mismatch (similarity: {similarity:.2%})")

        # Compare options
        orig_opts = original.get('options', {})
        reread_opts = reread.get('options', {})

        for opt in ['A', 'B', 'C', 'D', 'E']:
            orig_text = orig_opts.get(opt, original.get(f'option_{opt.lower()}', ''))
            reread_text = reread_opts.get(opt, '')

            if orig_text and reread_text:
                similarity = self._text_similarity(orig_text, reread_text)
                if similarity < 0.8:
                    issues.append(f"Option {opt} mismatch (similarity: {similarity:.2%})")

        return {
            'match': len(issues) == 0,
            'issues': issues,
            'similarity': 1.0 - (len(issues) / 6.0)  # Normalize by max possible issues
        }

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


def test_validator():
    """Test the validator"""
    validator = ExamQuestionValidator()

    # Test question with potential issue
    test_question = {
        'question_number': 1,
        'question_text': 'מה ההגדרה של מידע פנים?',
        'options': {
            'A': 'מידע שנמסר לציבור',
            'B': 'מידע מהותי שטרם פורסם',
            'C': 'כל מידע על החברה',
            'D': 'דוחות כספיים',
            'E': 'אף אחד מהנ"ל'
        },
        'correct_answer': 'B',
        'page_number': 1
    }

    result = validator.validate_question(test_question)

    print("Validation Result:")
    print(f"  Valid: {result['valid']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Issues: {result['issues']}")


if __name__ == "__main__":
    test_validator()
