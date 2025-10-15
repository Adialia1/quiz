# Backend Architecture - Quiz App

> **Master Plan Document**
> Last Updated: 2025-10-12

## 📋 Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [API Routes](#api-routes)
4. [Key Workflows](#key-workflows)
5. [Clerk Integration](#clerk-integration)
6. [Question Generation Strategy](#question-generation-strategy)
7. [Adaptive Algorithm](#adaptive-algorithm)
8. [Implementation Checklist](#implementation-checklist)

---

## Overview

The quiz app backend is built with:
- **FastAPI** - REST API framework
- **Supabase** - PostgreSQL database
- **Clerk** - Authentication (webhook integration)
- **AI Question Generation** - Pre-generated question pool
- **RAG System** - Legal docs + exam questions

### Core Principles

1. **Pre-generated Questions** - Generate 500+ questions upfront, don't generate on-demand
2. **User Performance Tracking** - Track every answer to build user profile
3. **Adaptive Learning** - Questions adapt to user's weak areas
4. **Topic-based Analysis** - Track performance by topic for targeted review
5. **Mistake Review** - Dedicated system for reviewing wrong answers

---

## Database Schema

### 1. `users`

User profiles synced from Clerk via webhook.

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  phone TEXT,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login_at TIMESTAMP WITH TIME ZONE,

  -- Subscription
  subscription_status TEXT DEFAULT 'free' CHECK (subscription_status IN ('free', 'premium', 'trial')),
  subscription_expires_at TIMESTAMP WITH TIME ZONE,

  -- Aggregate Stats
  total_questions_answered INTEGER DEFAULT 0,
  total_exams_taken INTEGER DEFAULT 0,
  average_score DECIMAL(5,2),

  -- Preferences
  preferred_difficulty TEXT DEFAULT 'adaptive' CHECK (preferred_difficulty IN ('easy', 'medium', 'hard', 'adaptive'))
);

CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_email ON users(email);
```

**Notes:**
- `clerk_user_id` is the link to Clerk authentication
- Aggregate stats updated via triggers or scheduled jobs
- `preferred_difficulty` can be 'adaptive' to auto-adjust

---

### 2. `ai_generated_questions`

Pre-generated question pool. Format matches output from `quiz_generator.py`.

```sql
CREATE TABLE ai_generated_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Question Content (matches quiz_generator.py output format)
  question_text TEXT NOT NULL,

  -- Options (exactly 5: A, B, C, D, E)
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  option_e TEXT NOT NULL,

  correct_answer TEXT NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D', 'E')),
  explanation TEXT NOT NULL,

  -- Metadata
  topic TEXT NOT NULL,
  sub_topic TEXT,
  difficulty_level TEXT NOT NULL CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
  legal_reference TEXT,

  -- Optional
  image_url TEXT,
  source_doc_id UUID, -- Link to RAG document if available

  -- Generation metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  generated_by TEXT DEFAULT 'quiz_generator', -- Which system generated it

  -- Quality tracking (updated as users answer)
  quality_score DECIMAL(3,2), -- 0.0 to 1.0 based on user performance
  times_shown INTEGER DEFAULT 0,
  times_correct INTEGER DEFAULT 0,
  times_wrong INTEGER DEFAULT 0,
  average_time_seconds DECIMAL(6,2),

  -- Expert validation metadata (from quiz_generator.py)
  expert_validated BOOLEAN DEFAULT false,
  expert_validation_data JSONB
);

CREATE INDEX idx_questions_topic ON ai_generated_questions(topic);
CREATE INDEX idx_questions_difficulty ON ai_generated_questions(difficulty_level);
CREATE INDEX idx_questions_active ON ai_generated_questions(is_active);
CREATE INDEX idx_questions_quality ON ai_generated_questions(quality_score);
```

**Question Format Example (from quiz_generator.py):**
```json
{
  "question_text": "רוני, יועץ השקעות בחברת פיננס-טק בע\"מ, קיבל מידע על...",
  "options": {
    "A": "אפשרות א...",
    "B": "אפשרות ב...",
    "C": "אפשרות ג...",
    "D": "אפשרות ד...",
    "E": "אפשרות ה..."
  },
  "correct_answer": "B",
  "explanation": "הסבר מפורט...",
  "topic": "מידע פנים",
  "difficulty": "medium",
  "legal_reference": "חוק ניירות ערך, תשכ\"ח-1968, סעיף 52"
}
```

**Notes:**
- Store options as separate columns (option_a, option_b, etc.) for easier querying
- `is_active` allows disabling low-quality questions without deleting
- `quality_score` auto-calculated from user performance
- Questions with quality_score < 0.6 should be reviewed/regenerated

---

### 3. `exams`

Individual exam sessions (practice, simulation, review).

```sql
CREATE TABLE exams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Exam metadata
  exam_type TEXT NOT NULL CHECK (exam_type IN ('practice', 'full_simulation', 'review_mistakes')),
  status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),

  -- Timestamps
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,

  -- Questions
  total_questions INTEGER NOT NULL,
  answered_questions INTEGER DEFAULT 0,
  correct_answers INTEGER DEFAULT 0,
  wrong_answers INTEGER DEFAULT 0,
  skipped_answers INTEGER DEFAULT 0,

  -- Results
  score_percentage DECIMAL(5,2),
  time_taken_seconds INTEGER,
  passing_threshold INTEGER DEFAULT 85, -- 85% to pass
  passed BOOLEAN,

  -- Topics covered in this exam
  topics_covered JSONB -- e.g., ["מידע פנים", "חובות גילוי", "מניפולציה"]
);

CREATE INDEX idx_exams_user ON exams(user_id);
CREATE INDEX idx_exams_type ON exams(exam_type);
CREATE INDEX idx_exams_status ON exams(status);
CREATE INDEX idx_exams_completed ON exams(completed_at);
```

**Notes:**
- Each exam session is a separate row
- `exam_type`:
  - `practice` - "תרגול שאלות" (flexible, no time limit)
  - `full_simulation` - "סימולציית מבחן" (30 questions, timed)
  - `review_mistakes` - "חזרה על טעויות" (only wrong questions)
- `topics_covered` stored as JSON array for easy filtering

---

### 4. `exam_questions`

Junction table linking exams to questions with user answers.

```sql
CREATE TABLE exam_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),

  -- Question order in exam
  question_order INTEGER NOT NULL, -- 1, 2, 3, etc.

  -- User's answer
  user_answer TEXT CHECK (user_answer IN ('A', 'B', 'C', 'D', 'E', NULL)),
  is_correct BOOLEAN,

  -- Timing
  time_taken_seconds INTEGER,
  answered_at TIMESTAMP WITH TIME ZONE,

  -- Flags
  flagged_for_review BOOLEAN DEFAULT false, -- User can flag during exam

  UNIQUE(exam_id, question_order)
);

CREATE INDEX idx_exam_questions_exam ON exam_questions(exam_id);
CREATE INDEX idx_exam_questions_question ON exam_questions(question_id);
CREATE INDEX idx_exam_questions_correct ON exam_questions(is_correct);
```

**Notes:**
- One row per question per exam
- `flagged_for_review` - user can mark questions to review later
- `time_taken_seconds` - time spent on this specific question

---

### 5. `user_question_history`

Aggregate history of each user's performance on each question.

```sql
CREATE TABLE user_question_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),

  -- Performance
  times_seen INTEGER DEFAULT 0,
  times_correct INTEGER DEFAULT 0,
  times_wrong INTEGER DEFAULT 0,

  -- Timestamps
  first_seen_at TIMESTAMP WITH TIME ZONE,
  last_seen_at TIMESTAMP WITH TIME ZONE,

  -- Metrics
  average_time_seconds DECIMAL(6,2),

  -- Mastery level (auto-calculated)
  mastery_level TEXT DEFAULT 'not_seen' CHECK (mastery_level IN ('not_seen', 'learning', 'practicing', 'mastered')),

  UNIQUE(user_id, question_id)
);

CREATE INDEX idx_history_user ON user_question_history(user_id);
CREATE INDEX idx_history_question ON user_question_history(question_id);
CREATE INDEX idx_history_mastery ON user_question_history(mastery_level);
```

**Mastery Level Rules:**
- `not_seen` - Never seen this question
- `learning` - Seen 1-2 times, < 50% correct
- `practicing` - Seen 3+ times, 50-80% correct
- `mastered` - Seen 3+ times, > 80% correct

**Notes:**
- Updated after each answer via trigger or API
- Used for adaptive question selection

---

### 6. `user_topic_performance`

Aggregate performance by topic for each user.

```sql
CREATE TABLE user_topic_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic TEXT NOT NULL,

  -- Performance
  total_questions INTEGER DEFAULT 0,
  correct_answers INTEGER DEFAULT 0,
  wrong_answers INTEGER DEFAULT 0,
  accuracy_percentage DECIMAL(5,2),

  -- Metrics
  average_time_seconds DECIMAL(6,2),
  last_practiced_at TIMESTAMP WITH TIME ZONE,

  -- Strength level (auto-calculated)
  strength_level TEXT DEFAULT 'average' CHECK (strength_level IN ('weak', 'average', 'strong')),

  UNIQUE(user_id, topic)
);

CREATE INDEX idx_topic_perf_user ON user_topic_performance(user_id);
CREATE INDEX idx_topic_perf_topic ON user_topic_performance(topic);
CREATE INDEX idx_topic_perf_strength ON user_topic_performance(strength_level);
```

**Strength Level Rules:**
- `weak` - < 70% accuracy
- `average` - 70-90% accuracy
- `strong` - > 90% accuracy

**Notes:**
- Updated after each exam completion
- Used for identifying weak areas
- Powers "מעקב התקדמות" analytics

---

### 7. `user_mistakes`

Track questions the user got wrong for "חזרה על טעויות".

```sql
CREATE TABLE user_mistakes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES ai_generated_questions(id),
  exam_id UUID REFERENCES exams(id), -- Which exam it was from

  -- Mistake tracking
  times_wrong INTEGER DEFAULT 1,
  first_wrong_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_wrong_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Review status
  reviewed BOOLEAN DEFAULT false, -- True after user gets it right in review mode
  reviewed_at TIMESTAMP WITH TIME ZONE,
  marked_for_review BOOLEAN DEFAULT true
);

CREATE INDEX idx_mistakes_user ON user_mistakes(user_id);
CREATE INDEX idx_mistakes_question ON user_mistakes(question_id);
CREATE INDEX idx_mistakes_reviewed ON user_mistakes(reviewed);
CREATE INDEX idx_mistakes_marked ON user_mistakes(marked_for_review);
```

**Notes:**
- Row created when user answers wrong
- `reviewed` = true when user finally gets it right in review mode
- Used for "חזרה על טעויות" feature
- Can show "You've gotten this wrong 3 times"

---

### 8. `ai_chat_sessions`

Chat sessions for "מרצה AI" feature.

```sql
CREATE TABLE ai_chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Context
  topic TEXT,
  question_id UUID REFERENCES ai_generated_questions(id), -- If asking about specific question

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user ON ai_chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_created ON ai_chat_sessions(created_at);
```

---

### 9. `ai_chat_messages`

Individual messages in chat sessions.

```sql
CREATE TABLE ai_chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,

  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON ai_chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON ai_chat_messages(created_at);
```

**Notes:**
- Store full conversation history
- Can use for context in future messages
- Can analyze common user questions

---

## API Routes

### Auth & User Management

```
POST   /api/auth/webhook              # Clerk webhook for user creation/update
GET    /api/users/me                  # Get current user profile
PATCH  /api/users/me                  # Update profile
GET    /api/users/me/stats            # Get user statistics
DELETE /api/users/me                  # Delete account
```

**Authentication:**
- All routes (except webhook) require Clerk JWT token
- Webhook requires Clerk signing secret validation

---

### Questions Management (Admin)

```
POST   /api/admin/questions/generate  # Generate batch of questions
GET    /api/admin/questions            # List all questions
GET    /api/admin/questions/{id}       # Get specific question
PATCH  /api/admin/questions/{id}       # Update question
DELETE /api/admin/questions/{id}       # Delete/deactivate question
POST   /api/admin/questions/validate   # Validate question quality
```

---

### Exams

```
POST   /api/exams                      # Create new exam session
  Body: {
    "exam_type": "practice" | "full_simulation" | "review_mistakes",
    "question_count": 20,  // optional
    "topics": ["topic1", "topic2"]  // optional, for filtering
  }
  Response: {
    "exam_id": "uuid",
    "exam_type": "practice",
    "total_questions": 20,
    "questions": [...]  // Array of questions
  }

GET    /api/exams/{exam_id}            # Get exam details
  Response: {
    "id": "uuid",
    "exam_type": "practice",
    "status": "in_progress",
    "started_at": "2025-10-12T...",
    "total_questions": 20,
    "answered_questions": 15,
    "current_question": 16
  }

POST   /api/exams/{exam_id}/answer     # Submit answer to question
  Body: {
    "question_id": "uuid",
    "user_answer": "B",
    "time_taken_seconds": 45
  }
  Response: {
    "is_correct": true,
    "correct_answer": "B",
    "explanation": "...",
    "immediate_feedback": true  // for practice mode
  }

POST   /api/exams/{exam_id}/submit     # Submit final exam
  Response: {
    "exam_id": "uuid",
    "score_percentage": 85.5,
    "passed": true,
    "correct_answers": 26,
    "wrong_answers": 4,
    "time_taken_seconds": 1800,
    "weak_topics": ["מידע פנים"],
    "strong_topics": ["חובות גילוי"]
  }

DELETE /api/exams/{exam_id}            # Abandon exam

GET    /api/exams/history              # Get user's exam history
  Query: ?limit=10&offset=0&type=full_simulation
  Response: {
    "exams": [...],
    "total_count": 45,
    "average_score": 82.3
  }

GET    /api/exams/{exam_id}/results    # Get detailed exam results
  Response: {
    "exam": {...},
    "questions": [...],  // All questions with user answers
    "analytics": {
      "time_per_question": 60,
      "accuracy_by_topic": {...}
    }
  }
```

---

### Practice Mode ("תרגול שאלות")

```
POST   /api/practice/start             # Start practice session
  Body: {
    "question_count": 20,
    "topics": ["מידע פנים"],  // optional
    "difficulty": "adaptive"   // or "easy", "medium", "hard"
  }
  Response: {
    "exam_id": "uuid",
    "questions": [...]
  }
```

**Note:** Practice mode uses the same exam endpoints but with `exam_type: "practice"`

---

### Review Mistakes ("חזרה על טעויות")

```
GET    /api/mistakes                   # Get all user mistakes
  Response: {
    "total_mistakes": 45,
    "by_topic": {
      "מידע פנים": 12,
      "חובות גילוי": 8,
      ...
    },
    "unreviewed_count": 23
  }

GET    /api/mistakes/questions         # Get questions to review
  Query: ?topic=מידע פנים&limit=20
  Response: {
    "questions": [...],  // Questions user got wrong
    "metadata": {
      "times_wrong": 3,
      "last_wrong_at": "...",
      "reviewed": false
    }
  }

POST   /api/mistakes/{mistake_id}/review  # Mark mistake as reviewed
  (Called automatically when user answers correctly in review mode)
```

---

### Analytics & Progress ("מעקב התקדמות")

```
GET    /api/analytics/overview         # Dashboard stats
  Response: {
    "total_exams": 45,
    "total_questions": 1234,
    "average_score": 82.5,
    "current_streak": 7,  // Days in a row
    "time_studied_minutes": 1234,
    "rank": "Top 15%"  // Compared to other users
  }

GET    /api/analytics/topics           # Performance by topic
  Response: {
    "topics": [
      {
        "topic": "מידע פנים",
        "accuracy": 75.5,
        "questions_answered": 45,
        "strength_level": "average",
        "trend": "improving"  // or "declining", "stable"
      },
      ...
    ]
  }

GET    /api/analytics/weaknesses       # Identified weak areas
  Response: {
    "weak_topics": [
      {
        "topic": "מידע פנים",
        "accuracy": 65.2,
        "questions_to_master": 12,
        "recommendation": "Practice 20 more questions"
      }
    ]
  }

GET    /api/analytics/progress         # Progress over time
  Query: ?period=week|month|year
  Response: {
    "chart_data": [
      { "date": "2025-10-05", "score": 75.5, "questions": 20 },
      { "date": "2025-10-06", "score": 78.2, "questions": 30 },
      ...
    ],
    "improvement": "+12.5% this month"
  }

GET    /api/analytics/comparison       # Compare to other users
  Response: {
    "your_score": 82.5,
    "average_score": 78.3,
    "percentile": 75,  // You're in top 25%
    "rank": "Advanced"
  }
```

---

### AI Instructor ("מרצה AI")

```
POST   /api/ai/sessions                # Start new chat session
  Body: {
    "topic": "מידע פנים",  // optional
    "question_id": "uuid"  // optional, if asking about specific question
  }
  Response: {
    "session_id": "uuid",
    "created_at": "..."
  }

GET    /api/ai/sessions                # List user's sessions
  Response: {
    "sessions": [
      {
        "id": "uuid",
        "topic": "מידע פנים",
        "last_message_at": "...",
        "message_count": 15
      }
    ]
  }

GET    /api/ai/sessions/{id}/messages  # Get chat history
  Response: {
    "messages": [
      { "role": "user", "content": "...", "created_at": "..." },
      { "role": "assistant", "content": "...", "created_at": "..." }
    ]
  }

POST   /api/ai/sessions/{id}/message   # Send message
  Body: {
    "content": "מה זה מידע פנים?"
  }
  Response: {
    "role": "assistant",
    "content": "מידע פנים הוא...",
    "created_at": "..."
  }

DELETE /api/ai/sessions/{id}           # Delete session
```

---

### Legal Content ("מושגים וחוקים")

```
GET    /api/legal/topics               # List all legal topics
  Response: {
    "topics": [
      {
        "name": "מידע פנים",
        "description": "...",
        "question_count": 45,
        "difficulty": "medium"
      }
    ]
  }

GET    /api/legal/search               # Search legal content
  Query: ?q=מידע פנים&limit=10
  Response: {
    "results": [
      {
        "title": "חוק ניירות ערך - סעיף 52",
        "content": "...",
        "relevance": 0.95
      }
    ]
  }

GET    /api/legal/topic/{topic}        # Get specific topic details
  Response: {
    "topic": "מידע פנים",
    "definition": "...",
    "legal_references": [...],
    "related_questions": [...],
    "examples": [...]
  }
```

---

## Key Workflows

### 1. User Registration Flow

```
1. User signs up in app → Clerk handles auth
2. Clerk sends webhook → POST /api/auth/webhook
3. Backend creates user in `users` table
4. Returns success
5. User is ready to take exams
```

**Webhook Payload:**
```json
{
  "type": "user.created",
  "data": {
    "id": "user_xxx",
    "email_addresses": [...],
    "first_name": "...",
    "last_name": "..."
  }
}
```

---

### 2. Practice Mode Flow ("תרגול שאלות")

```
1. User clicks "תרגול שאלות"
2. App: POST /api/practice/start
   {
     "question_count": 20,
     "difficulty": "adaptive"
   }

3. Backend:
   - Get user's weak topics from user_topic_performance
   - Select 20 questions using adaptive algorithm
   - Create exam record with type="practice"
   - Return questions

4. User answers each question
   App: POST /api/exams/{exam_id}/answer
   Backend:
   - Save answer in exam_questions
   - Update user_question_history
   - Return immediate feedback (correct/wrong + explanation)

5. User finishes practice
   App: POST /api/exams/{exam_id}/submit
   Backend:
   - Calculate final score
   - Update user_topic_performance
   - Update user aggregate stats
   - Return summary
```

---

### 3. Full Simulation Flow ("סימולציית מבחן")

```
1. User clicks "סימולציית מבחן"
2. App: POST /api/exams
   {
     "exam_type": "full_simulation",
     "question_count": 30
   }

3. Backend:
   - Select 30 questions (adaptive, covering all topics)
   - Create exam record
   - Return all questions at once

4. User takes exam (timed)
   - For each answer: POST /api/exams/{exam_id}/answer
   - No immediate feedback (only saves answer)

5. User submits exam
   App: POST /api/exams/{exam_id}/submit
   Backend:
   - Calculate score
   - Update all statistics
   - Create mistake records for wrong answers
   - Return detailed results

6. App shows results screen
   - Score: 85% (PASSED)
   - Correct: 26/30
   - Time: 30:15
   - Weak topics: [...]
```

---

### 4. Review Mistakes Flow ("חזרה על טעויות")

```
1. User clicks "חזרה על טעויות"
2. App: GET /api/mistakes
   Backend: Returns mistake summary by topic

3. User selects topic (or "כל הנושאים")
4. App: GET /api/mistakes/questions?topic=מידע פנים
   Backend: Returns questions user got wrong in that topic

5. User practices those questions
   - Same as practice mode
   - When user answers correctly → mark as reviewed

6. Backend: POST /api/mistakes/{mistake_id}/review
   - Set reviewed = true
   - Remove from active mistakes
```

---

## Clerk Integration

### Webhook Setup

1. In Clerk Dashboard:
   - Go to Webhooks
   - Add endpoint: `https://your-api.com/api/auth/webhook`
   - Select events:
     - `user.created`
     - `user.updated`
     - `user.deleted`
   - Copy signing secret

2. In Backend (`.env`):
   ```
   CLERK_WEBHOOK_SECRET=whsec_xxx
   ```

3. Webhook handler validates signature:
   ```python
   from svix.webhooks import Webhook

   wh = Webhook(CLERK_WEBHOOK_SECRET)
   wh.verify(payload, headers)
   ```

### JWT Authentication

All API routes (except webhook) require Clerk JWT:

```python
from clerk_sdk import Clerk

async def get_current_user(authorization: str):
    token = authorization.replace("Bearer ", "")
    clerk = Clerk(api_key=CLERK_SECRET_KEY)
    session = clerk.verify_token(token)
    return session.user_id
```

---

## Question Generation Strategy

### Initial Generation (500 questions)

```python
# Generate 500 questions covering all topics
topics = [
    "מידע פנים",
    "חובות גילוי",
    "מניפולציה",
    "ניגוד עניינים",
    "חובות נאמנות",
    "רישוי",
    ...
]

for topic in topics:
    # Generate ~50 questions per topic
    generator.generate_quiz(
        question_count=50,
        topic=topic,
        difficulty=None  # Mixed
    )
```

### Distribution

- **40% Easy** - Basic understanding questions
- **40% Medium** - Application questions
- **20% Hard** - Complex scenario questions

### Quality Control

1. **Structural Validation** - All questions have 5 options
2. **Legal Expert Validation** - Expert agent validates correctness
3. **User Performance Tracking** - Questions with low quality_score are flagged
4. **Periodic Review** - Regenerate questions with quality_score < 0.6

### Question Format (from quiz_generator.py)

```json
{
  "question_text": "שוקי ומוקי הם שותפים בחברת ייעוץ השקעות...",
  "options": {
    "A": "שוקי פעל בהתאם לחוק ולא עבר עבירה",
    "B": "שוקי עבר עבירה על איסור מידע פנים",
    "C": "שוקי חייב לדווח לרשות לניירות ערך",
    "D": "שוקי יכול להמשיך לפעול אם הוא לא מרוויח מהמידע",
    "E": "כל התשובות נכונות"
  },
  "correct_answer": "B",
  "explanation": "לפי סעיף 52 לחוק ניירות ערך...",
  "topic": "מידע פנים",
  "difficulty": "medium",
  "legal_reference": "חוק ניירות ערך, תשכ\"ח-1968, סעיף 52",
  "expert_validated": true
}
```

---

## Adaptive Algorithm

### Question Selection Algorithm

When selecting questions for a user, weight questions based on:

```python
def calculate_question_weight(question, user_history, user_topics):
    base_weight = 1.0

    # 1. Topic weakness (2x weight for weak topics)
    if question.topic in user_topics['weak_topics']:
        base_weight *= 2.0

    # 2. Question history
    history = user_history.get(question.id)
    if history:
        # Recently wrong? (3x weight)
        if history.last_seen_recently and history.is_wrong:
            base_weight *= 3.0

        # Mastered? (0.3x weight - rarely show)
        if history.mastery_level == 'mastered':
            base_weight *= 0.3

        # Not seen yet? (1.5x weight)
    else:
        base_weight *= 1.5

    # 3. Time since last seen (older = more likely)
    if history and history.last_seen_at:
        days_since = (now - history.last_seen_at).days
        if days_since > 7:
            base_weight *= 1.3
        elif days_since > 30:
            base_weight *= 1.6

    # 4. Question difficulty matching user level
    user_level = calculate_user_level(user_topics)
    if question.difficulty == user_level:
        base_weight *= 1.2

    # 5. Question quality
    if question.quality_score:
        base_weight *= question.quality_score

    return base_weight
```

### User Level Calculation

```python
def calculate_user_level(user_topics):
    avg_accuracy = sum(t.accuracy for t in user_topics) / len(user_topics)

    if avg_accuracy < 70:
        return 'easy'
    elif avg_accuracy < 85:
        return 'medium'
    else:
        return 'hard'
```

---

## Implementation Checklist

### Phase 1: Database Setup
- [ ] Create all tables in Supabase
- [ ] Set up Row Level Security (RLS) policies
- [ ] Create indexes for performance
- [ ] Set up database triggers for auto-updates

### Phase 2: Clerk Integration
- [ ] Set up Clerk webhook endpoint
- [ ] Implement webhook signature validation
- [ ] Test user creation flow
- [ ] Implement JWT authentication middleware

### Phase 3: Question Generation
- [ ] Generate initial 500 questions using quiz_generator.py
- [ ] Store questions in ai_generated_questions table
- [ ] Validate all questions
- [ ] Set up question quality monitoring

### Phase 4: Core Exam APIs
- [ ] Implement POST /api/exams (create exam)
- [ ] Implement POST /api/exams/{id}/answer (submit answer)
- [ ] Implement POST /api/exams/{id}/submit (finish exam)
- [ ] Implement adaptive question selection
- [ ] Test practice mode flow

### Phase 5: Analytics & Progress
- [ ] Implement user_topic_performance updates
- [ ] Implement user_question_history updates
- [ ] Implement GET /api/analytics/* endpoints
- [ ] Create analytics dashboard

### Phase 6: Mistake Review
- [ ] Implement user_mistakes tracking
- [ ] Implement GET /api/mistakes endpoints
- [ ] Test review mode flow

### Phase 7: AI Instructor
- [ ] Implement chat session endpoints
- [ ] Integrate Legal Expert agent
- [ ] Test chat flow

### Phase 8: Testing & Optimization
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Load testing
- [ ] Bug fixes

---

## Notes

- All timestamps use `TIMESTAMP WITH TIME ZONE` for proper timezone handling
- All routes return JSON with consistent error format
- Use Supabase RLS policies to ensure users can only access their own data
- Consider rate limiting for API endpoints
- Consider caching for analytics endpoints (Redis)
- Monitor question quality_score and regenerate low-quality questions

---

**Status:** Ready for implementation
**Next Step:** Create Supabase migrations
