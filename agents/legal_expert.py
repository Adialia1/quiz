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

    def enrich_exam_question(
        self,
        question_text: str,
        options: Dict[str, str],
        correct_answer: str
    ) -> Dict[str, Any]:
        """
        Enrich exam question with explanation, topic, difficulty, and legal references

        Args:
            question_text: The question text
            options: Dict of options (A-E)
            correct_answer: The correct answer (A-E)

        Returns:
            Dict with:
                - explanation: str - Detailed explanation
                - topic: str - Main topic/subject
                - difficulty: str - easy/medium/hard
                - legal_reference: str - Relevant law citations
        """
        # Format question for analysis
        formatted_question = f"""שאלת מבחן בנושא ניירות ערך ואתיקה:

**שאלה:**
{question_text}

**אפשרויות:**
א. {options.get('A', '')}
ב. {options.get('B', '')}
ג. {options.get('C', '')}
ד. {options.get('D', '')}
ה. {options.get('E', '')}

**תשובה נכונה:** {correct_answer}"""

        # Build enrichment query
        enrichment_query = f"""{formatted_question}

בהתבסס על השאלה והתשובה הנכונה, אנא ספק את המידע הבא:

1. **הסבר מפורט** - הסבר מדוע התשובה הנכונה היא נכונה, והסבר את הרקע המשפטי
2. **נושא עיקרי** - מהו הנושא/תחום המשפטי העיקרי של השאלה (למשל: "מידע פנים", "איסור מניפולציה", "חובות גילוי")
3. **רמת קושי** - האם השאלה קלה (easy), בינונית (medium), או קשה (hard)
4. **הפניה חוקית** - ציין את הסעיפים הרלוונטיים בחוק ניירות ערך או תקנות רלוונטיות

החזר בפורמט JSON:
```json
{{
  "explanation": "הסבר מפורט כאן...",
  "topic": "נושא עיקרי",
  "difficulty": "easy/medium/hard",
  "legal_reference": "חוק ניירות ערך, תשכ\"ח-1968, סעיף X"
}}
```"""

        self.log(f"Enriching exam question with legal context...")

        # Retrieve legal context with high k for accuracy
        context = self.retrieve_context(enrichment_query, k=15)

        # Generate enrichment using thinking model
        # Temporarily switch to thinking model for this task
        original_model = self.model
        original_temp = self.temperature

        self.model = THINKING_MODEL
        self.temperature = 0.3

        try:
            # Get enrichment from LLM
            response = self.invoke_llm(enrichment_query, context=context)

            # Parse JSON from response
            enrichment = self._parse_enrichment_response(response)

            # Validate and provide defaults
            result = {
                'explanation': enrichment.get('explanation', 'לא נמצא הסבר'),
                'topic': enrichment.get('topic', 'ניירות ערך'),
                'difficulty': enrichment.get('difficulty', 'medium'),
                'legal_reference': enrichment.get('legal_reference', '')
            }

            # Validate difficulty
            if result['difficulty'] not in ['easy', 'medium', 'hard']:
                result['difficulty'] = 'medium'

            self.log(f"✅ Enrichment complete - Topic: {result['topic']}, Difficulty: {result['difficulty']}")

            return result

        finally:
            # Restore original model settings
            self.model = original_model
            self.temperature = original_temp

    def _parse_enrichment_response(self, response: str) -> Dict[str, Any]:
        """Parse enrichment response from LLM"""
        import json
        import re

        # Try to extract JSON from code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to find JSON without code blocks
        json_match = re.search(r'(\{.*?\})', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Fallback: Try to parse entire response as JSON
        try:
            return json.loads(response)
        except:
            pass

        # Last resort: Extract manually using regex
        result = {}

        # Extract explanation
        exp_match = re.search(r'"explanation":\s*"([^"]+)"', response)
        if exp_match:
            result['explanation'] = exp_match.group(1)

        # Extract topic
        topic_match = re.search(r'"topic":\s*"([^"]+)"', response)
        if topic_match:
            result['topic'] = topic_match.group(1)

        # Extract difficulty
        diff_match = re.search(r'"difficulty":\s*"(easy|medium|hard)"', response)
        if diff_match:
            result['difficulty'] = diff_match.group(1)

        # Extract legal_reference
        ref_match = re.search(r'"legal_reference":\s*"([^"]+)"', response)
        if ref_match:
            result['legal_reference'] = ref_match.group(1)

        return result
