# Exams API Documentation

Complete guide for the exam management system.

## Overview

The Exams API handles the complete exam lifecycle:
- ✅ Create exam sessions (practice, full simulation, review mistakes)
- ✅ Deliver questions dynamically
- ✅ Submit answers with immediate or delayed feedback
- ✅ Calculate scores and analytics
- ✅ Track user progress and weak/strong topics
- ✅ Store detailed exam history

---

## Exam Types

### 1. Practice Mode (`practice`)
- **Purpose:** Learning and practicing
- **Feedback:** Immediate after each answer
- **Time Limit:** None
- **Questions:** Random (can include questions you've seen before)
- **Use Case:** Daily practice, topic review

### 2. Full Simulation (`full_simulation`)
- **Purpose:** Exam simulation
- **Feedback:** Only at the end
- **Time Limit:** 60 minutes
- **Questions:** ⭐ **ONLY FRESH QUESTIONS** - Never repeats questions you've seen in any previous exam
- **Use Case:** Pre-exam preparation, assessment

### 3. Review Mistakes (`review_mistakes`)
- **Purpose:** Focus on previously incorrect answers
- **Feedback:** Immediate
- **Time Limit:** None
- **Questions:** Only questions you got wrong (from `user_mistakes` table)
- **Use Case:** Targeted improvement

---

## API Endpoints

### 1. Create Exam Session

**`POST /api/exams`**

Create a new exam session with selected questions.

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "exam_type": "practice",
  "question_count": 25,
  "topics": ["מידע פנים", "חובות גילוי"],
  "difficulty": "medium"
}
```

**Parameters:**
- `exam_type` (required): `practice` | `full_simulation` | `review_mistakes`
- `question_count` (optional): Number of questions (default: **25**)
- `topics` (optional): Filter by specific topics. **If omitted, uses adaptive selection** ⭐
- `difficulty` (optional): `easy` | `medium` | `hard`

---

## ⭐ Adaptive Question Selection

**When `topics` is NOT specified**, the system uses intelligent topic selection:

### How it works:
1. **Analyzes your performance** - Gets your 5 weakest topics from `user_topic_performance`
2. **60% from weak topics** - Focus on areas you struggle with
3. **40% from other topics** - Discover new weak areas

### Example:
```json
// User's topic performance:
// מידע פנים: 55% (weak)
// דיווח מיידי: 62% (weak)
// חובות גילוי: 88% (strong)
// אתיקה מקצועית: 92% (strong)

// Request without topics:
{
  "exam_type": "practice",
  "question_count": 25
}

// System selects:
// - 15 questions (60%) from: מידע פנים, דיווח מיידי
// - 10 questions (40%) from: all other topics (to discover new weak areas)
```

### Benefits:
- ✅ **Reinforces weak areas** - More practice on topics you struggle with
- ✅ **Discovers new weak spots** - Tests you on other topics too
- ✅ **Adaptive learning** - Gets smarter as you practice
- ✅ **No manual topic selection needed** - System knows what you need

**Response:**
```json
{
  "exam_id": "550e8400-e29b-41d4-a716-446655440000",
  "exam_type": "practice",
  "total_questions": 20,
  "started_at": "2025-10-12T10:30:00Z",
  "time_limit_minutes": null,
  "questions": [
    {
      "id": "question-uuid-1",
      "question_text": "מהו מידע פנים?",
      "option_a": "מידע שאיננו ידוע לציבור",
      "option_b": "מידע שפורסם בעיתון",
      "option_c": "מידע על מוצרי חברה",
      "option_d": "מידע על עובדי החברה",
      "option_e": "מידע פיננסי בלבד",
      "topic": "מידע פנים",
      "sub_topic": "הגדרות בסיסיות",
      "difficulty_level": "medium",
      "image_url": null
    }
    // ... 19 more questions
  ]
}
```

**Notes:**
- Questions are delivered WITHOUT correct answers or explanations
- Questions are randomly selected from the database
- For `review_mistakes`, only previously incorrect questions are used

---

### 2. Get Exam Details

**`GET /api/exams/{exam_id}`**

Get current exam status and progress.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "exam_type": "practice",
  "status": "in_progress",
  "started_at": "2025-10-12T10:30:00Z",
  "completed_at": null,
  "total_questions": 20,
  "answered_questions": 15,
  "current_question": 16,
  "time_limit_minutes": null
}
```

---

### 3. Submit Answer

**`POST /api/exams/{exam_id}/answer`**

Submit an answer to a specific question.

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "question_id": "question-uuid-1",
  "user_answer": "B",
  "time_taken_seconds": 45
}
```

**Parameters:**
- `question_id` (required): UUID of the question
- `user_answer` (required): `A` | `B` | `C` | `D` | `E`
- `time_taken_seconds` (required): Time spent on question

**Response (Practice Mode):**
```json
{
  "is_correct": true,
  "correct_answer": "A",
  "explanation": "מידע פנים מוגדר כמידע שאיננו ידוע לציבור ויש לו השפעה מהותית על מחיר ניירות הערך.",
  "immediate_feedback": true
}
```

**Response (Full Simulation):**
```json
{
  "is_correct": true,
  "correct_answer": null,
  "explanation": null,
  "immediate_feedback": false
}
```

**Side Effects:**
- Updates `exam_question_answers` table
- Creates record in `user_question_history`
- If incorrect, adds to `user_mistakes` table
- Updates question statistics (times_shown, times_correct, times_wrong)

---

### 4. Submit Final Exam

**`POST /api/exams/{exam_id}/submit`**

Submit the exam and get results.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "exam_id": "550e8400-e29b-41d4-a716-446655440000",
  "score_percentage": 85.5,
  "passed": true,
  "correct_answers": 26,
  "wrong_answers": 4,
  "time_taken_seconds": 1800,
  "weak_topics": [
    "מידע פנים",
    "דיווח מיידי"
  ],
  "strong_topics": [
    "חובות גילוי",
    "אתיקה מקצועית"
  ]
}
```

**Passing Grade:** 70%

**Topic Classification:**
- **Weak Topic:** < 60% accuracy
- **Strong Topic:** ≥ 80% accuracy

**Side Effects:**
- Updates exam status to `completed`
- Sets `score_percentage` and `passed` fields
- Increments user statistics (total_questions_answered, total_exams_taken)
- Updates `user_topic_performance` table

---

### 5. Abandon Exam

**`DELETE /api/exams/{exam_id}`**

Abandon an in-progress exam.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "status": "success",
  "message": "Exam abandoned",
  "exam_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Side Effects:**
- Updates exam status to `abandoned`
- Sets `completed_at` timestamp
- Partial answers are preserved in database

---

### 6. Get Exam History

**`GET /api/exams/history`**

Get user's exam history with pagination.

**Authentication:** Required (Bearer token)

**Query Parameters:**
- `limit` (optional): Results per page (1-100, default: 10)
- `offset` (optional): Pagination offset (default: 0)
- `type` (optional): Filter by exam type

**Example:**
```
GET /api/exams/history?limit=10&offset=0&type=full_simulation
```

**Response:**
```json
{
  "exams": [
    {
      "id": "exam-uuid-1",
      "exam_type": "full_simulation",
      "status": "completed",
      "score_percentage": 85.5,
      "passed": true,
      "started_at": "2025-10-12T10:30:00Z",
      "completed_at": "2025-10-12T11:45:00Z",
      "total_questions": 30
    },
    {
      "id": "exam-uuid-2",
      "exam_type": "practice",
      "status": "completed",
      "score_percentage": 78.0,
      "passed": true,
      "started_at": "2025-10-11T14:20:00Z",
      "completed_at": "2025-10-11T15:10:00Z",
      "total_questions": 20
    }
  ],
  "total_count": 45,
  "average_score": 82.3
}
```

---

### 7. Get Detailed Exam Results

**`GET /api/exams/{exam_id}/results`**

Get comprehensive exam results with all questions, answers, and analytics.

**Authentication:** Required (Bearer token)

**Requirements:** Exam must be `completed`

**Response:**
```json
{
  "exam": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "exam_type": "full_simulation",
    "status": "completed",
    "started_at": "2025-10-12T10:30:00Z",
    "completed_at": "2025-10-12T11:45:00Z",
    "total_questions": 30,
    "answered_questions": 30,
    "current_question": 30,
    "time_limit_minutes": 60
  },
  "questions": [
    {
      "question_id": "question-uuid-1",
      "question_text": "מהו מידע פנים?",
      "user_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "time_taken_seconds": 45,
      "topic": "מידע פנים",
      "difficulty_level": "medium",
      "explanation": "מידע פנים מוגדר כמידע שאיננו ידוע לציבור..."
    }
    // ... 29 more questions with full details
  ],
  "analytics": {
    "time_per_question": 60.5,
    "accuracy_by_topic": {
      "מידע פנים": 75.5,
      "חובות גילוי": 88.2,
      "דיווח מיידי": 92.1
    },
    "difficulty_breakdown": {
      "easy": 10,
      "medium": 12,
      "hard": 8
    }
  }
}
```

---

## React Native Integration

### Setup API Client

```typescript
// app/src/utils/examApi.ts
import { useAuth } from '@clerk/clerk-expo';

const API_URL = process.env.EXPO_PUBLIC_API_URL;

export const examApi = {
  async createExam(data: {
    exam_type: 'practice' | 'full_simulation' | 'review_mistakes';
    question_count?: number;
    topics?: string[];
    difficulty?: string;
  }) {
    const { getToken } = useAuth();
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    return response.json();
  },

  async submitAnswer(examId: string, data: {
    question_id: string;
    user_answer: string;
    time_taken_seconds: number;
  }) {
    const { getToken } = useAuth();
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}/answer`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    return response.json();
  },

  async submitExam(examId: string) {
    const { getToken } = useAuth();
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}/submit`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    return response.json();
  },

  async getExamHistory(params?: {
    limit?: number;
    offset?: number;
    type?: string;
  }) {
    const { getToken } = useAuth();
    const token = await getToken();

    const queryParams = new URLSearchParams(params as any).toString();
    const url = `${API_URL}/api/exams/history${queryParams ? `?${queryParams}` : ''}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    return response.json();
  },

  async getExamResults(examId: string) {
    const { getToken } = useAuth();
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}/results`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    return response.json();
  }
};
```

### Usage in Exam Screen

```typescript
// app/src/screens/ExamScreen.tsx
import { useState, useEffect } from 'react';
import { examApi } from '../utils/examApi';

export const ExamScreen = ({ route }) => {
  const { examType } = route.params;
  const [exam, setExam] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [startTime, setStartTime] = useState(Date.now());

  // Create exam on mount
  useEffect(() => {
    createExam();
  }, []);

  const createExam = async () => {
    const result = await examApi.createExam({
      exam_type: examType,
      question_count: 20
    });
    setExam(result);
  };

  const handleAnswer = async (selectedOption: string) => {
    const timeTaken = Math.floor((Date.now() - startTime) / 1000);
    const currentQuestion = exam.questions[currentQuestionIndex];

    const result = await examApi.submitAnswer(exam.exam_id, {
      question_id: currentQuestion.id,
      user_answer: selectedOption,
      time_taken_seconds: timeTaken
    });

    // Show feedback if practice mode
    if (result.immediate_feedback) {
      showFeedback(result);
    }

    // Move to next question or submit exam
    if (currentQuestionIndex < exam.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setStartTime(Date.now());
    } else {
      await submitExam();
    }
  };

  const submitExam = async () => {
    const results = await examApi.submitExam(exam.exam_id);
    // Navigate to results screen
    navigation.navigate('Results', { results });
  };

  // ... render UI
};
```

---

## Database Schema

### Tables Used

**`exams`**
- Stores exam session metadata
- Fields: id, user_id, exam_type, status, started_at, completed_at, score_percentage, passed, total_questions, time_limit_minutes

**`exam_question_answers`**
- Junction table linking exams to questions with answers
- Fields: id, exam_id, question_id, question_order, user_answer, is_correct, time_taken_seconds, answered_at

**`user_question_history`**
- Complete history of all user answers across all exams
- Auto-calculates mastery_level (not_seen → learning → practicing → mastered)
- Fields: id, user_id, question_id, user_answer, is_correct, time_taken_seconds, context, mastery_level

**`user_mistakes`**
- Tracks incorrect answers for review
- Fields: id, user_id, question_id, user_answer, correct_answer, exam_id, is_resolved, times_reviewed

**`user_topic_performance`**
- Aggregated statistics per topic
- Auto-calculates strength_level (weak/average/strong)
- Fields: id, user_id, topic, questions_answered, correct_answers, accuracy_percentage, strength_level

---

## Testing

### Test Create Exam

```bash
curl -X POST http://localhost:8000/api/exams \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exam_type": "practice",
    "question_count": 10,
    "topics": ["מידע פנים"],
    "difficulty": "medium"
  }'
```

### Test Submit Answer

```bash
curl -X POST http://localhost:8000/api/exams/EXAM_ID/answer \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "QUESTION_ID",
    "user_answer": "A",
    "time_taken_seconds": 45
  }'
```

### Test Submit Exam

```bash
curl -X POST http://localhost:8000/api/exams/EXAM_ID/submit \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Get History

```bash
curl http://localhost:8000/api/exams/history?limit=10&offset=0 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Get Results

```bash
curl http://localhost:8000/api/exams/EXAM_ID/results \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Handling

### Common Errors

**400 Bad Request - Not enough questions**
```json
{
  "detail": "Not enough questions available. Requested: 20, Available: 15"
}
```
**Solution:** Reduce question_count or remove topic/difficulty filters

**404 Not Found - Exam not found**
```json
{
  "detail": "Exam not found or not in progress"
}
```
**Solution:** Verify exam_id and ensure exam belongs to user

**400 Bad Request - Exam not completed**
```json
{
  "detail": "Exam not completed yet"
}
```
**Solution:** Submit the exam before requesting results

---

## Next Steps

1. ✅ Run migration: `010_create_increment_user_stats_function.sql`
2. ⬜ Test all endpoints with Postman/curl
3. ⬜ Integrate in React Native app
4. ⬜ Build exam UI screens (selection, questions, results)
5. ⬜ Add real-time timer for full simulations
6. ⬜ Implement exam pause/resume functionality
7. ⬜ Add analytics dashboard

---

## Related Files

- `api/routes/exams.py` - Exam routes implementation
- `api/main.py` - FastAPI app with exam router
- `agent/scripts/migrations/004_create_exams_table.sql` - Exams table
- `agent/scripts/migrations/005_create_exam_question_answers.sql` - Junction table
- `agent/scripts/migrations/010_create_increment_user_stats_function.sql` - Stats function

---

**Last Updated:** 2025-10-12
**Status:** ✅ Fully Implemented
