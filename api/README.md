# Quiz Generator & Legal Expert API

REST API for generating exam questions and querying the Legal Expert Agent.

## 🚀 Quick Start

### Installation

```bash
# Install FastAPI dependencies
pip install -r api/requirements.txt
```

### Running the API

```bash
# From the project root directory
cd api
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

---

## 📚 API Endpoints

### 1. Legal Expert Question (`/api/legal/ask`)

Ask a question to the Legal Expert Agent with RAG.

**Method**: `POST`

**Request Body**:
```json
{
  "question": "מהו מידע פנים לפי חוק ניירות ערך?",
  "show_sources": true,
  "k": 10
}
```

**Parameters**:
- `question` (required): Legal question to ask
- `show_sources` (optional, default: `true`): Include source references
- `k` (optional, default: `10`): Number of relevant legal chunks to use (1-30)

**Response**:
```json
{
  "answer": "מידע פנים הוא מידע אשר...",
  "sources": [
    "חוק ניירות ערך, תשכ\"ח-1968, סעיף 52(א)",
    "תקנות ניירות ערך..."
  ],
  "query": "מהו מידע פנים לפי חוק ניירות ערך?",
  "timestamp": "2025-10-11T10:30:00"
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/legal/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "מהו מידע פנים?",
    "show_sources": true
  }'
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/legal/ask",
    json={
        "question": "מהי חובת הגילוי של חברה ציבורית?",
        "show_sources": True,
        "k": 15
    }
)

data = response.json()
print(f"Answer: {data['answer']}")
print(f"Sources: {data['sources']}")
```

---

### 2. Generate Questions (`/api/questions/generate`)

Generate individual exam questions using the Quiz Generator Agent.

**Method**: `POST`

**Request Body**:
```json
{
  "count": 5,
  "topic": "מידע פנים",
  "difficulty": "medium",
  "question_type": "mixed"
}
```

**Parameters**:
- `count` (required): Number of questions to generate (1-50)
- `topic` (optional): Specific topic (e.g., "מידע פנים", "חובות גילוי")
- `difficulty` (optional): "easy", "medium", or "hard"
- `question_type` (optional, default: "mixed"):
  - `"story"`: Emphasis on story-based scenarios
  - `"basic"`: Emphasis on basic definitions
  - `"mixed"`: Balanced (70-80% story, 20-30% basic)

**Response**:
```json
{
  "questions": [
    {
      "question_number": 1,
      "question_text": "שוקי, יועץ השקעות בחברת פיננס-טק בע\"מ...",
      "options": {
        "A": "אפשרות א",
        "B": "אפשרות ב",
        "C": "אפשרות ג",
        "D": "אפשרות ד",
        "E": "אפשרות ה"
      },
      "correct_answer": "B",
      "explanation": "הסבר מפורט...",
      "topic": "מידע פנים",
      "difficulty": "medium",
      "legal_reference": "חוק ניירות ערך, סעיף 52",
      "generated": true,
      "validated_by_expert": true,
      "expert_validation": {
        "validated": true,
        "confidence": "high"
      }
    }
  ],
  "metadata": {
    "question_count": 5,
    "topic": "מידע פנים",
    "difficulty": "medium",
    "question_type": "mixed",
    "generated_at": "2025-10-11T10:30:00",
    "validation_stats": {
      "generated": 10,
      "structurally_valid": 8,
      "expert_validated": 5,
      "final_count": 5
    }
  },
  "reference_sources": ["..."]
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/questions/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 10,
    "difficulty": "hard",
    "question_type": "story"
  }'
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/questions/generate",
    json={
        "count": 10,
        "topic": "חובות גילוי",
        "difficulty": "easy",
        "question_type": "mixed"
    }
)

data = response.json()
questions = data['questions']
print(f"Generated {len(questions)} questions")

for q in questions:
    print(f"\nQ{q['question_number']}: {q['question_text'][:100]}...")
    print(f"Correct Answer: {q['correct_answer']}")
    print(f"Difficulty: {q['difficulty']}")
```

---

### 3. Generate Full Quiz (`/api/quiz/generate`)

Generate full quiz(zes) with exactly 25 questions each.

**Method**: `POST`

**Request Body**:
```json
{
  "quiz_count": 1,
  "focus_areas": ["מידע פנים", "חובות גילוי"],
  "difficulty": "medium",
  "format": "json"
}
```

**Parameters**:
- `quiz_count` (optional, default: `1`): Number of quizzes to generate (1-10)
- `focus_areas` (optional): List of topics to emphasize
- `difficulty` (optional): "easy", "medium", or "hard"
- `format` (optional, default: `"json"`): "json" or "pdf"

**Response (JSON format)**:
```json
{
  "questions": [...],  // 25 questions
  "metadata": {
    "question_count": 25,
    "quiz_number": 1,
    "total_quizzes": 1,
    "difficulty": "medium",
    "focus_areas": ["מידע פנים", "חובות גילוי"],
    "generated_at": "2025-10-11T10:30:00"
  },
  "reference_sources": [...]
}
```

**Response (PDF format)**:
- Returns downloadable PDF file with:
  - All 25 questions
  - Answer table
  - Detailed explanations
  - Legal references

**Important**: PDF format only works with `quiz_count=1`. For multiple quizzes, use JSON format.

**cURL Example (JSON)**:
```bash
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "quiz_count": 1,
    "difficulty": "medium",
    "format": "json"
  }'
```

**cURL Example (PDF)**:
```bash
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "quiz_count": 1,
    "difficulty": "hard",
    "format": "pdf"
  }' \
  --output quiz.pdf
```

**Python Example (JSON)**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/quiz/generate",
    json={
        "quiz_count": 2,
        "focus_areas": ["מידע פנים", "מניפולציה"],
        "difficulty": "medium",
        "format": "json"
    }
)

data = response.json()
quizzes = data['quizzes']

for quiz in quizzes:
    print(f"\nQuiz #{quiz['metadata']['quiz_number']}")
    print(f"Questions: {len(quiz['questions'])}")
```

**Python Example (PDF)**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/quiz/generate",
    json={
        "quiz_count": 1,
        "difficulty": "easy",
        "format": "pdf"
    }
)

# Save PDF file
with open("quiz_exam.pdf", "wb") as f:
    f.write(response.content)

print("✅ PDF saved: quiz_exam.pdf")
```

---

## 🔧 Simplified GET Endpoints

For simple testing and quick queries, use these GET endpoints:

### Legal Question (GET)
```bash
GET /api/legal/ask-simple?question=מהו מידע פנים?&show_sources=true
```

### Generate Questions (GET)
```bash
GET /api/questions/generate-simple?count=5&topic=מידע פנים&difficulty=medium
```

---

## 📊 Additional Endpoints

### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2025-10-11T10:30:00",
  "agents": {
    "legal_expert": "initialized",
    "quiz_generator": "initialized"
  }
}
```

### API Root
```bash
GET /

Response:
{
  "message": "Quiz Generator & Legal Expert API",
  "version": "1.0.0",
  "endpoints": {
    "legal_question": "/api/legal/ask",
    "generate_questions": "/api/questions/generate",
    "generate_quiz": "/api/quiz/generate"
  },
  "docs": "/docs"
}
```

---

## 🎯 Complete Usage Examples

### Example 1: Study Session Flow

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Ask a legal question to understand a concept
response = requests.post(
    f"{BASE_URL}/api/legal/ask",
    json={"question": "מהו מידע פנים?", "show_sources": True}
)
print("Legal Expert Answer:")
print(response.json()['answer'])

# 2. Generate practice questions on that topic
response = requests.post(
    f"{BASE_URL}/api/questions/generate",
    json={
        "count": 10,
        "topic": "מידע פנים",
        "difficulty": "medium",
        "question_type": "mixed"
    }
)
questions = response.json()['questions']
print(f"\nGenerated {len(questions)} practice questions")

# 3. Generate a full practice exam
response = requests.post(
    f"{BASE_URL}/api/quiz/generate",
    json={
        "quiz_count": 1,
        "difficulty": "medium",
        "format": "pdf"
    }
)

with open("practice_exam.pdf", "wb") as f:
    f.write(response.content)
print("\n✅ Full practice exam saved!")
```

### Example 2: Batch Quiz Generation

```python
import requests

BASE_URL = "http://localhost:8000"

# Generate 3 quizzes focused on specific weak areas
response = requests.post(
    f"{BASE_URL}/api/quiz/generate",
    json={
        "quiz_count": 3,
        "focus_areas": ["מידע פנים", "חובות גילוי", "מניפולציה"],
        "difficulty": "hard",
        "format": "json"
    }
)

data = response.json()
quizzes = data['quizzes']

# Save each quiz separately
for quiz in quizzes:
    quiz_num = quiz['metadata']['quiz_number']
    filename = f"quiz_{quiz_num}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(quiz, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {filename} ({len(quiz['questions'])} questions)")
```

### Example 3: Interactive Legal Assistant

```python
import requests

BASE_URL = "http://localhost:8000"

def ask_legal_expert(question, show_sources=True):
    """Ask a question to the legal expert"""
    response = requests.post(
        f"{BASE_URL}/api/legal/ask",
        json={
            "question": question,
            "show_sources": show_sources,
            "k": 15
        }
    )

    data = response.json()
    print(f"\n❓ Question: {question}")
    print(f"\n✅ Answer:\n{data['answer']}")

    if show_sources and data.get('sources'):
        print(f"\n📚 Sources:")
        for i, source in enumerate(data['sources'][:3], 1):
            print(f"   {i}. {source}")

# Interactive session
questions = [
    "מהו מידע פנים?",
    "מהי חובת הגילוי של חברה ציבורית?",
    "מהו איסור מניפולציה בשוק ההון?"
]

for q in questions:
    ask_legal_expert(q)
    print("\n" + "="*70)
```

---

## 🐛 Error Handling

All endpoints return standard HTTP status codes:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid parameters
- **404 Not Found**: Endpoint not found
- **500 Internal Server Error**: Server error

Error response format:
```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "detail": "Additional details"
}
```

---

## 🚀 Production Deployment

### Using Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t quiz-api .
docker run -p 8000:8000 quiz-api
```

### Environment Variables

```bash
# .env file
OPENROUTER_API_KEY=your_api_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Production Settings

For production, modify `main.py`:

```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    reload=False,  # Disable auto-reload
    workers=4,     # Multiple workers
    log_level="warning"
)
```

---

## 📝 Notes

1. **First Request**: The first API request may take longer as agents are initialized
2. **PDF Generation**: Only available for single quizzes (`quiz_count=1`)
3. **Rate Limiting**: Consider implementing rate limiting for production use
4. **Caching**: Legal Expert responses could be cached for common questions
5. **Validation**: All questions are validated by Legal Expert Agent for accuracy

---

## 🔗 Related Documentation

- [Quiz Generator Guide](../docs/QUIZ_GENERATOR_GUIDE.md)
- [Legal Expert Documentation](../docs/LEGAL_EXPERT.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 📞 Support

For issues or questions, please refer to the main project documentation.
