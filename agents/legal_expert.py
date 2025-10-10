"""
Legal Expert Agent
Uses Legal RAG to answer questions about Israeli securities law
"""
from typing import Dict, Any, Optional, List

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.base_agent import RAGAgent
from rag.legal_rag import LegalRAG
from config.prompts import LEGAL_EXPERT_PROMPT
from config.settings import GEMINI_MODEL, THINKING_MODEL


class LegalExpertAgent(RAGAgent):
    """
    Legal Expert Agent - Answers legal questions using Legal RAG

    Capabilities:
    - Answer questions about securities law
    - Provide legal citations
    - Explain legal concepts
    - Reference specific articles and regulations
    """

    def __init__(
        self,
        model: str = GEMINI_MODEL,
        temperature: float = 0.1,
        top_k: int = 10,
        use_thinking_model: bool = False
    ):
        """
        Initialize Legal Expert Agent

        Args:
            model: LLM model to use
            temperature: Sampling temperature (low for factual answers)
            top_k: Number of chunks to retrieve from RAG
            use_thinking_model: If True, uses more powerful reasoning model
        """
        # Use thinking model if requested
        if use_thinking_model:
            model = THINKING_MODEL
            temperature = 0.3  # Slightly higher for reasoning
        # Initialize Legal RAG
        legal_rag = LegalRAG()

        # Initialize as RAG agent
        super().__init__(
            agent_name="Legal Expert",
            system_prompt=LEGAL_EXPERT_PROMPT,
            rag_system=legal_rag,
            model=model,
            temperature=temperature,
            top_k=top_k
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process legal question

        Args:
            input_data: Dict with:
                - query: str - Legal question
                - k: int (optional) - Number of chunks to retrieve
                - document: str (optional) - Specific document to search

        Returns:
            Dict with answer, sources, and citations
        """
        query = input_data.get("query")
        k = input_data.get("k", self.top_k)
        document = input_data.get("document")

        if not query:
            return {
                "error": "No query provided",
                "agent": self.agent_name
            }

        self.log(f"Processing query: {query[:50]}...")

        # Retrieve context
        if document:
            # Search in specific document
            results = self.rag_system.vector_store.search_by_document(
                self.rag_system.encoder([query])[0].tolist()
                if hasattr(self.rag_system.encoder([query])[0], 'tolist')
                else self.rag_system.encoder([query])[0],
                document_name=document,
                k=k
            )
            context = self._format_results(results)
        else:
            # General search
            context = self.retrieve_context(query, k=k)

        # Generate answer
        answer = self.invoke_llm(query, context=context)

        # Get sources for citations
        sources = self._extract_sources(context)

        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "context": context,
            "agent": self.agent_name,
            "model": self.model
        }

    def _format_results(self, results: List[Dict]) -> str:
        """Format search results into context"""
        if not results:
            return "לא נמצא מידע רלוונטי במסמכים המשפטיים."

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[מקור {i}] {result['document_name']} - עמוד {result['page_number']}\n"
                f"{result['content']}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _extract_sources(self, context: str) -> List[Dict[str, Any]]:
        """Extract source citations from context"""
        sources = []

        # Parse context to extract sources
        parts = context.split("---")
        for part in parts:
            if "[מקור" in part:
                lines = part.strip().split("\n")
                if lines:
                    # Extract document name and page from first line
                    header = lines[0]
                    # Format: [מקור X] DocumentName - עמוד Y
                    try:
                        doc_part = header.split("]")[1].strip()
                        doc_name = doc_part.split(" - ")[0].strip()
                        page = doc_part.split("עמוד")[1].strip() if "עמוד" in doc_part else "N/A"

                        sources.append({
                            "document": doc_name,
                            "page": page
                        })
                    except:
                        pass

        return sources
