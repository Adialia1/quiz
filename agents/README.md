# AI Ethica Agents

LangChain-based AI agents for Israeli Securities Authority ethics exam preparation.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              User Interface                      │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│          Agent Orchestrator (Future)             │
│              LangGraph                           │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼──────────┐  ┌──────▼──────────┐
│ Legal Expert     │  │ Chat Mentor     │
│ Agent            │  │ Agent           │
│                  │  │                 │
│ • Legal Q&A      │  │ • Conversational│
│ • Citations      │  │ • Memory        │
│ • Article lookup │  │ • Adaptive      │
└─────────┬────────┘  └────────┬────────┘
          │                    │
          └──────────┬─────────┘
                     │
          ┌──────────▼──────────┐
          │   Legal RAG         │
          │   (1,415 chunks)    │
          └─────────────────────┘
```

## Available Agents

### 1. Legal Expert Agent

**Purpose:** Answer legal questions with precision and citations

**Capabilities:**
- Answer questions about Israeli securities law
- Provide legal citations (document + page)
- Explain legal concepts
- Find specific articles
- Compare legal concepts
- List penalties for violations

**Use Cases:**
- "מה ההגדרה של 'איש פנים'?"
- "מהם העונשים על שימוש במידע פנים?"
- "מצא סעיף 52 בחוק ניירות ערך"

**Example:**
```python
from agents import LegalExpertAgent

agent = LegalExpertAgent()

result = agent.process({
    "query": "מה זה מידע פנים?",
    "k": 5  # Retrieve 5 chunks
})

print(result['answer'])
print(result['sources'])  # Citations
```

**Response Style:**
- Formal and precise
- Always includes legal citations
- Based strictly on retrieved documents
- Temperature: 0.1 (deterministic)

---

### 2. Chat Mentor Agent

**Purpose:** Conversational tutor with memory for learning support

**Capabilities:**
- Explain concepts in simple language
- Adapt to user proficiency level
- Remember conversation context
- Provide examples and analogies
- Encourage and motivate
- Track topics discussed

**Use Cases:**
- Learning new concepts
- Asking follow-up questions
- Getting clarifications
- Understanding with examples

**Example:**
```python
from agents import ChatMentorAgent

agent = ChatMentorAgent(user_id="student_123")

# Turn 1
result1 = agent.process({
    "message": "מה זה מידע פנים?"
})

# Turn 2 (remembers context)
result2 = agent.process({
    "message": "תוכל להסביר עם דוגמה?"
})

# Get conversation summary
summary = agent.get_conversation_summary()
```

**Response Style:**
- Conversational and friendly
- Uses examples and analogies
- Adapts complexity to user level
- Temperature: 0.3 (more variety)

**Memory Features:**
- Conversation history
- Topics discussed
- User proficiency level
- Session tracking

---

## Agent Classes

### BaseAgent

Base class for all agents

```python
class BaseAgent(ABC):
    def __init__(self, agent_name, system_prompt, model, temperature)
    def process(self, input_data) -> Dict  # Abstract
    def invoke_llm(self, user_message, context, include_history)
    def clear_history()
    def get_history()
```

### RAGAgent

Base class for RAG-enabled agents (inherits from BaseAgent)

```python
class RAGAgent(BaseAgent):
    def __init__(self, agent_name, system_prompt, rag_system, ...)
    def retrieve_context(self, query, k)
    def process_with_rag(self, query, k, additional_context)
```

---

## System Prompts

Located in `config/prompts.py`

Each agent has a specialized Hebrew prompt that defines:
- Role and responsibilities
- Behavior guidelines
- Response format
- Constraints and limitations

**Example (Legal Expert):**
```python
LEGAL_EXPERT_PROMPT = """אתה מומחה משפטי בדיני ניירות ערך...

**תפקידך:**
- לענות על שאלות משפטיות
- לצטט מקורות
- להסביר מושגים

**כללים:**
1. דיוק משפטי
2. ציטוט מקורות
3. בהירות
..."""
```

---

## Testing

### Run All Tests
```bash
python scripts/test_agents.py
```

### Test Individual Agents
```bash
# Legal Expert
python agents/legal_expert.py

# Chat Mentor
python agents/chat_mentor.py
```

### Expected Output
```
🧪 TESTING LEGAL EXPERT AGENT
✅ Test 1: Definition Question
✅ Test 2: Penalty Question
✅ Test 3: Comparison Question

🧪 TESTING CHAT MENTOR AGENT
✅ 4-turn conversation simulation
📊 Conversation summary

🧪 AGENT COMPARISON TEST
✅ Style differences demonstrated
```

---

## Configuration

### Model Settings (config/settings.py)
```python
GEMINI_MODEL = "google/gemini-2.0-flash-001"
RAG_TOP_K = 5  # Default chunks to retrieve
```

### Per-Agent Override
```python
# More creative for chat
agent = ChatMentorAgent(
    model="google/gemini-2.0-flash-001",
    temperature=0.5,  # Higher for variety
    top_k=3
)

# More deterministic for legal
agent = LegalExpertAgent(
    temperature=0.0,  # Fully deterministic
    top_k=7  # More context
)
```

---

## Performance

### Legal Expert Agent
- **Retrieval:** ~200ms (3-5 chunks)
- **LLM Response:** ~2-3 seconds
- **Total:** ~2-3 seconds per query

### Chat Mentor Agent
- **Retrieval:** ~200ms (when needed)
- **LLM Response:** ~2-4 seconds (longer due to history)
- **Total:** ~2-4 seconds per turn

---

## Future Agents (Coming Soon)

### 3. Explanation Generator Agent
- Generate question explanations
- Explain why answers are correct/incorrect
- Provide learning tips

### 4. Performance Tracker Agent
- Analyze user performance
- Identify weak topics
- Track improvement over time

### 5. Question Selector Agent
- Adaptive question selection
- Spaced repetition
- Difficulty balancing

### 6. Content Generator Agent
- Create flashcards
- Generate practice questions
- Build mock exams

### 7. Analytics Agent
- Exam readiness score
- Pass probability prediction
- Study recommendations

---

## Implementation Details

### LLM Provider
- **OpenRouter** with Gemini 2.0 Flash
- Best for Hebrew understanding
- Fast and cost-effective

### RAG Integration
- Uses Legal RAG (1,415 chunks)
- Semantic search with multilingual-e5-large
- Supabase pgvector backend

### Conversation Memory
- Stored in agent instance
- LangChain message history
- Session-based tracking
- Future: Persist to Supabase

---

## Best Practices

### When to Use Legal Expert
- Need precise legal information
- Want source citations
- Looking up specific articles
- Comparing legal concepts

### When to Use Chat Mentor
- Learning new topics
- Need explanations with examples
- Want conversational interaction
- Multi-turn conversations

### Combining Agents
```python
# Get formal legal info
legal_agent = LegalExpertAgent()
legal_info = legal_agent.process({"query": "מה זה מידע פנים?"})

# Then explain it conversationally
chat_agent = ChatMentorAgent()
explanation = chat_agent.process({
    "message": "הסבר לי את זה בפשטות",
    "use_rag": False  # Use legal_info as context instead
})
```

---

## Troubleshooting

### Agent initialization fails
```python
# Check RAG system is working
from rag.legal_rag import LegalRAG
rag = LegalRAG()  # Should show "1415 chunks available"
```

### No context retrieved
```python
# Check vector store
result = agent.process({"query": "test", "k": 1})
print(result.get('context'))  # Should not be empty
```

### LLM errors
```python
# Check API key
import os
print(os.getenv('OPENROUTER_API_KEY'))  # Should be set
```

---

## Examples

See `scripts/test_agents.py` for comprehensive examples of:
- Single-turn queries
- Multi-turn conversations
- Error handling
- Response parsing
- Source citation extraction

---

## Contributing

When adding new agents:
1. Inherit from `BaseAgent` or `RAGAgent`
2. Add system prompt to `config/prompts.py`
3. Implement `process()` method
4. Add to `agents/__init__.py`
5. Create test file
6. Update this README

---

**Built with ❤️ for Israeli Securities Authority exam preparation**
