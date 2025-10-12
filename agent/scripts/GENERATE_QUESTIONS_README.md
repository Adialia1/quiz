# AI Question Generation Script

This script generates 500 AI questions covering all syllabus topics and stores them in the `ai_generated_questions` database table.

## Overview

- **Total Questions:** 500
- **Topics Covered:** 18 topics from the syllabus
- **Questions per Topic:** ~27-28 questions
- **Difficulty Distribution:**
  - 40% Easy
  - 40% Medium
  - 20% Hard

## Topics Covered

### Part A - דיני ניירות ערך (Securities Law)

1. מבוא ודיני יסוד (Introduction and Foundations)
2. חוק ניירות ערך - הגדרות (Securities Law - Definitions)
3. חוק ניירות ערך - חובות גילוי (Securities Law - Disclosure)
4. חוק ניירות ערך - עבירות (Securities Law - Offenses)
5. חוק השקעות משותפות בנאמנות (Mutual Funds Law)
6. דיני חברות רלוונטיים (Relevant Corporate Law)
7. אחריות משפטית (Legal Liability)
8. חוק איסור הלבנת הון (Anti-Money Laundering)
9. רגולציה נוספת ושינויים (Additional Regulations)

### Part B - אתיקה מקצועית (Professional Ethics)

10. עקרונות אתיים כלליים (General Ethical Principles)
11. הקוד האתי לשוק ההון (Ethical Code)
12. שירות הוגן ללקוחות (Fair Service to Clients)
13. הבחנה בין ייעוץ לשיווק (Advice vs Marketing)
14. חובת הנאמנות (Fiduciary Duty)
15. אי־תלות של היועץ (Advisor Independence)
16. חובות גילוי ללקוח (Disclosure to Client)
17. התנהגות שאינה הולמת (Misconduct)
18. סטנדרטים אתיים (Professional Standards)

## How It Works

### 1. Question Generation

The script uses `QuizGeneratorAgent` which:
- Uses Gemini 2.5 Pro (thinking model) for question generation
- Retrieves context from Legal RAG (legal documents)
- Retrieves reference questions from Exam RAG
- Validates questions with Legal Expert Agent
- Ensures all questions have exactly 5 options (A-E)

### 2. Quality Validation

Each question goes through:
1. **Structural Validation** - Must have all required fields and 5 options
2. **Legal Expert Validation** - Expert agent must answer correctly
3. **Confidence Check** - Expert must be confident in the answer

Only questions that pass all validations are inserted into the database.

### 3. Database Storage

Questions are stored in `ai_generated_questions` table with:
- Question text and 5 options (A-E)
- Correct answer and explanation
- Topic, difficulty, legal reference
- Expert validation metadata
- Quality tracking fields (initialized to 0)

## Prerequisites

1. **Database Setup:**
   ```bash
   # Run migrations first
   # See agent/scripts/migrations/README.md
   ```

2. **Environment Variables:**
   ```bash
   # Make sure .env has:
   OPENROUTER_API_KEY=sk-or-v1-...
   SUPABASE_URL=https://....supabase.co
   SUPABASE_SERVICE_KEY=eyJhbGci...
   ```

3. **Python Dependencies:**
   ```bash
   # Already installed if you ran:
   pip install -r requirements.txt
   ```

## Usage

### Run the Script

```bash
cd /Users/adialia/Desktop/quiz
python agent/scripts/generate_initial_questions.py
```

### Expected Output

```
================================================================================
🚀 AI Question Generation - Initial Dataset
================================================================================
Target: 500 questions
Topics: 18
Questions per topic: ~27
Difficulty distribution: 40% easy, 40% medium, 20% hard
================================================================================

🔧 Initializing...
✅ Initialization complete

📚 Topic 1/18: מבוא ודיני יסוד
--------------------------------------------------------------------------------
  🔧 Generating 11 easy questions for: מבוא ודיני יסוד
     ✅ Generated 11 questions (validation passed)
     💾 Inserted 11/11 easy questions
  🔧 Generating 11 medium questions for: מבוא ודיני יסוד
     ✅ Generated 11 questions (validation passed)
     💾 Inserted 11/11 medium questions
  🔧 Generating 5 hard questions for: מבוא ודיני יסוד
     ✅ Generated 5 questions (validation passed)
     💾 Inserted 5/5 hard questions
  ✅ Topic complete: 27 questions inserted

... (continues for all topics)

================================================================================
📊 GENERATION COMPLETE
================================================================================
Total Generated: 500
Total Inserted: 500
Failed: 0

By Difficulty:
  Easy:   200
  Medium: 200
  Hard:   100

By Topic:
  מבוא ודיני יסוד: 27 (11E, 11M, 5H)
  ...

📄 Stats saved to: generation_stats_20251012_005530.json
✅ All done!
```

## Time Estimate

- **Per Question:** ~5-10 seconds (includes generation + validation)
- **Total Time:** ~45-90 minutes for 500 questions

Why so long?
- Each question is validated by Legal Expert Agent
- Uses RAG retrieval (2 systems: Legal RAG + Exam RAG)
- Generates 2x questions per batch (due to validation rejections)
- Uses thinking model (slower but higher quality)

## Output

### 1. Database

All questions stored in `ai_generated_questions` table in Supabase.

### 2. Stats File

A JSON file with generation statistics:
```json
{
  "total_generated": 500,
  "total_inserted": 500,
  "by_difficulty": {
    "easy": 200,
    "medium": 200,
    "hard": 100
  },
  "by_topic": {
    "מבוא ודיני יסוד": {
      "easy": 11,
      "medium": 11,
      "hard": 5
    },
    ...
  }
}
```

## Troubleshooting

### Error: "Missing Supabase credentials"

**Fix:** Check `.env` file has `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

### Error: "relation 'ai_generated_questions' does not exist"

**Fix:** Run migrations first:
```bash
# See agent/scripts/migrations/README.md
```

### Questions failing validation

This is **normal**. The Legal Expert Agent is strict. The script requests 2x questions per batch to account for validation rejections.

If too many fail (>50%), check:
- Legal RAG is populated with documents
- Exam RAG has reference questions
- Legal Expert Agent is working

### Script is slow

This is **expected**. Quality > Speed. Each question:
1. Retrieves 20 legal chunks
2. Retrieves 15 reference questions
3. Generates with thinking model
4. Validates with Legal Expert
5. Inserts into database

To speed up (not recommended):
- Reduce validation (lower quality)
- Use faster model (lower quality)
- Skip expert validation (risky)

## Next Steps

After generating questions:

1. **Verify in Database:**
   ```sql
   SELECT topic, difficulty_level, COUNT(*)
   FROM ai_generated_questions
   GROUP BY topic, difficulty_level
   ORDER BY topic, difficulty_level;
   ```

2. **Check Quality:**
   ```sql
   SELECT * FROM ai_generated_questions
   WHERE expert_validated = true
   LIMIT 10;
   ```

3. **Build API Endpoints:**
   - See `BACKEND_ARCHITECTURE.md` for API design
   - Implement exam creation endpoints
   - Implement adaptive question selection

4. **Test in App:**
   - Start practice mode
   - Verify questions display correctly
   - Test answer submission

## Notes

- Questions are validated by Legal Expert, so they should be accurate
- All questions have exactly 5 options (A-E) as required
- Questions include explanations and legal references
- Expert validation metadata is stored for quality tracking
- Questions are marked as `is_active = true` by default

## Support

If you encounter issues:
1. Check the error message
2. Verify environment variables
3. Check database migrations
4. Verify RAG systems are populated
5. Review generation stats file
