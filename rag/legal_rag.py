"""
Legal Documents RAG (RAG #1)
Interface for legal knowledge retrieval
"""
from typing import List, Dict, Optional
from semantic_router.encoders import HuggingFaceEncoder

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag.vector_store import LegalDocsVectorStore
from config.settings import EMBEDDING_MODEL, RAG_TOP_K

class LegalRAG:
    """RAG system for legal documents"""

    def __init__(self):
        """Initialize legal RAG with encoder and vector store"""
        print(f"🔧 Initializing Legal RAG...")

        # Initialize encoder
        self.encoder = HuggingFaceEncoder(name=EMBEDDING_MODEL)

        # Initialize vector store
        self.vector_store = LegalDocsVectorStore()

        print(f"✅ Legal RAG ready ({self.vector_store.count()} chunks available)")

    def search(
        self,
        query: str,
        k: int = RAG_TOP_K,
        document_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for relevant legal content

        Args:
            query: Search query (Hebrew or English)
            k: Number of results to return
            document_name: Optional filter by document name

        Returns:
            List of relevant chunks with similarity scores
        """
        # Generate query embedding
        embedding = self.encoder([query])[0]
        query_embedding = embedding.tolist() if hasattr(embedding, 'tolist') else embedding

        # Search
        if document_name:
            results = self.vector_store.search_by_document(
                query_embedding,
                document_name,
                k=k
            )
        else:
            results = self.vector_store.similarity_search(
                query_embedding,
                k=k
            )

        return results

    def get_context(
        self,
        query: str,
        k: int = RAG_TOP_K,
        format: str = 'text'
    ) -> str:
        """
        Get formatted context for LLM

        Args:
            query: Search query
            k: Number of chunks
            format: 'text' or 'markdown'

        Returns:
            Formatted context string
        """
        results = self.search(query, k=k)

        if not results:
            return "לא נמצא מידע רלוונטי במסמכים המשפטיים."

        if format == 'markdown':
            context_parts = []
            for i, result in enumerate(results, 1):
                context_parts.append(
                    f"### מקור {i}: {result['document_name']} (עמוד {result['page_number']})\n\n"
                    f"{result['content']}\n\n"
                    f"**דמיון:** {result['similarity']:.2f}\n"
                )
            return '\n---\n\n'.join(context_parts)

        else:  # text format
            context_parts = []
            for i, result in enumerate(results, 1):
                context_parts.append(
                    f"[מקור {i}] {result['document_name']} - עמוד {result['page_number']}\n"
                    f"{result['content']}"
                )
            return '\n\n---\n\n'.join(context_parts)

    def get_legal_reference(self, query: str) -> Dict:
        """
        Get legal reference with citations

        Args:
            query: Legal question

        Returns:
            Dictionary with answer, sources, and citations
        """
        results = self.search(query, k=3)

        if not results:
            return {
                'found': False,
                'message': 'לא נמצא מידע רלוונטי'
            }

        # Extract citations
        citations = []
        for result in results:
            citation = {
                'document': result['document_name'],
                'page': result['page_number'],
                'excerpt': result['content'][:200] + '...',
                'similarity': result['similarity']
            }
            citations.append(citation)

        return {
            'found': True,
            'context': self.get_context(query, k=3),
            'citations': citations,
            'top_document': results[0]['document_name'],
            'top_page': results[0]['page_number']
        }

    def list_documents(self) -> List[str]:
        """Get list of all available legal documents"""
        return self.vector_store.get_document_list()

    def get_document_content(self, document_name: str) -> List[Dict]:
        """Get all chunks from a specific document"""
        return self.vector_store.get_document_chunks(document_name)


def test_legal_rag():
    """Test Legal RAG functionality"""
    print("Testing Legal RAG...\n")

    rag = LegalRAG()

    # Test 1: List documents
    print(f"Available documents: {rag.list_documents()}\n")

    # Test 2: Search
    test_queries = [
        "מה ההגדרה של מידע פנים?",
        "מהם העונשים על שימוש במידע פנים?",
        "מהי חובת הגילוי?"
    ]

    for query in test_queries:
        print(f"Query: {query}")
        print("="*70)

        results = rag.search(query, k=2)

        if results:
            for i, result in enumerate(results, 1):
                print(f"\nResult {i} (similarity: {result['similarity']:.3f}):")
                print(f"Document: {result['document_name']}")
                print(f"Page: {result['page_number']}")
                print(f"Content: {result['content'][:200]}...")
        else:
            print("No results found")

        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    test_legal_rag()
