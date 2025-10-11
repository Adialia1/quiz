# API Quick Reference

## 🚀 Starting the API

```bash
# Method 1: Quick start script
./start_api.sh

# Method 2: Direct Python
cd api && python main.py

# Method 3: Uvicorn command
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Access Points:**
- Base URL: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs ← **Use this!**
- Alternative Docs: http://localhost:8000/redoc

---

## 📋 API Endpoints Summary

### 1️⃣ Legal Expert Question
**POST** `/api/legal/ask`

Ask questions to the Legal Expert with RAG support.

```json
{
  "question": "מהו מידע פנים?",
  "show_sources": true,
  "k": 10
}
```

### 2️⃣ Generate Questions
**POST** `/api/questions/generate`

Generate individual exam questions (1-50).

```json
{
  "count": 10,
  "topic": "מידע פנים",
  "difficulty": "medium",
  "question_type": "mixed"
}
```

**question_type options:**
- `"story"` - Emphasis on scenario-based questions
- `"basic"` - Emphasis on definition questions
- `"mixed"` - Balanced (70-80% story, 20-30% basic) ← **Default**

### 3️⃣ Generate Full Quiz
**POST** `/api/quiz/generate`

Generate full quiz with exactly 25 questions.

```json
{
  "quiz_count": 1,
  "focus_areas": ["מידע פנים", "חובות גילוי"],
  "difficulty": "medium",
  "format": "json"
}
```

**format options:**
- `"json"` - JSON response (supports multiple quizzes)
- `"pdf"` - PDF file download (only quiz_count=1)

---

## 🧪 Testing the API

```bash
# Run test client
python api/test_api.py

# Or test individual endpoints
curl http://localhost:8000/health
```

---

## 💡 Common Use Cases

### Study Assistant
```python
import requests

# 1. Ask a question
response = requests.post(
    "http://localhost:8000/api/legal/ask",
    json={"question": "מהו מידע פנים?"}
)
print(response.json()['answer'])

# 2. Generate practice questions
response = requests.post(
    "http://localhost:8000/api/questions/generate",
    json={"count": 10, "topic": "מידע פנים"}
)
questions = response.json()['questions']

# 3. Generate full exam
response = requests.post(
    "http://localhost:8000/api/quiz/generate",
    json={"format": "pdf"}
)
with open("exam.pdf", "wb") as f:
    f.write(response.content)
```

### Batch Quiz Generation
```python
# Generate 5 different quizzes
response = requests.post(
    "http://localhost:8000/api/quiz/generate",
    json={
        "quiz_count": 5,
        "difficulty": "medium",
        "format": "json"
    }
)
quizzes = response.json()['quizzes']
```

---

## 🎯 Key Features

✅ **Legal Expert with RAG** - Accurate answers with source citations
✅ **3-Stage Validation** - All questions validated by Legal Expert
✅ **Fake Company Names** - Copyright-safe scenario questions
✅ **Mixed Question Types** - Story-based (70-80%) + Basic (20-30%)
✅ **PDF Export** - Professional formatted quizzes
✅ **Batch Generation** - Generate multiple quizzes at once

---

## 📝 Parameter Reference

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `count` | int | 1-50 | Number of questions |
| `topic` | string | "מידע פנים", etc. | Specific topic or null for all |
| `difficulty` | string | easy/medium/hard | Difficulty level or null for mixed |
| `question_type` | string | story/basic/mixed | Question style (default: mixed) |
| `quiz_count` | int | 1-10 | Number of quizzes to generate |
| `focus_areas` | array | ["מידע פנים", ...] | Topics to emphasize |
| `format` | string | json/pdf | Output format |
| `show_sources` | bool | true/false | Include legal sources |
| `k` | int | 1-30 | Number of RAG chunks |

---

## 🔧 Troubleshooting

**API won't start?**
```bash
pip install fastapi uvicorn pydantic python-multipart
```

**Connection refused?**
- Make sure API is running: `./start_api.sh`
- Check correct port: http://localhost:8000

**Slow first request?**
- Normal! Agents initialize on first use
- Takes 10-30 seconds for first request
- Subsequent requests are fast

**PDF not generating?**
- Only works with `quiz_count=1`
- Check WeasyPrint installed: `pip install weasyprint`

---

## 📚 Full Documentation

- **Comprehensive Guide**: [api/README.md](README.md)
- **Interactive API Docs**: http://localhost:8000/docs (when running)
- **Quiz Generator**: [docs/QUIZ_GENERATOR_GUIDE.md](../docs/QUIZ_GENERATOR_GUIDE.md)

---

## 🎓 Example Workflow

```bash
# 1. Start the API
./start_api.sh

# 2. In another terminal, test it
python api/test_api.py

# 3. Open interactive docs
open http://localhost:8000/docs

# 4. Try generating a quiz
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -H "Content-Type: application/json" \
  -d '{"quiz_count": 1, "format": "pdf"}' \
  --output my_quiz.pdf

# 5. Success! 🎉
```
