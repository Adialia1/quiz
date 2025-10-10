"""
Base Agent Class for AI Ethica System
All specialized agents inherit from this base
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_models import ChatOpenAI

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import OPENROUTER_API_KEY, GEMINI_MODEL, THINKING_MODEL


class BaseAgent(ABC):
    """
    Base class for all AI agents in the system

    Provides common functionality:
    - LLM initialization
    - Message handling
    - Logging
    - Error handling
    """

    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        model: str = GEMINI_MODEL,
        temperature: float = 0.1
    ):
        """
        Initialize base agent

        Args:
            agent_name: Name of the agent (for logging)
            system_prompt: System prompt that defines agent behavior
            model: LLM model to use
            temperature: Sampling temperature (0.0 = deterministic)
        """
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature

        # Initialize LLM via OpenRouter
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=4000
        )

        # Message history for this agent
        self.messages: List[Any] = [SystemMessage(content=system_prompt)]

        print(f"✅ {agent_name} initialized (model: {model})")

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method - must be implemented by each agent

        Args:
            input_data: Input data specific to the agent

        Returns:
            Output data from the agent
        """
        pass

    def invoke_llm(
        self,
        user_message: str,
        context: Optional[str] = None,
        include_history: bool = False
    ) -> str:
        """
        Invoke LLM with message

        Args:
            user_message: User's message
            context: Optional additional context
            include_history: Whether to include conversation history

        Returns:
            LLM response
        """
        # Build messages
        messages = []

        if include_history:
            messages.extend(self.messages)
        else:
            messages.append(SystemMessage(content=self.system_prompt))

        # Add context if provided
        if context:
            messages.append(SystemMessage(content=f"Context:\n{context}"))

        # Add user message
        messages.append(HumanMessage(content=user_message))

        # Invoke LLM
        try:
            response = self.llm.invoke(messages)

            # Store in history if tracking
            if include_history:
                self.messages.append(HumanMessage(content=user_message))
                self.messages.append(AIMessage(content=response.content))

            return response.content

        except Exception as e:
            print(f"❌ {self.agent_name} LLM error: {e}")
            return f"Error: {str(e)}"

    def clear_history(self):
        """Clear conversation history"""
        self.messages = [SystemMessage(content=self.system_prompt)]

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history

        Returns:
            List of message dicts with 'role' and 'content'
        """
        history = []
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history

    def log(self, message: str, level: str = "INFO"):
        """
        Log agent activity

        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.agent_name}] [{level}] {message}")


class RAGAgent(BaseAgent):
    """
    Base class for agents that use RAG (Retrieval Augmented Generation)
    """

    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        rag_system: Any,
        model: str = GEMINI_MODEL,
        temperature: float = 0.1,
        top_k: int = 5
    ):
        """
        Initialize RAG-enabled agent

        Args:
            agent_name: Name of the agent
            system_prompt: System prompt
            rag_system: RAG system instance (LegalRAG or ExamRAG)
            model: LLM model
            temperature: Sampling temperature
            top_k: Number of chunks to retrieve
        """
        super().__init__(agent_name, system_prompt, model, temperature)

        self.rag_system = rag_system
        self.top_k = top_k

    def retrieve_context(self, query: str, k: Optional[int] = None) -> str:
        """
        Retrieve context from RAG system

        Args:
            query: Search query
            k: Number of results (uses default if None)

        Returns:
            Formatted context string
        """
        k = k or self.top_k

        try:
            context = self.rag_system.get_context(query, k=k, format='text')
            return context

        except Exception as e:
            self.log(f"RAG retrieval error: {e}", level="ERROR")
            return "לא נמצא מידע רלוונטי."

    def process_with_rag(
        self,
        query: str,
        k: Optional[int] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process query with RAG

        Args:
            query: User query
            k: Number of chunks to retrieve
            additional_context: Optional additional context

        Returns:
            Dict with answer, sources, and metadata
        """
        # Retrieve context
        context = self.retrieve_context(query, k)

        # Build full context
        full_context = context
        if additional_context:
            full_context = f"{additional_context}\n\n{context}"

        # Generate answer
        answer = self.invoke_llm(query, context=full_context)

        return {
            "query": query,
            "answer": answer,
            "context": context,
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat()
        }
