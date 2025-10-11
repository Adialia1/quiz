"""
AI Ethica Agents Module

Available Agents:
- LegalExpertAgent: Answers legal questions using Legal RAG
"""
from agent.agents.base_agent import BaseAgent, RAGAgent
from agent.agents.legal_expert import LegalExpertAgent

__all__ = [
    "BaseAgent",
    "RAGAgent",
    "LegalExpertAgent"
]
