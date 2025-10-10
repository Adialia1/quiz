"""
Exam Question Ingestion Pipeline
Parse JSON/CSV → Embeddings → Supabase

Usage:
    # JSON file
    python scripts/ingest_exam_questions.py questions.json

    # Multiple files
    python scripts/ingest_exam_questions.py examples/legal*.json

Expected JSON format:
[
  {
    "question": "מה ההגדרה של 'איש פנים'?",
    "options": {
      "A": "כל עובד בחברה",
      "B": "מי שיש לו מידע פנים",
      "C": "בעל מניות",
      "D": "דירקטור",
      "E": "אף אחד מהנ\"ל"
    },
    "correct_answer": "B",
    "explanation": "איש פנים הוא מי שמחזיק במידע פנים...",
    "topic": "מידע פנים",
    "difficulty": "medium",
    "legal_reference": "חוק ניירות ערך, סעיף 52(א)"
  }
]
"""
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
import csv

sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY, validate_config
from ingestion.semantic_chunking import SemanticChunker

class ExamQuestionIngestion:
    """Pipeline for ingesting exam questions into Supabase"""

    def __init__(self):
        validate_config()

        print("🔧 Initializing exam question ingestion...")

        self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.chunker = SemanticChunker()

        print("✅ Pipeline ready\n")

    def load_questions_from_json(self, json_path: str) -> List[Dict]:
        """Load questions from JSON file"""
        print(f"📄 Loading questions from: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both array and object with 'questions' key
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
        elif isinstance(data, list):
            questions = data
        else:
            raise ValueError("Invalid JSON format. Expected list or {questions: [...]}")

        print(f"✅ Loaded {len(questions)} questions")
        return questions

    def validate_question(self, q: Dict, index: int) -> bool:
        """Validate question structure"""
        required_fields = ['question', 'options', 'correct_answer']

        for field in required_fields:
            if field not in q:
                print(f"⚠️  Question {index}: Missing required field '{field}'")
                return False

        # Validate options
        if not isinstance(q['options'], dict):
            print(f"⚠️  Question {index}: 'options' must be a dictionary")
            return False

        required_options = ['A', 'B', 'C', 'D', 'E']
        for opt in required_options:
            if opt not in q['options']:
                print(f"⚠️  Question {index}: Missing option '{opt}'")
                return False

        # Validate correct_answer
        if q['correct_answer'] not in required_options:
            print(f"⚠️  Question {index}: Invalid correct_answer '{q['correct_answer']}'")
            return False

        return True

    def create_embedding_text(self, question: Dict) -> str:
        """
        Create text for embedding that captures question context

        Combines question + all options + explanation for better semantic search
        """
        parts = [
            question['question'],
            question['options']['A'],
            question['options']['B'],
            question['options']['C'],
            question['options']['D'],
            question['options']['E']
        ]

        if question.get('explanation'):
            parts.append(question['explanation'])

        if question.get('topic'):
            parts.append(f"נושא: {question['topic']}")

        return ' | '.join(parts)

    def ingest_questions(self, questions: List[Dict]) -> dict:
        """
        Ingest questions into Supabase

        Args:
            questions: List of question dictionaries

        Returns:
            Ingestion results
        """
        print(f"\n{'='*70}")
        print(f"🔄 Processing {len(questions)} questions")
        print(f"{'='*70}\n")

        # Validate all questions
        valid_questions = []
        for i, q in enumerate(questions, 1):
            if self.validate_question(q, i):
                valid_questions.append(q)

        if len(valid_questions) < len(questions):
            print(f"⚠️  {len(questions) - len(valid_questions)} questions failed validation")

        if not valid_questions:
            print("❌ No valid questions to ingest")
            return {'success': False, 'error': 'No valid questions'}

        # Generate embeddings
        print(f"🔄 Generating embeddings for {len(valid_questions)} questions...")

        supabase_records = []

        for i, q in enumerate(valid_questions):
            if (i + 1) % 10 == 0:
                print(f"   Progress: {i + 1}/{len(valid_questions)}...")

            # Create embedding text
            embedding_text = self.create_embedding_text(q)

            # Generate embedding
            embedding = self.chunker.encoder([embedding_text])[0]

            # Convert to list if needed
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else embedding

            # Prepare record
            record = {
                'question_text': q['question'],
                'option_a': q['options']['A'],
                'option_b': q['options']['B'],
                'option_c': q['options']['C'],
                'option_d': q['options']['D'],
                'option_e': q['options']['E'],
                'correct_answer': q['correct_answer'],
                'explanation': q.get('explanation'),
                'topic': q.get('topic'),
                'difficulty': q.get('difficulty', 'medium'),
                'legal_reference': q.get('legal_reference'),
                'embedding': embedding_list,
                'metadata': {
                    'source': q.get('source', 'manual'),
                    'tags': q.get('tags', [])
                }
            }

            supabase_records.append(record)

        print(f"✅ Embeddings generated")

        # Insert into Supabase
        print(f"\n🔄 Inserting into Supabase...")

        try:
            response = self.supabase.table('exam_questions').insert(supabase_records).execute()

            print(f"✅ Successfully inserted {len(supabase_records)} questions")

            result = {
                'success': True,
                'total_questions': len(questions),
                'valid_questions': len(valid_questions),
                'inserted': len(supabase_records)
            }

            return result

        except Exception as e:
            print(f"❌ Error inserting into Supabase: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_stats(self) -> dict:
        """Get statistics about existing questions in database"""
        try:
            # Total count
            response = self.supabase.table('exam_questions')\
                .select('id', count='exact')\
                .execute()
            total = response.count

            # By topic
            response = self.supabase.table('exam_questions')\
                .select('topic')\
                .execute()
            topics = {}
            for row in response.data:
                topic = row['topic'] or 'Unknown'
                topics[topic] = topics.get(topic, 0) + 1

            # By difficulty
            response = self.supabase.table('exam_questions')\
                .select('difficulty')\
                .execute()
            difficulties = {}
            for row in response.data:
                diff = row['difficulty'] or 'medium'
                difficulties[diff] = difficulties.get(diff, 0) + 1

            stats = {
                'total': total,
                'by_topic': topics,
                'by_difficulty': difficulties
            }

            return stats

        except Exception as e:
            print(f"⚠️  Could not fetch stats: {e}")
            return {}

    def print_stats(self):
        """Print database statistics"""
        stats = self.get_stats()

        if not stats:
            print("No stats available")
            return

        print("\n" + "="*70)
        print("📊 EXAM QUESTIONS DATABASE STATS")
        print("="*70)

        print(f"\nTotal Questions: {stats['total']}")

        if stats.get('by_topic'):
            print(f"\nBy Topic:")
            for topic, count in sorted(stats['by_topic'].items(), key=lambda x: -x[1]):
                print(f"   {topic:.<40} {count:>4}")

        if stats.get('by_difficulty'):
            print(f"\nBy Difficulty:")
            for diff, count in stats['by_difficulty'].items():
                print(f"   {diff:.<40} {count:>4}")

        print("="*70)


def main():
    parser = argparse.ArgumentParser(description='Ingest exam questions into Supabase')
    parser.add_argument('paths', nargs='*', help='JSON file(s) with questions')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')

    args = parser.parse_args()

    pipeline = ExamQuestionIngestion()

    # Just show stats
    if args.stats:
        pipeline.print_stats()
        return

    if not args.paths:
        print("❌ No input files specified")
        print("Usage: python scripts/ingest_exam_questions.py questions.json")
        sys.exit(1)

    # Collect all JSON files
    json_paths = []
    for path_str in args.paths:
        path = Path(path_str)

        if path.is_file() and path.suffix.lower() == '.json':
            json_paths.append(str(path))
        elif '*' in path_str:
            json_paths.extend([str(p) for p in Path('.').glob(path_str)])

    if not json_paths:
        print("❌ No JSON files found")
        sys.exit(1)

    # Process all files
    all_questions = []
    for json_path in json_paths:
        questions = pipeline.load_questions_from_json(json_path)
        all_questions.extend(questions)

    # Ingest
    result = pipeline.ingest_questions(all_questions)

    # Show final stats
    print("\n" + "="*70)
    print("📊 INGESTION COMPLETE")
    print("="*70)

    if result.get('success'):
        print(f"✅ Inserted: {result['inserted']} questions")
        print(f"✅ Files processed: {len(json_paths)}")

        # Show updated stats
        pipeline.print_stats()
    else:
        print(f"❌ Ingestion failed: {result.get('error')}")


if __name__ == "__main__":
    main()
