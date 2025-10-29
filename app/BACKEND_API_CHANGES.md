# Backend API Changes Required for Guest Mode

## Overview
To comply with Apple App Store guideline 5.1.1, we've added guest mode to the app. Guest users can browse learning content (topics and concepts) WITHOUT creating an account.

## Required API Changes

### 1. Make These Endpoints PUBLIC (No Auth Required)

#### `/api/concepts/topics` - GET
**Purpose:** List all available topics with concept counts

**Current:** Requires authentication
**Required:** Allow access without authentication

**Example:**
```python
@router.get("/api/concepts/topics")
async def get_topics(user = Depends(get_optional_user)):  # Optional user
    """
    Get all topics with concept counts
    Works for both guest and authenticated users
    """
    topics = await fetch_all_topics()

    if user:
        # Authenticated user - add progress data
        return add_user_progress(topics, user)
    else:
        # Guest user - return basic data only
        return topics
```

**Response (Guest):**
```json
[
  {
    "topic": "פרק 1 - יסודות האתיקה",
    "concept_count": 15
  },
  {
    "topic": "פרק 2 - עקרונות מקצועיים",
    "concept_count": 12
  }
]
```

---

#### `/api/concepts/topics/{topic}` - GET
**Purpose:** Get all concepts for a specific topic

**Current:** May require authentication
**Required:** Allow access without authentication

**IMPORTANT:** Guest users should only get the first **10 concepts** per topic (to encourage sign-up)

**Example:**
```python
@router.get("/api/concepts/topics/{topic}")
async def get_concepts_by_topic(
    topic: str,
    user = Depends(get_optional_user)  # Optional user
):
    """
    Get all concepts for a topic
    - Guest users: First 10 concepts only
    - Authenticated users: All concepts with progress data
    """
    concepts = await fetch_concepts_by_topic(topic)

    if user:
        # Authenticated user - return ALL concepts with user data
        return enrich_with_user_data(concepts, user)
    else:
        # Guest user - return only first 10 concepts
        limited_concepts = concepts[:10]
        return limited_concepts
```

**Response (Guest):**
```json
[
  {
    "id": "concept-123",
    "topic": "פרק 1 - יסודות האתיקה",
    "title": "עקרון האוטונומיה",
    "explanation": "כבוד זכות האדם להחליט על עצמו...",
    "example": "למשל, אדם רשאי לסרב לטיפול רפואי...",
    "key_points": [
      "כבוד לזכות ההחלטה",
      "הסכמה מדעת",
      "חופש בחירה"
    ]
  }
]
```

---

#### `/api/concepts/{conceptId}` - GET (if exists)
**Purpose:** Get a single concept by ID

**Current:** May require authentication
**Required:** Allow access without authentication

---

### 2. Helper Function for Optional Authentication

Create a dependency that allows BOTH authenticated and guest users:

```python
from typing import Optional
from fastapi import Depends, Header

async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[User]:
    """
    Get user from token if provided, otherwise return None (guest)
    """
    if not authorization:
        return None  # Guest user

    try:
        # Remove 'Bearer ' prefix
        token = authorization.replace("Bearer ", "")

        # Verify and decode token
        user = await verify_token(token)
        return user
    except Exception as e:
        # Invalid token - treat as guest
        print(f"Invalid token: {e}")
        return None
```

---

### 3. Keep These Endpoints AUTHENTICATED (No Changes)

These features require an account and should remain authenticated:

```
POST /api/exams                     # Create exam
GET /api/exams/{examId}            # Get exam results
GET /api/practice/questions        # Practice questions
POST /api/practice/answer          # Submit answer
GET /api/progress                  # User progress
POST /api/ai-mentor/chat          # AI mentor
GET /api/users/me                  # User profile
POST /api/concepts/favorite       # Favorite concepts
GET /api/mistakes                  # Mistake review
```

---

## Testing

### Test Without Auth Token (Guest Mode)
```bash
# Should work - return topics
curl https://www.ethicaplus.net/api/concepts/topics

# Should work - return concepts for topic
curl "https://www.ethicaplus.net/api/concepts/topics/פרק%201%20-%20יסודות%20האתיקה"

# Should fail (401) - requires auth
curl https://www.ethicaplus.net/api/practice/questions
```

### Test With Auth Token (Authenticated User)
```bash
# Should work - return enriched data with user progress
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://www.ethicaplus.net/api/concepts/topics
```

---

## Implementation Checklist

- [ ] Add `get_optional_user` dependency function
- [ ] Update `/api/concepts/topics` to accept optional auth
- [ ] Update `/api/concepts/topics/{topic}` to accept optional auth
- [ ] Update `/api/concepts/{conceptId}` (if exists) to accept optional auth
- [ ] Test guest access (no token)
- [ ] Test authenticated access (with token)
- [ ] Verify authenticated endpoints still require auth
- [ ] Deploy changes

---

## Expected Behavior

### Guest Users Can:
✅ Browse all topics
✅ View up to **10 concepts per topic** (limited preview)
✅ Read examples and key points
✅ Use flashcard study mode (read-only, max 10 cards per topic)

### Guest Users Cannot:
❌ Practice questions
❌ Take exams
❌ Track progress
❌ Save favorites
❌ Use AI mentor
❌ Review mistakes
❌ View more than 10 concepts per topic

### Authenticated Users Get:
✅ Everything guests get, PLUS:
✅ User-specific progress data
✅ Favorite concepts
✅ Study statistics
✅ Personalized recommendations

---

## Security Considerations

1. **Rate Limiting:** Add rate limiting for guest endpoints to prevent abuse
2. **Data Filtering:** Guest users should only see published/approved content
3. **No Personal Data:** Don't expose any user-generated content to guests
4. **Analytics:** Track guest usage separately for analytics

---

## Questions?

Contact the mobile team if you need clarification on any endpoints or behavior.

**Last Updated:** 2025-10-29
