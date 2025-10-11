# Exam Question Validation System

## Overview

A two-stage validation system that ensures extracted exam questions are accurate and properly matched with their correct answers. This addresses the critical issue of option-answer mismatches in PDF parsing.

## The Problem

When parsing exam PDFs, several issues can occur:
- **OCR Errors**: Misread text leading to incorrect options
- **Answer Key Misalignment**: Question numbers not matching between questions and answer key
- **Multi-line Options**: Options spanning multiple lines being split incorrectly
- **Option Order Confusion**: Options extracted in wrong order
- **Answer Letter Misreading**: Correct answer misidentified (e.g., B read as D)

## Solution: Two-Stage Validation

### Stage 1: Basic Structural Validation
Fast, rule-based validation checking:
- ✅ Question has text
- ✅ Exactly 5 options (A-E) present
- ✅ All options are non-empty
- ✅ Correct answer is one of A-E
- ✅ Correct answer maps to an existing option

### Stage 2: LLM Validation
AI-powered semantic validation checking:
- ✅ Question is clearly worded
- ✅ Options are complete and make sense
- ✅ Correct answer is logically valid
- ✅ No mismatch between options and answer
- ✅ Question tests a coherent concept

## Architecture

```
┌─────────────┐
│  PDF Input  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   OCR Parser    │  ← Extract questions, options, answers
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Stage 1:       │
│  Basic Check    │  ← Structural validation
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Stage 2:       │
│  LLM Validate   │  ← Semantic validation with Gemini
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Validated Q's   │  ← Only questions that pass both stages
└─────────────────┘
```

## Usage

### 1. Automatic Validation (Recommended)

```bash
# Parse with full validation (default)
python scripts/ingest_exam_questions.py exam.pdf \
    --type pdf \
    --topic "Legal Ethics"

# This will:
# 1. Extract all questions
# 2. Run basic validation
# 3. Run LLM validation on passing questions
# 4. Insert only validated questions to database
```

### 2. Skip LLM Validation (Faster, Less Accurate)

```bash
# Skip LLM validation for speed
python scripts/ingest_exam_questions.py exam.pdf \
    --type pdf \
    --no-llm-validation

# Use this when:
# - Testing/debugging
# - PDF quality is known to be high
# - Speed is critical
```

### 3. Dry Run with Validation Report

```bash
# See validation results without inserting to database
python scripts/ingest_exam_questions.py exam.pdf \
    --type pdf \
    --dry-run

# Output will show:
# - Total extracted: X questions
# - Basic valid: Y questions
# - LLM validated: Z questions
# - Success rate: Z/X %
```

### 4. Interactive Review Tool

For problematic PDFs with known issues:

```bash
# Review and fix issues interactively
python scripts/review_exam_issues.py exam.pdf

# This opens an interactive interface to:
# - Review each problematic question
# - See specific validation issues
# - Edit questions manually
# - Delete invalid questions
# - Export corrected questions
```

## Validation Output

### Validation Report Structure

```json
{
  "total_extracted": 50,
  "basic_valid": 48,
  "llm_valid": 45,
  "final_valid": 45,
  "invalid_questions": 2,
  "llm_rejected": 3,
  "success_rate": 0.9,
  "basic_invalid_details": [
    {
      "question_number": 23,
      "reason": "Missing option E",
      "option_count": 4
    }
  ],
  "llm_issues": [
    {
      "question_number": 15,
      "issues": ["Option B text seems incomplete"],
      "confidence": 0.65
    }
  ]
}
```

### Per-Question Validation Data

Each validated question includes:

```json
{
  "question_text": "...",
  "options": { "A": "...", "B": "...", ... },
  "correct_answer": "B",
  "validation": {
    "valid": true,
    "confidence": 0.95,
    "issues": [],
    "correct_answer_valid": true
  }
}
```

## LLM Validation Logic

The validator uses Gemini 2.0 Flash to check each question:

### Input to LLM
```
**Question:** What is insider trading?

**A.** Legal trading based on public information
**B.** Illegal trading based on material nonpublic information
**C.** Any stock market trading
**D.** Trading during market hours
**E.** None of the above

**Correct Answer:** B

Check if this question is valid and the answer matches correctly.
```

### Output from LLM
```json
{
  "valid": true,
  "issues": [],
  "confidence": 0.95,
  "correct_answer_valid": true
}
```

### Rejection Criteria

A question is rejected if:
- `valid: false`
- `confidence < 0.7`
- `correct_answer_valid: false`
- Critical issues detected

## Common Issues Detected

### 1. Option-Answer Mismatch
**Issue:** Correct answer references wrong option
```
Question: "What is X?"
A. Definition of Y
B. Definition of Z
C. Definition of X  ← Actually correct
Correct Answer: A  ← Marked as A but should be C
```

**Detection:** LLM reads question and all options, determines C is correct, flags mismatch with marked answer A

### 2. Incomplete Options
**Issue:** Multi-line option split incorrectly
```
Question: "Which statement is correct?"
A. The definition of insider trading is
B. any use of material information
C. Complete option text
```

**Detection:** LLM identifies option A is incomplete sentence, flags as issue

### 3. Answer Key Misalignment
**Issue:** Question numbers don't match answer key
```
Questions: 1, 2, 3, 4, 5
Answer Key: 1→A, 3→B, 4→C  (missing 2, 5)
```

**Detection:** Basic validation catches missing answers, LLM can't verify correctness

### 4. OCR Misreading
**Issue:** Character confusion (B vs D, א vs ה)
```
Actual:  Answer is B
OCR read: Answer is D
```

**Detection:** LLM evaluates if marked answer makes logical sense

## Best Practices

### 1. Always Use Validation for Production
```bash
# ✅ Good - Full validation
python scripts/ingest_exam_questions.py exam.pdf --type pdf

# ❌ Bad - No validation
python scripts/ingest_exam_questions.py exam.pdf --type pdf --no-llm-validation
```

### 2. Review Validation Reports
Check the success rate:
- **> 90%**: Good quality PDF, proceed
- **70-90%**: Review issues, may need manual fixes
- **< 70%**: PDF quality issues, use review tool

### 3. Test with Dry Run First
```bash
# Test parsing before inserting
python scripts/ingest_exam_questions.py exam.pdf --type pdf --dry-run

# Review the report, then run actual ingestion if acceptable
python scripts/ingest_exam_questions.py exam.pdf --type pdf
```

### 4. Use Review Tool for Problem PDFs
```bash
# Interactive review and correction
python scripts/review_exam_issues.py problematic_exam.pdf

# Exports: validated_questions.json
# Then ingest the corrected JSON:
python scripts/ingest_exam_questions.py validated_questions.json --type json
```

## Performance Considerations

### Speed vs Accuracy Trade-off

| Mode | Speed | Accuracy | Use Case |
|------|-------|----------|----------|
| No validation | Fast | Low | Testing only |
| Basic validation | Medium | Medium | High-quality PDFs |
| Full LLM validation | Slow | High | Production (recommended) |

### Processing Time Examples

For a 50-question exam:
- **No validation**: ~2 minutes
- **Basic validation**: ~2.5 minutes
- **Full LLM validation**: ~8-10 minutes

### Cost Considerations

LLM validation uses API calls:
- ~1 call per question
- 50 questions ≈ 50 API calls
- Cost: ~$0.10 per exam (at current Gemini rates)

## Troubleshooting

### High Rejection Rate

**Problem:** Many questions rejected by LLM

**Solutions:**
1. Check PDF quality - is text clear?
2. Review OCR settings (DPI, language)
3. Use review tool to inspect specific issues
4. Consider manual correction for small batches

### False Positives

**Problem:** Valid questions being rejected

**Solutions:**
1. Check confidence threshold (currently 0.7)
2. Review LLM prompt for language-specific issues
3. Adjust validation criteria in `exam_validator.py`

### Performance Issues

**Problem:** Validation too slow

**Solutions:**
1. Process in smaller batches
2. Use `--no-llm-validation` for testing
3. Increase API rate limits
4. Cache validation results

## Configuration

Key settings in `config/settings.py`:

```python
# Validation settings
VALIDATION_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence
VALIDATION_ENABLED_BY_DEFAULT = True   # Auto-validate

# LLM settings for validation
GEMINI_MODEL = "google/gemini-2.0-flash-exp:free"
GEMINI_TEMPERATURE = 0.1  # Low for consistent validation
```

## Advanced: Deep Validation

For critical exams, use deep validation (re-reads from PDF):

```python
from ingestion.exam_validator import ExamQuestionValidator
from ingestion.ocr_utils import GeminiOCR

validator = ExamQuestionValidator()
ocr = GeminiOCR()

# Get PDF page as image
import base64
from pdf2image import convert_from_path

images = convert_from_path("exam.pdf")
page_image_base64 = base64.b64encode(images[0]).decode()

# Deep validate specific question
result = validator.deep_validate_with_reread(
    question=extracted_question,
    pdf_page_image_base64=page_image_base64
)

# Compare original extraction with re-read
if not result['comparison']['match']:
    print("Mismatch detected!")
    print(result['comparison']['issues'])
```

## Summary

The validation system provides:
- ✅ **Accuracy**: Catches option-answer mismatches
- ✅ **Reliability**: Two-stage validation ensures quality
- ✅ **Transparency**: Detailed reports show what was rejected and why
- ✅ **Flexibility**: Can skip for speed or use full validation for accuracy
- ✅ **Interactivity**: Review tool for manual correction

**Recommendation:** Always use full LLM validation for production ingestion to ensure exam question quality.