"""
Exam Questions RAG (RAG #2)
Interface for question retrieval and selection
"""
from typing import List, Dict, Optional
from semantic_router.encoders import HuggingFaceEncoder

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag.vector_store import ExamQuestionsVectorStore
from config.settings import EMBEDDING_MODEL, RAG_TOP_K, EXAM_QUESTION_COUNT

class ExamRAG:
    """RAG system for exam questions"""

    def __init__(self):
        """Initialize exam RAG with encoder and vector store"""
        print(f"🔧 Initializing Exam Questions RAG...")

        # Initialize encoder
        self.encoder = HuggingFaceEncoder(name=EMBEDDING_MODEL)

        # Initialize vector store
        self.vector_store = ExamQuestionsVectorStore()

        print(f"✅ Exam RAG ready ({self.vector_store.count()} questions available)")

    def search(
        self,
        query: str,
        k: int = RAG_TOP_K,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar questions (alias for search_similar_questions)

        Args:
            query: Search query (concept or question text)
            k: Number of results
            topic: Optional topic filter
            difficulty: Optional difficulty filter

        Returns:
            List of similar questions
        """
        return self.search_similar_questions(query, k, topic, difficulty)

    def search_similar_questions(
        self,
        query: str,
        k: int = RAG_TOP_K,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar questions

        Args:
            query: Search query (concept or question text)
            k: Number of results
            topic: Optional topic filter
            difficulty: Optional difficulty filter

        Returns:
            List of similar questions
        """
        # Generate query embedding
        embedding = self.encoder([query])[0]
        query_embedding = embedding.tolist() if hasattr(embedding, 'tolist') else embedding

        # Search with filters
        if topic:
            results = self.vector_store.search_by_topic(query_embedding, topic, k=k)
        elif difficulty:
            results = self.vector_store.search_by_difficulty(query_embedding, difficulty, k=k)
        else:
            results = self.vector_store.similarity_search(query_embedding, k=k)

        return results

    def get_questions_by_topic(
        self,
        topic: str,
        difficulty: Optional[str] = None,
        count: int = 10
    ) -> List[Dict]:
        """
        Get questions filtered by topic

        Args:
            topic: Topic to filter by
            difficulty: Optional difficulty filter
            count: Number of questions

        Returns:
            List of questions
        """
        return self.vector_store.get_random_questions(
            count=count,
            topic=topic,
            difficulty=difficulty
        )

    def get_random_exam(
        self,
        count: int = EXAM_QUESTION_COUNT,
        topic_distribution: Optional[Dict[str, int]] = None
    ) -> List[Dict]:
        """
        Generate a random exam

        Args:
            count: Total number of questions
            topic_distribution: Optional dict of {topic: count}

        Returns:
            List of exam questions
        """
        if topic_distribution:
            # Distribute questions across topics
            questions = []
            for topic, topic_count in topic_distribution.items():
                topic_questions = self.get_questions_by_topic(
                    topic=topic,
                    count=topic_count
                )
                questions.extend(topic_questions)

            # Fill remaining with random
            remaining = count - len(questions)
            if remaining > 0:
                random_questions = self.vector_store.get_random_questions(remaining)
                questions.extend(random_questions)

            return questions[:count]

        else:
            # Fully random
            return self.vector_store.get_random_questions(count)

    def get_balanced_exam(self, count: int = EXAM_QUESTION_COUNT) -> List[Dict]:
        """
        Generate a balanced exam across all topics

        Args:
            count: Total number of questions

        Returns:
            List of exam questions balanced across topics
        """
        topics = self.vector_store.get_topics()

        if not topics:
            return self.vector_store.get_random_questions(count)

        # Calculate questions per topic
        questions_per_topic = count // len(topics)
        remainder = count % len(topics)

        topic_distribution = {}
        for i, topic in enumerate(topics):
            topic_distribution[topic] = questions_per_topic
            if i < remainder:
                topic_distribution[topic] += 1

        return self.get_random_exam(count, topic_distribution)

    def find_questions_on_concept(
        self,
        concept: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Find questions that test a specific concept

        Args:
            concept: Legal concept (e.g., "מידע פנים", "חובת גילוי")
            k: Number of questions

        Returns:
            List of relevant questions
        """
        return self.search_similar_questions(concept, k=k)

    def get_questions_similar_to(
        self,
        question_id: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Find questions similar to a given question

        Args:
            question_id: UUID of reference question
            k: Number of similar questions

        Returns:
            List of similar questions
        """
        # Get reference question
        reference = self.vector_store.get_by_id(question_id)

        if not reference:
            return []

        # Search using the question's embedding
        results = self.vector_store.similarity_search(
            reference['embedding'],
            k=k + 1  # +1 because result will include the reference itself
        )

        # Filter out the reference question
        similar = [r for r in results if r['id'] != question_id]

        return similar[:k]

    def list_topics(self) -> List[str]:
        """Get list of all available topics"""
        return self.vector_store.get_topics()

    def get_topic_statistics(self) -> Dict[str, int]:
        """Get question count by topic"""
        return self.vector_store.get_topic_stats()

    def format_question_for_display(self, question: Dict) -> str:
        """
        Format question for display

        Args:
            question: Question dictionary

        Returns:
            Formatted string
        """
        formatted = f"""
שאלה: {question['question_text']}

א. {question['option_a']}
ב. {question['option_b']}
ג. {question['option_c']}
ד. {question['option_d']}
ה. {question['option_e']}

תשובה נכונה: {question['correct_answer']}
"""

        if question.get('explanation'):
            formatted += f"\nהסבר: {question['explanation']}"

        if question.get('legal_reference'):
            formatted += f"\nמקור: {question['legal_reference']}"

        if question.get('topic'):
            formatted += f"\nנושא: {question['topic']}"

        if question.get('difficulty'):
            formatted += f"\nרמת קושי: {question['difficulty']}"

        return formatted


def test_exam_rag():
    """Test Exam RAG functionality"""
    print("Testing Exam Questions RAG...\n")

    rag = ExamRAG()

    # Test 1: List topics
    print(f"Available topics: {rag.list_topics()}")
    print(f"Topic statistics: {rag.get_topic_statistics()}\n")

    # Test 2: Search for questions on a concept
    concept = "מידע פנים"
    print(f"Searching questions about: {concept}")
    print("="*70)

    questions = rag.find_questions_on_concept(concept, k=3)

    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i} (similarity: {q['similarity']:.3f}):")
        print(rag.format_question_for_display(q))
        print("-"*70)

    # Test 3: Generate random exam
    print("\nGenerating balanced exam...")
    exam = rag.get_balanced_exam(count=5)

    print(f"\n✅ Generated exam with {len(exam)} questions")
    for i, q in enumerate(exam, 1):
        print(f"\n{i}. {q['question_text'][:50]}... (Topic: {q.get('topic', 'N/A')})")


if __name__ == "__main__":
    test_exam_rag()
