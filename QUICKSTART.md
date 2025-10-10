# 🚀 Quick Start Guide

## ✅ Phase 1 Complete: RAG Infrastructure

You now have a **production-ready dual RAG system** with:

1. ✅ **Supabase database** - Schema setup complete
2. ✅ **Legal Documents RAG** - OCR + Semantic chunking + Vector search
3. ✅ **Exam Questions RAG** - Question storage + Similarity search
4. ✅ **Ingestion pipelines** - Ready to process PDFs and questions

---

## 🎯 Next Immediate Steps

### Step 1: Install Dependencies (5 minutes)

```bash
cd /Users/adialia/Desktop/quiz

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install all packages
pip install -r requirements.txt
```

### Step 2: Enable pgvector in Supabase (2 minutes)

1. Go to https://supabase.com/dashboard
2. Select your project: `omgykoftsrtyipmykamk`
3. Click **Database** → **Extensions**
4. Search for `vector`
5. Click **Enable** next to "vector"

### Step 3: Setup Database Schema (2 minutes)

**Option A: Supabase SQL Editor (Recommended)**

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click **SQL Editor** in left menu
4. Click **New Query**
5. Open `scripts/schema.sql` and copy all contents
6. Paste into SQL Editor
7. Click **Run** (or press Cmd+Enter)

You should see: `Success. No rows returned`

**Option B: Verify Setup via Python**

```bash
python scripts/setup_supabase_simple.py
```

**Expected output:**
```
✅ Configuration valid
✅ Connected to Supabase

Checking tables...
✅ legal_doc_chunks
✅ exam_questions
✅ users
✅ user_performance
✅ chat_messages
✅ study_sessions
✅ topic_mastery

🎉 All tables exist! Setup is complete.
```

### Step 4: Ingest Legal Documents

You have **16 PDFs** in `legal_documents/` ready to ingest!

**Option A: Test with one document first** (Recommended)

```bash
# Test with 5 pages from one PDF
python scripts/ingest_legal_docs.py legal_documents/1193856b-495b-4ce3-b796-33e7548e739c.pdf --max-pages 5
```

**Option B: Ingest ALL documents** (Takes ~30 min for 16 PDFs)

```bash
# Ingest all PDFs in legal_documents folder
python scripts/ingest_all_legal_docs.py

# Or skip already processed documents
python scripts/ingest_all_legal_docs.py --skip-existing
```

**Option C: Bash script** (same as Option B)

```bash
chmod +x scripts/ingest_all_legal_docs.sh
./scripts/ingest_all_legal_docs.sh
```

**What happens:**
- OCR extracts text from PDF (~10-20 sec/page)
- Creates semantic chunks
- Generates embeddings
- Stores in Supabase

**Expected output:**
```
🔄 Converting PDF to images (300 DPI)...
✅ Processing 5 pages with Gemini 2.0 Flash...
   Page 1/5... ✅
   Page 2/5... ✅
   ...
✅ OCR Complete: 5 pages, 12,450 chars

📊 Chunking document...
✅ Created 23 chunks

🔄 Generating embeddings...
✅ Embeddings generated

[4/4] Inserting into Supabase...
✅ Successfully inserted 23 chunks
```

### Step 5: Test Legal RAG

```bash
python rag/legal_rag.py
```

This will:
- Connect to your vector database
- Run test queries in Hebrew
- Show you the search results

### Step 6: Prepare Exam Questions

Create a JSON file: `questions.json`

```json
[
  {
    "question": "מה ההגדרה של 'איש פנים' לפי חוק ניירות ערך?",
    "options": {
      "A": "כל עובד בחברה ציבורית",
      "B": "מי שמחזיק במידע פנים",
      "C": "בעל מניות בעל שליטה",
      "D": "חבר דירקטוריון בלבד",
      "E": "כל הנ\"ל"
    },
    "correct_answer": "B",
    "explanation": "איש פנים מוגדר כמי שמחזיק במידע פנים בשל תפקידו, מעמדו או קשריו עם התאגיד.",
    "topic": "מידע פנים",
    "difficulty": "medium",
    "legal_reference": "חוק ניירות ערך, התשכ\"ח-1968, סעיף 52(א)"
  },
  {
    "question": "מהו העונש על שימוש במידע פנים?",
    "options": {
      "A": "קנס בלבד",
      "B": "מאסר עד 5 שנים",
      "C": "מאסר עד 5 שנים או קנס פי 10 מהרווח",
      "D": "השעיה מהמסחר",
      "E": "אזהרה בכתב"
    },
    "correct_answer": "C",
    "explanation": "העונש על שימוש במידע פנים כולל מאסר של עד 5 שנים או קנס של עד פי 10 מהרווח שנצבר או ההפסד שנמנע.",
    "topic": "מידע פנים",
    "difficulty": "hard",
    "legal_reference": "חוק ניירות ערך, התשכ\"ח-1968, סעיף 53"
  }
]
```

### Step 7: Ingest Exam Questions

```bash
python scripts/ingest_exam_questions.py questions.json
```

**Expected output:**
```
📄 Loading questions from: questions.json
✅ Loaded 2 questions

🔄 Processing 2 questions
✅ Embeddings generated

🔄 Inserting into Supabase...
✅ Successfully inserted 2 questions

📊 EXAM QUESTIONS DATABASE STATS
Total Questions: 2

By Topic:
   מידע פנים................................    2
```

### Step 8: Test Exam RAG

```bash
python rag/exam_rag.py
```

---

## 🎉 You're Ready!

You now have:
- ✅ Dual RAG system working
- ✅ Legal documents indexed and searchable
- ✅ Exam questions indexed
- ✅ Semantic search operational

---

## 📊 What You Can Do Now

### Search Legal Documents
```python
from rag.legal_rag import LegalRAG

rag = LegalRAG()
results = rag.search("מהם העונשים על מידע פנים?", k=5)
```

### Find Similar Questions
```python
from rag.exam_rag import ExamRAG

rag = ExamRAG()
questions = rag.find_questions_on_concept("מידע פנים", k=10)
```

### Generate Practice Exams
```python
exam = rag.get_balanced_exam(count=25)  # Balanced across all topics
```

---

## 🚀 Next Phase: LangChain Agents

Now that RAG infrastructure is ready, you can:

1. **Build LangChain Agents** (see PRD.MD for all 8 agents)
   - Legal Expert Agent (uses Legal RAG)
   - Question Analyzer Agent (uses Exam RAG)
   - Explanation Generator Agent (uses both)
   - etc.

2. **Create FastAPI Backend**
   - REST API endpoints
   - WebSocket for chat
   - User authentication

3. **AWS Parallel Processing**
   - Batch process 50+ documents at once
   - S3 + Lambda + Batch setup

---

## 💡 Pro Tips

### Batch Ingestion
```bash
# Ingest all PDFs in a folder
python scripts/ingest_legal_docs.py legal_documents/*.pdf

# Skip already processed
python scripts/ingest_legal_docs.py legal_documents/ --skip-existing

# Check what's in database
python scripts/ingest_legal_docs.py --check-only
```

### View Database Stats
```bash
# Exam questions stats
python scripts/ingest_exam_questions.py --stats

# Legal docs count
python rag/vector_store.py
```

### Test Individual Components
```bash
# Test OCR only
python ingestion/ocr_utils.py legal1.pdf 5

# Test chunking only
python ingestion/semantic_chunking.py
```

---

## 🐛 Common Issues

### "Module not found"
```bash
pip install -r requirements.txt
```

### "pgvector not enabled"
Enable it in Supabase dashboard → Database → Extensions → vector

### "Rate limit exceeded"
Edit `config/settings.py`:
```python
OCR_RATE_LIMIT_DELAY = 1.0  # Increase delay
```

### "Out of memory"
Process fewer pages:
```bash
python scripts/ingest_legal_docs.py file.pdf --max-pages 10
```

---

## 📞 Questions?

Check:
1. `README.md` - Full documentation
2. `PRD.MD` - Product requirements and agent specs
3. Each script has `--help` flag

---

**You've completed Phase 1! Ready to build the agents? 🚀**
