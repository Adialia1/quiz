# Product Requirements Document (PRD)
## AI Ethica - Backend Agent System

**Version:** 1.0  
**Date:** October 2025  
**Product:** AI-Powered Learning Agent for Ethics & Securities Law Exam

---

## 1. Executive Summary

Backend AI agent system built with LangChain that powers personalized learning for Israeli Securities Authority ethics and securities law exam preparation.

---

## 2. Core Agent Features

### 2.1 Legal Knowledge Expert Agent
- Understand and retrieve information from Israeli securities law documents
- Process all ISA regulations, ethics guidelines, and legal statutes
- Maintain accurate legal citations and references
- Support Hebrew and English content
- Vector search across all legal documents

### 2.2 Question Analysis Agent
- Parse multiple-choice questions (A-E format)
- Validate student answers
- Identify legal concepts in questions
- Classify questions by topic and difficulty
- Tag questions with relevant legal areas

### 2.3 Explanation Generator Agent
- Generate basic explanations (2-3 sentences + legal citation)
- Generate detailed explanations with full legal reasoning
- Adapt explanation complexity based on user level
- Provide step-by-step legal logic
- Include relevant examples and cross-references

### 2.4 Performance Analysis Agent
- Track all question attempts and response times
- Identify weak topics based on error patterns
- Calculate topic-level mastery scores
- Detect knowledge gaps
- Measure learning velocity and improvement trends
- Generate proficiency levels (Beginner/Intermediate/Advanced/Expert)

### 2.5 Adaptive Question Selector Agent
- Select questions based on weak topics (60% weight)
- Implement spaced repetition algorithm
- Remove questions after 2 consecutive correct answers
- Increase frequency for repeated errors
- Ensure topic diversity in practice sessions
- Avoid recently-seen questions (24h minimum gap)

### 2.6 AI Mentor Chat Agent
- Answer free-form Hebrew questions about exam topics
- Provide conversational explanations of legal concepts
- Reference user's performance history in responses
- Restrict conversations to exam-related topics only
- Refuse off-topic or legal advice requests
- Maintain context across conversation turns
- Adjust language complexity to user level

### 2.7 Content Generation Agent
- Generate flashcard-style questions from legal documents
- Create practice question sets by topic
- Build randomized exam simulations (25 questions)
- Ensure proper topic distribution in exams
- Balance difficulty levels appropriately

### 2.8 Analytics & Insights Agent
- Calculate overall exam readiness score
- Track progress over time
- Compare user to cohort averages
- Predict exam pass probability
- Generate personalized study recommendations
- Identify high-priority focus topics

---