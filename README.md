# AI Ethica - Backend Agent System

Backend AI agent system for Israeli Securities Authority ethics and securities law exam preparation.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              LangGraph Agents                    │
│  - Legal Expert (RAG #1)                         │
│  - Question Analyzer (RAG #2)                    │
│  - Explanation Generator                         │
│  - Performance Tracker                           │
│  - Question Selector                             │
│  - Chat Mentor                                   │
│  - Content Generator                             │
│  - Analytics                                     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│            SUPABASE (PostgreSQL)                 │
│  ┌───────────────────────────────────────────┐  │
│  │  Relational Tables                        │  │
│  │  - users, user_performance                │  │
│  │  - chat_history, study_sessions           │  │
│  │  - topic_mastery                          │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  Vector Tables (pgvector)                 │  │
│  │  - legal_doc_chunks (RAG #1)              │  │
│  │  - exam_questions (RAG #2)                │  │
│  └───────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- Supabase account (free tier is fine)
- OpenRouter API key (for Gemini OCR)
- Poppler (for PDF processing)

**Install Poppler:**
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows (via chocolatey)
choco install poppler
```

### 2. Installation

```bash
# Clone repo
git clone <your-repo>
cd quiz

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Go to **Settings → Database** → Copy your connection details
3. Go to **Settings → API** → Copy your keys

4. **Enable pgvector extension:**
   - Dashboard → Database → Extensions
   - Search for "vector" and enable it

5. Update `.env` with your credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
OPENROUTER_API_KEY=your-openrouter-key
```

6. **Run schema setup:**
```bash
python scripts/setup_supabase.py
```

This creates all necessary tables:
- `legal_doc_chunks` - Legal document chunks (RAG #1)
- `exam_questions` - Exam questions (RAG #2)
- `users` - User accounts
- `user_performance` - Question attempts
- `chat_messages` - Chat history
- `study_sessions` - Study session tracking
- `topic_mastery` - Topic-level progress

### 4. Ingest Legal Documents

Place your legal PDFs in a folder (e.g., `legal_documents/`), then run:

**Quick batch ingestion:**

```bash
# Ingest ALL PDFs in legal_documents/ folder
python scripts/ingest_all_legal_docs.py

# With options
python scripts/ingest_all_legal_docs.py --skip-existing  # Skip already processed
python scripts/ingest_all_legal_docs.py --max-pages 5    # Test with 5 pages each

# Or use bash script
./scripts/ingest_all_legal_docs.sh
```

**Individual file control:**

```bash
# Single file
python scripts/ingest_legal_docs.py legal_documents/legal1.pdf

# Multiple specific files
python scripts/ingest_legal_docs.py legal1.pdf legal2.pdf legal3.pdf

# Entire directory
python scripts/ingest_legal_docs.py legal_documents/

# Test mode (5 pages only)
python scripts/ingest_legal_docs.py legal1.pdf --max-pages 5

# Skip already ingested
python scripts/ingest_legal_docs.py legal_documents/ --skip-existing

# Check what's already ingested
python scripts/ingest_legal_docs.py --check-only
```

**What happens:**
1. **OCR** - Gemini 2.0 Flash extracts Hebrew text (300 DPI, high quality)
2. **Chunking** - StatisticalChunker creates semantic chunks
3. **Embeddings** - multilingual-e5-large generates vectors
4. **Storage** - Chunks inserted into Supabase with HNSW index

**Expected time:** ~30 seconds per page (depends on API rate limits)

### 5. Ingest Exam Questions

Create a JSON file with your questions:

```json
[
  {
    "question": "מה ההגדרה של 'איש פנים'?",
    "options": {
      "A": "כל עובד בחברה",
      "B": "מי שיש לו מידע פנים",
      "C": "בעל מניות",
      "D": "דירקטור",
      "E": "אף אחד מהנ\"ל"
    },
    "correct_answer": "B",
    "explanation": "איש פנים הוא מי שמחזיק במידע פנים...",
    "topic": "מידע פנים",
    "difficulty": "medium",
    "legal_reference": "חוק ניירות ערך, סעיף 52(א)"
  }
]
```

Then ingest:

```bash
# Single file
python scripts/ingest_exam_questions.py questions.json

# Multiple files
python scripts/ingest_exam_questions.py examples/legal*.json

# Show database stats
python scripts/ingest_exam_questions.py --stats
```

**Output:**
```
✅ Inserted: 150 questions
📊 EXAM QUESTIONS DATABASE STATS
Total Questions: 150

By Topic:
   מידע פנים................................   45
   חובת גילוי...............................   30
   איסורי מניפולציה.........................   25
   ...
```

## 🤖 Using the Legal Expert Agent

### Simple Usage

Edit your question in the script:

```bash
python scripts/ask_question.py
```

**How to use:**
1. Open `scripts/ask_question.py`
2. Edit line 11:
   ```python
   question = "שאלה שלך כאן?"
   ```
3. Run: `python scripts/ask_question.py`
4. Get answer with citations!

### Features

✅ Formal, precise answers
✅ Legal citations (document + page)
✅ Based on 1,415 legal chunks
✅ Hebrew-optimized (Gemini 2.0 Flash)

---

## 📚 Using the RAG System

### Legal Documents RAG (RAG #1)

```python
from rag.legal_rag import LegalRAG

# Initialize
legal_rag = LegalRAG()

# Search for legal content
results = legal_rag.search("מה הם העונשים על שימוש במידע פנים?", k=5)

# Get formatted context for LLM
context = legal_rag.get_context(
    "מהי חובת הגילוי?",
    k=3,
    format='markdown'  # or 'text'
)

# Get legal reference with citations
reference = legal_rag.get_legal_reference("הגדרת איש פנים")
print(reference['context'])
print(reference['citations'])

# List available documents
docs = legal_rag.list_documents()
```

### Exam Questions RAG (RAG #2)

```python
from rag.exam_rag import ExamRAG

# Initialize
exam_rag = ExamRAG()

# Find questions on a specific concept
questions = exam_rag.find_questions_on_concept("מידע פנים", k=10)

# Get questions by topic
questions = exam_rag.get_questions_by_topic(
    topic="חובת גילוי",
    difficulty="medium",
    count=10
)

# Generate a random exam
exam = exam_rag.get_random_exam(count=25)

# Generate a balanced exam (equal distribution across topics)
exam = exam_rag.get_balanced_exam(count=25)

# Find similar questions
similar = exam_rag.get_questions_similar_to(question_id="uuid-here", k=5)

# Get topic statistics
stats = exam_rag.get_topic_statistics()
```

## 🧪 Testing

### Test OCR
```bash
python ingestion/ocr_utils.py legal1.pdf
```

### Test Semantic Chunking
```bash
python ingestion/semantic_chunking.py
```

### Test Legal RAG
```bash
python rag/legal_rag.py
```

### Test Exam RAG
```bash
python rag/exam_rag.py
```

### Test Vector Store
```bash
python rag/vector_store.py
```

## 📁 Project Structure

```
quiz/
├── config/
│   └── settings.py              # Environment config
│
├── ingestion/
│   ├── ocr_utils.py             # PDF → Markdown (Gemini OCR)
│   └── semantic_chunking.py     # Semantic chunking
│
├── rag/
│   ├── vector_store.py          # Supabase vector operations
│   ├── legal_rag.py             # Legal documents RAG
│   └── exam_rag.py              # Exam questions RAG
│
├── agents/                       # LangChain agents (coming next)
│   ├── legal_expert.py
│   ├── question_analyzer.py
│   ├── explanation_generator.py
│   └── ...
│
├── api/                          # FastAPI endpoints (coming next)
│   └── main.py
│
├── scripts/
│   ├── setup_supabase.py        # Database schema setup
│   ├── ingest_legal_docs.py     # Ingest legal PDFs
│   └── ingest_exam_questions.py # Ingest exam questions
│
├── .env                          # Environment variables
├── requirements.txt
└── README.md
```

## 🔧 Configuration

All configuration in `config/settings.py`:

```python
# Embeddings
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_DIMENSION = 1024

# RAG
RAG_TOP_K = 5  # Number of chunks to retrieve
RAG_SCORE_THRESHOLD = 0.7  # Minimum similarity

# OCR
OCR_DPI = 300  # High quality for Hebrew
OCR_MAX_PAGES = None  # None = process all
OCR_RATE_LIMIT_DELAY = 0.5  # seconds

# Chunking
CHUNK_METHOD = "statistical"  # StatisticalChunker

# Performance
MASTERY_THRESHOLD = 0.8  # 80% = mastery
CONSECUTIVE_CORRECT_TO_REMOVE = 2
SPACED_REPETITION_MIN_HOURS = 24

# Exam
EXAM_QUESTION_COUNT = 25
MIN_QUESTIONS_PER_TOPIC = 2
```

## 🚦 Next Steps

### Phase 1: Core Infrastructure ✅ (COMPLETE)
- [x] Supabase schema setup
- [x] OCR pipeline (Gemini 2.0 Flash)
- [x] Semantic chunking (StatisticalChunker)
- [x] Legal documents RAG
- [x] Exam questions RAG
- [x] Vector store operations

### Phase 2: LangChain Agents (Next)
- [ ] Agent base class
- [ ] Legal Expert Agent
- [ ] Question Analyzer Agent
- [ ] Explanation Generator Agent
- [ ] Performance Tracker Agent
- [ ] Question Selector Agent
- [ ] Chat Mentor Agent
- [ ] Content Generator Agent
- [ ] Analytics Agent

### Phase 3: FastAPI Backend
- [ ] User authentication
- [ ] API endpoints for all agents
- [ ] WebSocket for real-time chat
- [ ] Rate limiting

### Phase 4: AWS Parallel Processing
- [ ] S3 + Lambda trigger
- [ ] AWS Batch for parallel OCR
- [ ] SQS queue management

## 🐛 Troubleshooting

### "pgvector extension not found"
Enable it in Supabase dashboard: Database → Extensions → vector

### "Poppler not found"
Install poppler: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)

### "Rate limit exceeded"
Increase `OCR_RATE_LIMIT_DELAY` in settings.py

### "Out of memory during chunking"
Process documents in smaller batches or reduce `--max-pages`

### "Embedding dimension mismatch"
Verify `EMBEDDING_MODEL` matches your Supabase schema (default: 1024 for multilingual-e5-large)

## 📖 Documentation

- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [LangChain](https://python.langchain.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [semantic-chunkers](https://github.com/aurelio-labs/semantic-chunkers)
- [sentence-transformers](https://www.sbert.net/)

## 🤝 Contributing

1. Test your changes thoroughly
2. Update documentation
3. Follow existing code style
4. Add tests for new features

## 📄 License

MIT License

---

**Built with ❤️ for Israeli Securities Authority exam preparation**
