"""
Exam PDF Parser for extracting questions, options, and answers
Designed for exams with:
- Questions with 5 options (A-E)
- Answer key table at the end
"""

import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import json

import sys
sys.path.append(str(Path(__file__).parent.parent))

from agent.ingestion.ocr_utils import GeminiOCR
from agent.ingestion.exam_validator import ExamQuestionValidator
from agent.config.settings import OCR_MAX_PAGES

class ExamParser:
    """Parser for exam PDFs with questions and answer keys"""

    def __init__(self, enable_validation: bool = True):
        self.ocr = GeminiOCR()
        self.validator = ExamQuestionValidator() if enable_validation else None
        self.enable_validation = enable_validation

        # Regex patterns for Hebrew and English
        self.patterns = {
            # Question patterns - looking for numbered questions
            'question_number': re.compile(r'^(\d+)[\.\)]\s*(.+)', re.MULTILINE),

            # Option patterns - Hebrew (א, ב, ג, ד, ה) or English (A, B, C, D, E)
            'option_hebrew': re.compile(r'^([א-ה])[\.\)]\s*(.+)', re.MULTILINE),
            'option_english': re.compile(r'^([A-E])[\.\)]\s*(.+)', re.MULTILINE | re.IGNORECASE),

            # Answer key patterns - various table formats
            'answer_table_row': re.compile(r'(\d+)\s*[:\|\-]?\s*([א-הA-E])', re.IGNORECASE),
            'answer_inline': re.compile(r'תשובה\s*נכונה[:\s]*([א-הA-E])|correct\s*answer[:\s]*([A-E])', re.IGNORECASE),
        }

    def parse_pdf(self, pdf_path: str, verbose: bool = True) -> Dict:
        """
        Parse exam PDF to extract questions and answers

        Args:
            pdf_path: Path to exam PDF
            verbose: Print progress

        Returns:
            Dictionary with questions, answers, and metadata
        """
        if verbose:
            print(f"\n📝 Parsing exam: {pdf_path}")

        # OCR the PDF
        ocr_result = self.ocr.process_document(pdf_path, max_pages=OCR_MAX_PAGES)

        # Parse questions from all pages
        questions = self._extract_questions(ocr_result['page_markdowns'])

        # Find and parse answer key (usually last pages)
        answer_key = self._extract_answer_key(ocr_result['page_markdowns'])

        # Match answers to questions
        matched_questions = self._match_answers(questions, answer_key)

        # Generate metadata
        exam_metadata = {
            'file_name': Path(pdf_path).name,
            'total_pages': ocr_result['total_pages'],
            'total_questions': len(matched_questions),
            'questions_with_answers': sum(1 for q in matched_questions if q.get('correct_answer')),
            'extraction_timestamp': str(Path(pdf_path).stat().st_mtime)
        }

        if verbose:
            print(f"✅ Extracted {exam_metadata['total_questions']} questions")
            print(f"✅ Found answers for {exam_metadata['questions_with_answers']} questions")

        return {
            'questions': matched_questions,
            'metadata': exam_metadata,
            'raw_pages': ocr_result['page_markdowns']
        }

    def _extract_questions(self, pages: List[str]) -> List[Dict]:
        """
        Extract questions and options from pages

        Args:
            pages: List of page markdown content

        Returns:
            List of question dictionaries
        """
        questions = []
        current_question = None
        question_counter = 0

        for page_num, page_content in enumerate(pages, 1):
            lines = page_content.split('\n')

            for i, line in enumerate(lines):
                # Check for question number
                q_match = self.patterns['question_number'].match(line.strip())

                if q_match:
                    # Save previous question if exists
                    if current_question and self._validate_question(current_question):
                        questions.append(current_question)

                    # Start new question
                    question_counter += 1
                    current_question = {
                        'question_number': int(q_match.group(1)),
                        'question_text': q_match.group(2).strip(),
                        'page_number': page_num,
                        'options': {},
                        'raw_text': line
                    }

                    # Look for multi-line question text
                    j = i + 1
                    while j < len(lines) and not self._is_option_line(lines[j]):
                        if lines[j].strip():
                            current_question['question_text'] += ' ' + lines[j].strip()
                        j += 1

                # Check for options
                elif current_question:
                    option_match = self._extract_option(line)
                    if option_match:
                        option_letter, option_text = option_match
                        # Normalize option letter to English uppercase
                        normalized_letter = self._normalize_option_letter(option_letter)
                        current_question['options'][normalized_letter] = option_text.strip()

                        # Look for multi-line options
                        j = i + 1
                        while j < len(lines) and not self._is_option_line(lines[j]) and not self.patterns['question_number'].match(lines[j].strip()):
                            if lines[j].strip():
                                current_question['options'][normalized_letter] += ' ' + lines[j].strip()
                            j += 1

        # Add last question
        if current_question and self._validate_question(current_question):
            questions.append(current_question)

        return questions

    def _extract_option(self, line: str) -> Optional[Tuple[str, str]]:
        """Extract option letter and text from a line"""
        # Try Hebrew options first
        match = self.patterns['option_hebrew'].match(line.strip())
        if match:
            return match.group(1), match.group(2)

        # Try English options
        match = self.patterns['option_english'].match(line.strip())
        if match:
            return match.group(1).upper(), match.group(2)

        return None

    def _is_option_line(self, line: str) -> bool:
        """Check if a line contains an option"""
        return bool(self._extract_option(line))

    def _normalize_option_letter(self, letter: str) -> str:
        """Convert Hebrew option letters to English A-E"""
        hebrew_to_english = {
            'א': 'A', 'ב': 'B', 'ג': 'C', 'ד': 'D', 'ה': 'E'
        }
        return hebrew_to_english.get(letter, letter.upper())

    def _extract_answer_key(self, pages: List[str]) -> Dict[int, str]:
        """
        Extract answer key from pages (usually in a table at the end)

        Args:
            pages: List of page markdown content

        Returns:
            Dictionary mapping question number to correct answer
        """
        answer_key = {}

        # Start from the last pages (where answer key usually is)
        for page_content in reversed(pages):
            # Look for answer table patterns
            matches = self.patterns['answer_table_row'].findall(page_content)

            for match in matches:
                question_num = int(match[0])
                answer = self._normalize_option_letter(match[1])
                answer_key[question_num] = answer

            # If we found answers, we can stop
            if answer_key and len(answer_key) > 10:  # Assume at least 10 answers for a valid key
                break

        # Also try to find inline answers in questions
        if not answer_key:
            for page_content in pages:
                inline_matches = self.patterns['answer_inline'].findall(page_content)
                # Process inline answers if found
                for match in inline_matches:
                    answer = match[0] if match[0] else match[1]
                    if answer:
                        # This would need context to know which question
                        pass

        return answer_key

    def _match_answers(self, questions: List[Dict], answer_key: Dict[int, str]) -> List[Dict]:
        """
        Match answers from answer key to questions

        Args:
            questions: List of question dictionaries
            answer_key: Dictionary of question number to answer

        Returns:
            Questions with matched answers
        """
        for question in questions:
            q_num = question['question_number']
            if q_num in answer_key:
                question['correct_answer'] = answer_key[q_num]
            else:
                question['correct_answer'] = None

        return questions

    def _validate_question(self, question: Dict) -> bool:
        """
        Validate that a question has all required components

        Args:
            question: Question dictionary

        Returns:
            True if question is valid
        """
        # Must have question text
        if not question.get('question_text'):
            return False

        # Must have at least 4 options (A-D minimum)
        if len(question.get('options', {})) < 4:
            return False

        # Check that we have consecutive options starting from A
        expected_options = ['A', 'B', 'C', 'D', 'E']
        for i, opt in enumerate(expected_options[:len(question['options'])]):
            if opt not in question['options']:
                return False

        return True

    def format_question_for_db(self, question: Dict, source_metadata: Dict = None) -> Dict:
        """
        Format a parsed question for database insertion

        Args:
            question: Parsed question dictionary
            source_metadata: Additional metadata about the source

        Returns:
            Formatted dictionary for database
        """
        # Ensure all 5 options exist
        options = question.get('options', {})

        db_format = {
            'question_text': question['question_text'],
            'option_a': options.get('A', ''),
            'option_b': options.get('B', ''),
            'option_c': options.get('C', ''),
            'option_d': options.get('D', ''),
            'option_e': options.get('E', ''),
            'correct_answer': question.get('correct_answer'),
            'metadata': {
                'source_file': source_metadata.get('file_name') if source_metadata else None,
                'page_number': question.get('page_number'),
                'question_number': question.get('question_number'),
                'extraction_method': 'gemini_ocr_parser'
            }
        }

        # Add topic and difficulty if available
        if source_metadata:
            if 'topic' in source_metadata:
                db_format['topic'] = source_metadata['topic']
            if 'difficulty' in source_metadata:
                db_format['difficulty'] = source_metadata['difficulty']

        return db_format

    def extract_and_validate(
        self,
        pdf_path: str,
        use_llm_validation: bool = True
    ) -> Tuple[List[Dict], Dict]:
        """
        Extract questions and perform validation (with optional LLM validation)

        Args:
            pdf_path: Path to exam PDF
            use_llm_validation: Use LLM to validate each question

        Returns:
            Tuple of (valid_questions, validation_report)
        """
        result = self.parse_pdf(pdf_path)

        valid_questions = []
        invalid_questions = []

        # Stage 1: Basic structural validation
        print(f"\n📋 Stage 1: Basic validation...")
        for q in result['questions']:
            if self._validate_question(q) and q.get('correct_answer'):
                valid_questions.append(q)
            else:
                invalid_questions.append({
                    'question_number': q.get('question_number'),
                    'reason': 'Missing options or answer',
                    'has_answer': bool(q.get('correct_answer')),
                    'option_count': len(q.get('options', {}))
                })

        print(f"   ✅ {len(valid_questions)}/{len(result['questions'])} passed basic validation")

        # Stage 2: LLM validation (if enabled)
        llm_validated = []
        llm_issues = []

        if use_llm_validation and self.validator and valid_questions:
            print(f"\n🤖 Stage 2: LLM validation...")

            # Create page context map
            page_contexts = {
                i+1: content
                for i, content in enumerate(result.get('raw_pages', []))
            }

            # Validate with LLM
            llm_validated, llm_report = self.validator.validate_batch(
                valid_questions,
                page_contexts,
                verbose=True
            )

            llm_issues = llm_report.get('issues', [])

            print(f"   ✅ {len(llm_validated)}/{len(valid_questions)} passed LLM validation")

        else:
            llm_validated = valid_questions

        validation_report = {
            'total_extracted': len(result['questions']),
            'basic_valid': len(valid_questions),
            'llm_valid': len(llm_validated),
            'final_valid': len(llm_validated),
            'invalid_questions': len(invalid_questions),
            'llm_rejected': len(valid_questions) - len(llm_validated),
            'success_rate': len(llm_validated) / len(result['questions']) if result['questions'] else 0,
            'basic_invalid_details': invalid_questions,
            'llm_issues': llm_issues
        }

        return llm_validated, validation_report


def test_parser():
    """Test the exam parser"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python exam_parser.py <exam_pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    parser = ExamParser()
    valid_questions, report = parser.extract_and_validate(pdf_path)

    print(f"\n📊 Validation Report:")
    print(f"   Total extracted: {report['total_extracted']}")
    print(f"   Valid questions: {report['valid_questions']}")
    print(f"   Success rate: {report['success_rate']:.1%}")

    if valid_questions:
        print(f"\n📝 Sample Question:")
        q = valid_questions[0]
        formatted = parser.format_question_for_db(q)
        print(json.dumps(formatted, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_parser()