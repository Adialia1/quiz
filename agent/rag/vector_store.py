"""
Supabase vector store wrapper for LangChain integration
"""
from typing import List, Dict, Optional, Tuple
import numpy as np

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from agent.config.settings import (
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    RAG_TOP_K,
    RAG_SCORE_THRESHOLD,
    validate_config
)

class SupabaseVectorStore:
    """Base class for Supabase vector operations"""

    def __init__(self, table_name: str, match_function: str):
        """
        Initialize vector store

        Args:
            table_name: Name of the Supabase table
            match_function: Name of the similarity search function
        """
        validate_config()

        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.table_name = table_name
        self.match_function = match_function

    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = RAG_TOP_K,
        score_threshold: float = RAG_SCORE_THRESHOLD,
        **kwargs
    ) -> List[Dict]:
        """
        Perform similarity search

        Args:
            query_embedding: Query vector
            k: Number of results
            score_threshold: Minimum similarity score
            **kwargs: Additional filter parameters

        Returns:
            List of matching documents with scores
        """
        try:
            # Call the match function
            response = self.client.rpc(
                self.match_function,
                {
                    'query_embedding': query_embedding,
                    'match_count': k,
                    'match_threshold': score_threshold,
                    **kwargs
                }
            ).execute()

            return response.data

        except Exception as e:
            print(f"❌ Error in similarity search: {e}")
            return []

    def get_by_id(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID"""
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('id', doc_id)\
                .execute()

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            print(f"❌ Error fetching document: {e}")
            return None

    def count(self) -> int:
        """Get total count of documents"""
        try:
            response = self.client.table(self.table_name)\
                .select('id', count='exact')\
                .execute()

            return response.count

        except Exception as e:
            print(f"❌ Error counting documents: {e}")
            return 0


class LegalDocsVectorStore(SupabaseVectorStore):
    """Vector store for legal document chunks"""

    def __init__(self):
        super().__init__(
            table_name='legal_doc_chunks',
            match_function='match_legal_chunks'
        )

    def search_by_document(
        self,
        query_embedding: List[float],
        document_name: str,
        k: int = RAG_TOP_K
    ) -> List[Dict]:
        """
        Search within a specific document

        Args:
            query_embedding: Query vector
            document_name: Name of the document to search in
            k: Number of results

        Returns:
            Matching chunks from the specified document
        """
        try:
            # First do similarity search
            results = self.similarity_search(query_embedding, k=k * 3)  # Get more candidates

            # Filter by document name
            filtered = [r for r in results if r['document_name'] == document_name]

            return filtered[:k]

        except Exception as e:
            print(f"❌ Error in document search: {e}")
            return []

    def get_document_list(self) -> List[str]:
        """Get list of all available documents"""
        try:
            response = self.client.table(self.table_name)\
                .select('document_name')\
                .execute()

            # Get unique document names
            docs = list(set(row['document_name'] for row in response.data))
            return sorted(docs)

        except Exception as e:
            print(f"❌ Error fetching documents: {e}")
            return []

    def get_document_chunks(self, document_name: str) -> List[Dict]:
        """Get all chunks from a specific document"""
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('document_name', document_name)\
                .order('chunk_index')\
                .execute()

            return response.data

        except Exception as e:
            print(f"❌ Error fetching document chunks: {e}")
            return []


class ExamQuestionsVectorStore(SupabaseVectorStore):
    """Vector store for exam questions"""

    def __init__(self):
        super().__init__(
            table_name='exam_questions',
            match_function='match_exam_questions'
        )

    def search_by_topic(
        self,
        query_embedding: List[float],
        topic: str,
        k: int = RAG_TOP_K
    ) -> List[Dict]:
        """
        Search questions by topic

        Args:
            query_embedding: Query vector
            topic: Topic to filter by
            k: Number of results

        Returns:
            Matching questions from the specified topic
        """
        return self.similarity_search(
            query_embedding,
            k=k,
            filter_topic=topic
        )

    def search_by_difficulty(
        self,
        query_embedding: List[float],
        difficulty: str,
        k: int = RAG_TOP_K
    ) -> List[Dict]:
        """
        Search questions by difficulty

        Args:
            query_embedding: Query vector
            difficulty: Difficulty level (easy, medium, hard)
            k: Number of results

        Returns:
            Matching questions of specified difficulty
        """
        return self.similarity_search(
            query_embedding,
            k=k,
            filter_difficulty=difficulty
        )

    def get_random_questions(
        self,
        count: int = 25,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict]:
        """
        Get random questions with optional filters

        Args:
            count: Number of questions
            topic: Optional topic filter
            difficulty: Optional difficulty filter

        Returns:
            List of random questions
        """
        try:
            query = self.client.table(self.table_name)\
                .select('*')\
                .eq('is_active', True)

            if topic:
                query = query.eq('topic', topic)

            if difficulty:
                query = query.eq('difficulty', difficulty)

            # PostgreSQL random sampling
            response = query.limit(count * 2).execute()  # Get more then sample

            # Randomly sample
            results = response.data
            if len(results) > count:
                import random
                results = random.sample(results, count)

            return results

        except Exception as e:
            print(f"❌ Error fetching random questions: {e}")
            return []

    def get_topics(self) -> List[str]:
        """Get list of all available topics"""
        try:
            response = self.client.table(self.table_name)\
                .select('topic')\
                .execute()

            topics = list(set(row['topic'] for row in response.data if row['topic']))
            return sorted(topics)

        except Exception as e:
            print(f"❌ Error fetching topics: {e}")
            return []

    def get_topic_stats(self) -> Dict[str, int]:
        """Get question count by topic"""
        try:
            response = self.client.table(self.table_name)\
                .select('topic')\
                .execute()

            stats = {}
            for row in response.data:
                topic = row['topic'] or 'Unknown'
                stats[topic] = stats.get(topic, 0) + 1

            return stats

        except Exception as e:
            print(f"❌ Error fetching topic stats: {e}")
            return {}


def test_vector_stores():
    """Test vector store operations"""
    print("Testing Legal Docs Vector Store...")
    legal_store = LegalDocsVectorStore()

    print(f"Total legal chunks: {legal_store.count()}")
    print(f"Documents: {legal_store.get_document_list()}")

    print("\nTesting Exam Questions Vector Store...")
    exam_store = ExamQuestionsVectorStore()

    print(f"Total questions: {exam_store.count()}")
    print(f"Topics: {exam_store.get_topics()}")
    print(f"Topic stats: {exam_store.get_topic_stats()}")


if __name__ == "__main__":
    test_vector_stores()
