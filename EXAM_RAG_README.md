# Exam Questions RAG System

## Overview

A comprehensive Retrieval-Augmented Generation (RAG) system for managing, searching, and generating exam questions from PDF documents. The system parses exam PDFs, extracts questions with their options and correct answers, creates semantic embeddings, and provides intelligent search and exam generation capabilities.

## Key Features

### 1. **PDF Parsing**
- Automatically extracts questions from exam PDFs
- Handles both Hebrew and English formats
- Detects questions with 5 options (A-E)
- Extracts answer keys from tables at the end of PDFs
- Validates question completeness and structure

### 2. **Intelligent Embedding Strategy**
- Combines question text with all options for comprehensive semantic understanding
- Uses HuggingFace embeddings (1024 dimensions)
- Enables concept-based similarity search
- Maintains semantic relationships between related questions

### 3. **Advanced Search Capabilities**
- Search by concept or topic
- Find similar questions
- Filter by difficulty level
- Retrieve questions testing specific legal concepts

### 4. **Exam Generation**
- Generate random exams with specified question count
- Create balanced exams across topics
- Topic-specific exam generation
- Export exams in multiple formats (JSON, Markdown, Text)

## Architecture

```
┌─────────────────┐     ┌────────────────┐     ┌─────────────────┐
│   Exam PDFs     │────▶│  ExamParser    │────▶│   Embeddings    │
└─────────────────┘     └────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌────────────────┐     ┌─────────────────┐
│  Query Interface│◀────│   ExamRAG      │◀────│   Supabase DB   │
└─────────────────┘     └────────────────┘     └─────────────────┘
```

## Components

### 1. **ExamParser** (`ingestion/exam_parser.py`)
- OCR-based PDF processing using Gemini 2.0
- Pattern recognition for questions and options
- Answer key extraction
- Validation and formatting

### 2. **ExamRAG** (`rag/exam_rag.py`)
- Semantic search interface
- Topic and difficulty filtering
- Exam generation logic
- Question formatting

### 3. **Ingestion Pipeline** (`scripts/ingest_exam_questions.py`)
- Batch processing of PDFs
- Embedding generation
- Database insertion
- Progress tracking

### 4. **Query Interface** (`scripts/query_exam_rag.py`)
- Interactive search
- Exam generation
- Export functionality
- Statistics display

## Database Schema

```sql
exam_questions
├── id (UUID)
├── question_text (TEXT)
├── option_a...option_e (TEXT)
├── correct_answer (CHAR)
├── explanation (TEXT)
├── topic (TEXT)
├── difficulty (TEXT)
├── legal_reference (TEXT)
├── embedding (VECTOR[1024])
└── metadata (JSONB)
```

## Usage

### 1. Ingesting Exam PDFs

```bash
# Single PDF file
python scripts/ingest_exam_questions.py exam.pdf \
    --type pdf \
    --topic "Securities Law" \
    --difficulty medium

# Directory of PDFs
python scripts/ingest_exam_questions.py exam_pdfs/ \
    --type pdf \
    --topic "Legal Ethics"

# Dry run (parse without inserting)
python scripts/ingest_exam_questions.py exam.pdf \
    --type pdf \
    --dry-run

# Show statistics
python scripts/ingest_exam_questions.py --stats
```

### 2. Querying Questions

```bash
# Search by concept
python scripts/query_exam_rag.py search "מידע פנים" -k 10

# Generate exam
python scripts/query_exam_rag.py exam \
    --count 30 \
    --topic "Securities Law" \
    --output exam.json

# Interactive mode
python scripts/query_exam_rag.py interactive

# Show statistics
python scripts/query_exam_rag.py stats
```

### 3. Python API Usage

```python
from rag.exam_rag import ExamRAG

# Initialize
rag = ExamRAG()

# Search for questions
questions = rag.find_questions_on_concept("insider trading", k=5)

# Generate balanced exam
exam = rag.get_balanced_exam(count=25)

# Get questions by topic
topic_questions = rag.get_questions_by_topic(
    topic="Securities Law",
    difficulty="hard",
    count=10
)
```

## Embedding Strategy Deep Dive

### Why Combine Question + Options?

The embedding strategy concatenates the question text with all five options (A-E) before generating the embedding vector. This approach provides several advantages:

1. **Semantic Completeness**: The full context of what the question is testing is captured
2. **Better Similarity Matching**: Questions with similar concepts but different phrasings are matched
3. **Option-Based Retrieval**: Can find questions with similar answer choices
4. **Concept Coverage**: Captures the breadth of the topic being tested

### Example Embedding Text

```
Question: "What is insider trading?"
Options: A, B, C, D, E
➜ Embedding text: "What is insider trading? | Illegal trading based on material nonpublic information | Trading during market hours | Buying company stock | Selling securities | None of the above"
```

## PDF Format Requirements

The system expects exam PDFs in the following format:

1. **Questions**: Numbered sequentially (1, 2, 3...)
2. **Options**: Five options labeled A-E (or א-ה in Hebrew)
3. **Answer Key**: Table at the end with question numbers and correct answers

### Example PDF Structure

```
1. What is the definition of insider information?
   A. Public information
   B. Material nonpublic information
   C. Company reports
   D. Market rumors
   E. None of the above

2. Who is considered an insider?
   ...

[End of exam]

Answer Key:
1. B
2. D
...
```

## Performance Optimization

### Batch Processing
- Process multiple PDFs in parallel
- Batch database insertions (50 questions per batch)
- Efficient embedding generation

### Caching
- Vector embeddings are stored once and reused
- Similarity search uses HNSW indexes for fast retrieval
- Topic and difficulty indexes for quick filtering

### Rate Limiting
- OCR requests are rate-limited to avoid API throttling
- Configurable delays between API calls

## Error Handling

### Validation
- Each question must have at least 4 options
- Correct answer must match one of the options
- Question text is required
- Invalid questions are logged but don't stop processing

### Recovery
- Failed OCR pages are skipped with logging
- Partial answer keys are handled gracefully
- Database insertion failures are reported per batch

## Configuration

Key settings in `config/settings.py`:

```python
EMBEDDING_MODEL = "Alibaba-NLP/gte-large-en-v1.5"
RAG_TOP_K = 5
EXAM_QUESTION_COUNT = 25
OCR_MAX_PAGES = None  # Process all pages
OCR_DPI = 200
```

## Troubleshooting

### Common Issues

1. **No questions extracted from PDF**
   - Check PDF format matches expected structure
   - Verify OCR is working (test with `--dry-run`)
   - Review validation report for specific issues

2. **Low similarity scores**
   - Ensure questions have complete text and options
   - Check embedding model is loaded correctly
   - Verify database indexes are created

3. **Slow processing**
   - Reduce OCR DPI for faster processing
   - Process PDFs in smaller batches
   - Check rate limiting settings

## Future Enhancements

1. **Multi-language Support**: Enhanced support for mixed Hebrew/English content
2. **Advanced Analytics**: Question difficulty analysis based on user performance
3. **Smart Exam Generation**: ML-based exam composition for optimal difficulty curves
4. **Question Versioning**: Track changes and updates to questions over time
5. **Collaborative Features**: Allow multiple users to contribute and validate questions

## Dependencies

- `pdf2image`: PDF to image conversion
- `openai`: Gemini OCR via OpenRouter
- `semantic-router`: Embedding generation
- `supabase`: Vector database
- `rich`: Terminal UI
- `pathlib`: File operations

## License

[Your License Here]

## Support

For issues or questions, please contact [your contact info]