# Database Migrations

This folder contains SQL migrations to set up the quiz app database schema.

## Quick Start

### Option 1: Run All Migrations at Once (Recommended)

1. Open Supabase Dashboard → SQL Editor
2. Create a new query
3. Copy the contents of `run_all_migrations.sql`
4. Click "Run"

This will:
- Drop old tables: `users`, `user_performance`, `chat_messages`, `study_sessions`, `topic_mastery`
- Create new tables with the complete schema
- Set up all indexes, triggers, and functions

**Note:** Tables `legal_doc_chunks` and `exam_questions` are NOT touched (they are RAG tables).

---

### Option 2: Run Individual Migrations

Run each migration file in order:

```
001_drop_old_tables.sql
002_create_users_table.sql
003_create_ai_generated_questions.sql
004_create_exams_table.sql
005_create_exam_question_answers.sql
006_create_user_question_history.sql
007_create_user_topic_performance.sql
008_create_user_mistakes.sql
009_create_ai_chat_tables.sql
```

---

## New Schema Overview

### Core Tables

1. **users** - User profiles synced from Clerk
   - `clerk_user_id` - Link to Clerk authentication
   - Subscription status, preferences, aggregate stats

2. **ai_generated_questions** - Pre-generated question pool
   - Matches `quiz_generator.py` output format
   - 5 options (A-E), quality tracking, expert validation
   - Different from `exam_questions` (RAG table)

3. **exams** - Exam sessions
   - Types: `practice`, `full_simulation`, `review_mistakes`
   - Status tracking, results, topics covered

4. **exam_question_answers** - User answers to questions
   - Junction table linking exams to questions
   - Answer tracking, timing, review flags

### Analytics Tables

5. **user_question_history** - Per-question performance
   - Times seen/correct/wrong
   - Mastery level (auto-calculated)

6. **user_topic_performance** - Per-topic performance
   - Accuracy by topic
   - Strength level (weak/average/strong)

7. **user_mistakes** - Wrong answers tracker
   - Powers "חזרה על טעויות" feature
   - Review status tracking

### AI Instructor Tables

8. **ai_chat_sessions** - Chat sessions
9. **ai_chat_messages** - Chat messages

---

## Auto-Calculated Fields

### Mastery Level (user_question_history)

Automatically calculated based on performance:
- `not_seen` - Never answered
- `learning` - < 50% accuracy
- `practicing` - 50-80% accuracy
- `mastered` - > 80% accuracy

### Strength Level (user_topic_performance)

Automatically calculated from accuracy:
- `weak` - < 70%
- `average` - 70-90%
- `strong` - > 90%

### Accuracy Percentage (user_topic_performance)

Automatically calculated: `(correct_answers / total_questions) * 100`

---

## Important Notes

### Table Name Changes

- `exam_questions` → **RAG table (DON'T TOUCH)**
- `ai_generated_questions` → **New table for user-facing questions**
- `exam_question_answers` → **Junction table (renamed to avoid conflict)**

### Removed Tables

These old tables are dropped:
- `users` (old structure)
- `user_performance`
- `chat_messages`
- `study_sessions`
- `topic_mastery`

### Preserved Tables

These tables are **NOT touched**:
- `legal_doc_chunks` - RAG system for legal documents
- `exam_questions` - RAG system for reference questions

---

## Next Steps

After running migrations:

1. ✅ Set up Clerk webhook to create users
2. ✅ Generate initial 500 questions using `quiz_generator.py`
3. ✅ Implement FastAPI endpoints
4. ✅ Test exam flow

---

## Rollback

If you need to rollback, you can:

1. Drop new tables:
```sql
DROP TABLE IF EXISTS ai_chat_messages CASCADE;
DROP TABLE IF EXISTS ai_chat_sessions CASCADE;
DROP TABLE IF EXISTS user_mistakes CASCADE;
DROP TABLE IF EXISTS user_topic_performance CASCADE;
DROP TABLE IF EXISTS user_question_history CASCADE;
DROP TABLE IF EXISTS exam_question_answers CASCADE;
DROP TABLE IF EXISTS exams CASCADE;
DROP TABLE IF EXISTS ai_generated_questions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
```

2. Restore old schema from `../schema.sql` (if needed)

---

## Verification

After running migrations, verify with:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

You should see:
- ai_chat_messages
- ai_chat_sessions
- ai_generated_questions
- exam_question_answers
- exam_questions (RAG - unchanged)
- exams
- legal_doc_chunks (RAG - unchanged)
- user_mistakes
- user_question_history
- user_topic_performance
- users
