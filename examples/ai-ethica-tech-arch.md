# AI Ethica - Technical Architecture Document

## 1. Product Overview

**Product Name:** AI Ethica  
**Purpose:** AI-powered learning platform for Israeli Securities Authority ethics and securities law exams

### Target Users
- Investment advisor license candidates
- Portfolio manager candidates  
- Finance students
- Self-learners preparing for regulatory exams

### Core Value Proposition
AI system that identifies weak topics, strengthens knowledge, explains mistakes intuitively, and guides users through exam preparation.

---

## 2. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│              (TypeScript + React + Tailwind)             │
│  ┌──────────┬──────────┬──────────┬──────────────────┐ │
│  │ Practice │  Exam    │   Weak   │  Flashcards &    │ │
│  │   Mode   │Simulator │  Points  │    AI Chat       │ │
│  └──────────┴──────────┴──────────┴──────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ REST API / tRPC
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌──────────────────┐
│  Supabase       │         │  LangChain API   │
│  ────────       │         │  (Python/FastAPI)│
│  • PostgreSQL   │◄────────┤  ────────────    │
│  • Auth         │         │  • PDF Ingestion │
│  • Storage      │         │  • Vector Store  │
│  • Edge Funcs   │         │  • AI Generation │
│  • pgvector     │         │  • OpenAI API    │
└─────────────────┘         └──────────────────┘
```

---

## 3. Technology Stack

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS + shadcn/ui components
- **State Management:** React Context + Zustand
- **API Layer:** tRPC or REST with Axios
- **Auth:** Supabase Auth (Google, Apple, Email)
- **Forms:** React Hook Form + Zod validation

### Backend Services

#### A. Next.js API Routes/Server Actions
- User management
- Payment processing (Stripe)
- Progress tracking
- Admin operations

#### B. LangChain Python Service
- **Framework:** FastAPI
- **Libraries:**
  - LangChain for PDF processing and RAG
  - OpenAI API for GPT-4
  - Sentence-Transformers for embeddings
  - PyPDF2/Unstructured for PDF parsing
- **Vector Store:** Supabase pgvector
- **Deployment:** Docker container

### Database
- **Primary:** Supabase (PostgreSQL 15+)
- **Extensions:** pgvector for embeddings
- **Storage:** Supabase Storage for PDFs

### AI/ML
- **LLM:** OpenAI GPT-4 Turbo
- **Embeddings:** text-embedding-3-large
- **Fine-tuning:** Optional GPT-4 fine-tuning on exam data
- **Vector DB:** pgvector in Supabase

---

## 4. Database Schema

### Core Tables

```sql
-- Users (handled by Supabase Auth, extended with profiles)
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  subscription_tier TEXT DEFAULT 'free',
  subscription_expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Questions Bank (UPDATED FOR COMPLEX QUESTIONS)
CREATE TABLE questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_number INTEGER,
  question_text TEXT NOT NULL, -- Full question including all parts
  scenario TEXT, -- Main scenario/story
  sub_scenarios JSONB, -- {I: "...", II: "...", III: "..."} for multi-part
  question_stem TEXT, -- The actual question being asked
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  option_e TEXT NOT NULL,
  correct_answer CHAR(1) NOT NULL, -- א, ב, ג, ד, or ה
  explanation TEXT,
  legal_references TEXT[], -- Array of citations like "סעיף 17 לחוק הייעוץ"
  topic TEXT NOT NULL,
  difficulty TEXT DEFAULT 'medium',
  source_exam TEXT,
  source_pdf TEXT,
  word_count INTEGER,
  has_sub_scenarios BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- User Answers (Practice & Exam tracking)
CREATE TABLE user_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  question_id UUID REFERENCES questions(id),
  selected_answer CHAR(1),
  is_correct BOOLEAN,
  time_spent_seconds INTEGER,
  session_type TEXT, -- 'practice', 'exam', 'weak_point'
  session_id UUID,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Exam Sessions
CREATE TABLE exam_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  total_questions INTEGER DEFAULT 25,
  correct_answers INTEGER,
  score_percentage DECIMAL(5,2),
  time_taken_minutes INTEGER,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Weak Points Tracking
CREATE TABLE weak_points (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  question_id UUID REFERENCES questions(id),
  error_count INTEGER DEFAULT 1,
  last_failed_at TIMESTAMP,
  consecutive_correct INTEGER DEFAULT 0,
  status TEXT DEFAULT 'active', -- 'active', 'resolved'
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, question_id)
);

-- Flashcards/Concepts
CREATE TABLE flashcards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  term TEXT NOT NULL,
  definition TEXT NOT NULL,
  category TEXT,
  law_reference TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- User Flashcard Progress
CREATE TABLE user_flashcard_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  flashcard_id UUID REFERENCES flashcards(id),
  mastery_level INTEGER DEFAULT 0, -- 0-5
  last_reviewed_at TIMESTAMP,
  next_review_at TIMESTAMP,
  total_reviews INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, flashcard_id)
);

-- AI Chat History
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  response TEXT NOT NULL,
  context_used TEXT[], -- references to source documents
  created_at TIMESTAMP DEFAULT NOW()
);

-- Document Embeddings (for RAG)
CREATE TABLE document_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  embedding vector(1536), -- OpenAI embedding size
  metadata JSONB, -- {source, page, topic, etc}
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create vector similarity search index
CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Admin audit log
CREATE TABLE admin_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID REFERENCES profiles(id),
  action_type TEXT,
  entity_type TEXT,
  entity_id UUID,
  details JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. LangChain Backend Implementation

### Project Structure
```
langchain-backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── generate.py    # Question generation
│   │   │   │   ├── chat.py        # AI mentor chat
│   │   │   │   ├── ingest.py      # PDF ingestion
│   │   │   │   └── explain.py     # Explanation generation
│   ├── core/
│   │   ├── config.py
│   │   ├── supabase_client.py
│   │   └── security.py
│   ├── services/
│   │   ├── pdf_processor.py
│   │   ├── embeddings.py
│   │   ├── question_generator.py
│   │   ├── chat_service.py
│   │   └── rag_service.py
│   └── models/
│       ├── schemas.py
│       └── prompts.py
├── requirements.txt
├── Dockerfile
└── .env
```

### Key Implementation Files

#### 1. PDF Processing Pipeline (UPDATED FOR REAL EXAM COMPLEXITY)

```python
# services/pdf_processor.py
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from typing import List, Dict
import re

class PDFProcessor:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large"
        )
        # Different splitter for legal docs vs exams
        self.legal_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", ".", " "]
        )
    
    async def process_exam_pdf(self, pdf_path: str, exam_metadata: dict) -> List[dict]:
        """
        Extract COMPLETE questions from exam PDFs.
        Real Israeli ethics exams have:
        - Very long scenario-based questions (200-500+ words)
        - Multiple sub-parts (I, II, III, IV, V, VI)
        - 5 options (א-ה) which are also long and detailed
        - Legal citations embedded in questions
        - Answer key at the end with explanations
        """
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        full_text = "\n".join([page.page_content for page in pages])
        
        # Extract questions (numbered .1, .2, .3... up to .25)
        questions = self._extract_numbered_questions(full_text)
        
        # Extract answer key
        answer_key = self._extract_answer_key(full_text)
        
        # Combine questions with answers
        complete_questions = []
        for q_num, question_data in questions.items():
            if q_num in answer_key:
                complete_questions.append({
                    **question_data,
                    'correct_answer': answer_key[q_num]['answer'],
                    'explanation': answer_key[q_num].get('explanation', ''),
                    **exam_metadata
                })
        
        # Save to database
        for q in complete_questions:
            await self.supabase.table('questions').insert(q).execute()
        
        return complete_questions
    
    def _extract_numbered_questions(self, text: str) -> Dict[int, dict]:
        """
        Extract questions numbered .1 through .25
        Each question has:
        - Main scenario (can be 200-500 words)
        - Sub-scenarios marked with Roman numerals (I, II, III, etc.)
        - Final question asking "which of the following..."
        - 5 options (א, ב, ג, ד, ה)
        """
        questions = {}
        
        # Pattern: .1 or .2 or .3... up to .25
        # Matches: ".1 " or ".2 " with Hebrew text following
        question_pattern = r'\.(\d{1,2})\s+(.*?)(?=\.\d{1,2}\s+|מספר\s*שאלה|$)'
        
        matches = re.finditer(question_pattern, text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            q_num = int(match.group(1))
            question_text = match.group(2).strip()
            
            # Parse the full question structure
            parsed = self._parse_complex_question(question_text)
            
            if parsed:
                questions[q_num] = {
                    'question_number': q_num,
                    'question_text': parsed['full_text'],
                    'scenario': parsed['scenario'],
                    'sub_scenarios': parsed['sub_scenarios'],
                    'question_stem': parsed['question_stem'],
                    'option_a': parsed['options'].get('א', ''),
                    'option_b': parsed['options'].get('ב', ''),
                    'option_c': parsed['options'].get('ג', ''),
                    'option_d': parsed['options'].get('ד', ''),
                    'option_e': parsed['options'].get('ה', ''),
                    'topic': self._extract_topic(parsed['full_text']),
                    'legal_references': self._extract_legal_refs(parsed['full_text']),
                    'difficulty': 'medium'  # Can be updated with ML later
                }
        
        return questions
    
    def _parse_complex_question(self, text: str) -> dict:
        """
        Parse structure of complex Israeli ethics questions:
        1. Main scenario introduction
        2. Sub-scenarios (I, II, III, IV, V, VI) if present
        3. Final question stem ("בנסיבות המתוארות, איזה מן ההיגדים...")
        4. Five options (א, ב, ג, ד, ה)
        """
        result = {
            'full_text': text,
            'scenario': '',
            'sub_scenarios': {},
            'question_stem': '',
            'options': {}
        }
        
        # Extract Roman numeral sub-scenarios
        roman_pattern = r'((?:I{1,3}|IV|V|VI))\s+(.*?)(?=(?:I{1,3}|IV|V|VI)\s+|בנסיבות|איזה|אילו|מי|מה|א\.|$)'
        roman_matches = re.finditer(roman_pattern, text, re.DOTALL)
        
        for match in roman_matches:
            roman = match.group(1)
            content = match.group(2).strip()
            result['sub_scenarios'][roman] = content
        
        # Extract question stem (usually starts with בנסיבות, איזה, אילו, מי, מה)
        stem_pattern = r'(בנסיבות המתוארות|לפניכם|איזה מן ההיגדים|מי מהבאים|על פי|לפי)(.*?)(?=א\.|$)'
        stem_match = re.search(stem_pattern, text, re.DOTALL)
        if stem_match:
            result['question_stem'] = stem_match.group(0).strip()
        
        # Extract options א-ה
        option_pattern = r'([א-ה])\.\s+(.*?)(?=[א-ה]\.|$)'
        option_matches = re.finditer(option_pattern, text, re.DOTALL)
        
        for match in option_matches:
            letter = match.group(1)
            content = match.group(2).strip()
            result['options'][letter] = content
        
        # Scenario is everything before sub-scenarios or question stem
        if result['sub_scenarios']:
            first_roman = list(result['sub_scenarios'].keys())[0]
            scenario_end = text.find(first_roman)
            result['scenario'] = text[:scenario_end].strip()
        elif result['question_stem']:
            scenario_end = text.find(result['question_stem'])
            result['scenario'] = text[:scenario_end].strip()
        else:
            result['scenario'] = text[:text.find('א.')].strip() if 'א.' in text else text
        
        return result
    
    def _extract_answer_key(self, text: str) -> Dict[int, dict]:
        """
        Extract answer key table that appears at end of exam
        Format:
        מספר שאלה | תשובה נכונה | תוכן התשובה הנכונה
        1          | א           | (א) בירורים I, II, III ו-V בלבד.
        """
        answer_key = {}
        
        # Find the answer table section
        table_pattern = r'מספר\s*שאלה.*?תשובה.*?נכונה(.*?)(?=\n\n|$)'
        table_match = re.search(table_pattern, text, re.DOTALL)
        
        if table_match:
            table_content = table_match.group(1)
            
            # Parse each row: question_num | answer | explanation
            row_pattern = r'(\d{1,2})\s+([א-ה])\s+(.*?)(?=\n\d{1,2}\s+|$)'
            rows = re.finditer(row_pattern, table_content, re.DOTALL)
            
            for row in rows:
                q_num = int(row.group(1))
                answer = row.group(2)
                explanation = row.group(3).strip()
                
                answer_key[q_num] = {
                    'answer': answer,
                    'explanation': explanation
                }
        
        return answer_key
    
    def _extract_topic(self, text: str) -> str:
        """
        Identify topic based on keywords in question
        """
        topics = {
            'איסור הלבנת הון': 'money_laundering',
            'קרן נאמנות': 'mutual_funds',
            'דירקטור חיצוני': 'external_directors',
            'מידע פנים': 'insider_trading',
            'הצעת רכש': 'takeover_bids',
            'לקוח כשיר': 'qualified_clients',
            'ניגוד עניינים': 'conflict_of_interest',
            'ועדת ביקורת': 'audit_committee'
        }
        
        for keyword, topic in topics.items():
            if keyword in text:
                return topic
        
        return 'general'
    
    def _extract_legal_refs(self, text: str) -> List[str]:
        """
        Extract legal citations like "סעיף 17 לחוק הייעוץ"
        """
        refs = []
        
        # Pattern: סעיף X לחוק Y
        ref_pattern = r'סעיף\s+\d+[א-ת]*\s+לחוק\s+[א-ת\s]+'
        matches = re.finditer(ref_pattern, text)
        
        for match in matches:
            refs.append(match.group(0))
        
        return refs
    
    async def process_legal_document(self, pdf_path: str, metadata: dict):
        """
        Process legal documents (laws, regulations, presentations) for RAG
        These need to be chunked by legal section for proper retrieval
        """
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        # For legal docs, chunk by section/topic
        chunks = self.legal_splitter.split_documents(pages)
        
        # Generate embeddings and store with enhanced metadata
        for i, chunk in enumerate(chunks):
            # Extract section numbers if present
            section_refs = self._extract_legal_refs(chunk.page_content)
            
            embedding = self.embeddings.embed_query(chunk.page_content)
            
            await self.supabase.table('document_embeddings').insert({
                'content': chunk.page_content,
                'embedding': embedding,
                'metadata': {
                    **metadata,
                    'page': chunk.metadata.get('page', 0),
                    'chunk_index': i,
                    'legal_references': section_refs,
                    'document_type': 'legal_source'
                }
            }).execute()
        
        return len(chunks)
```

#### 2. Question Generator Service (UPDATED FOR COMPLEX QUESTIONS)

```python
# services/question_generator.py
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict
import json

class QuestionGenerator:
    def __init__(self, supabase_client):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7
        )
        self.supabase = supabase_client
    
    async def generate_similar_question(
        self, 
        topic: str, 
        difficulty: str,
        example_questions: List[dict],
        include_sub_scenarios: bool = False
    ) -> dict:
        """
        Generate new COMPLEX question similar to Israeli ethics exam style
        These are scenario-based questions with:
        - Detailed business/legal scenario (200-500 words)
        - Optional sub-scenarios (I, II, III, IV, V, VI)
        - Question stem asking for correct interpretation
        - 5 detailed options requiring legal reasoning
        """
        
        # Prepare examples with full structure
        examples_formatted = self._format_examples_for_prompt(example_questions)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """אתה מומחה ליצירת שאלות בחינה מורכבות באתיקה ודיני ניירות ערך, בדיוק כמו המבחנים 
האמיתיים של רשות ניירות ערך בישראל.

שאלות במבחן האמיתי הן:
- ארוכות ומפורטות (200-500 מילים)
- מבוססות על תרחישים ריאליסטיים של יועצי השקעות, מנהלי תיקים, או חברות
- מכילות פרטים ספציפיים: שמות, סכומים, אחוזים, תאריכים
- לעיתים כוללות תת-תרחישים מסומנים ברומיים (I, II, III, IV, V, VI)
- השאלה עצמה מתחילה ב"בנסיבות המתוארות" או "לפניכם"
- 5 אפשרויות תשובה (א-ה) שכל אחת היא משפט מלא או יותר
- האופציות דורשות הבנה משפטית, לא רק זיכרון
- כוללות ציטוטים מהחוק (סעיף X בחוק Y)

צור שאלה חדשה בנושא {topic} ברמת קושי {difficulty}.

דרישות:
1. תרחיש ריאליסטי ומפורט עם שמות בדויים בעברית
2. {sub_scenarios_instruction}
3. שאלה ברורה המתחילה ב"בנסיבות המתוארות" או דומה
4. 5 אופציות (א-ה) שכל אחת היא פסקה קצרה
5. רק תשובה אחת נכונה, השאר קרובות אבל לא מדויקות
6. הסבר מפורט למה התשובה נכונה
7. ציון הסעיף הרלוונטי בחוק

החזר JSON בפורמט:
{{
  "scenario": "התרחיש המלא...",
  "sub_scenarios": {{"I": "...", "II": "...", ...}} או null,
  "question_stem": "השאלה עצמה...",
  "option_a": "אופציה א...",
  "option_b": "אופציה ב...",
  "option_c": "אופציה ג...",
  "option_d": "אופציה ד...",
  "option_e": "אופציה ה...",
  "correct_answer": "א/ב/ג/ד/ה",
  "explanation": "הסבר מפורט למה זו התשובה הנכונה...",
  "legal_references": ["סעיף X בחוק Y", ...]
}}"""),
            ("user", """דוגמאות לשאלות מהמבחנים האמיתיים:

{examples}

עכשיו צור שאלה חדשה דומה בנושא {topic}.""")
        ])
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        sub_scenarios_instruction = (
            "כלול 3-6 תת-תרחישים מסומנים I, II, III, וכו'"
            if include_sub_scenarios
            else "ללא תת-תרחישים, רק תרחיש אחד מרכזי"
        )
        
        result = await chain.arun(
            topic=topic,
            difficulty=difficulty,
            sub_scenarios_instruction=sub_scenarios_instruction,
            examples=examples_formatted
        )
        
        # Parse JSON response
        try:
            question_data = json.loads(result)
            
            # Construct full question text
            full_text = self._construct_full_question(question_data)
            question_data['question_text'] = full_text
            question_data['word_count'] = len(full_text.split())
            question_data['has_sub_scenarios'] = bool(question_data.get('sub_scenarios'))
            question_data['topic'] = topic
            question_data['difficulty'] = difficulty
            
            return question_data
        except json.JSONDecodeError:
            # Fallback: try to extract from text
            return self._parse_generated_question(result, topic, difficulty)
    
    def _format_examples_for_prompt(self, questions: List[dict]) -> str:
        """Format example questions in a way that shows the full structure"""
        formatted = []
        
        for q in questions[:3]:  # Use top 3 examples
            example = f"""
שאלה {q.get('question_number', '')}:

תרחיש:
{q.get('scenario', '')}
"""
            if q.get('sub_scenarios'):
                example += "\nתת-תרחישים:\n"
                for key, value in q['sub_scenarios'].items():
                    example += f"{key}. {value}\n"
            
            example += f"""
שאלה:
{q.get('question_stem', '')}

אופציות:
א. {q.get('option_a', '')}
ב. {q.get('option_b', '')}
ג. {q.get('option_c', '')}
ד. {q.get('option_d', '')}
ה. {q.get('option_e', '')}

תשובה נכונה: {q.get('correct_answer', '')}
הסבר: {q.get('explanation', '')}
"""
            formatted.append(example)
        
        return "\n---\n".join(formatted)
    
    def _construct_full_question(self, data: dict) -> str:
        """Construct full question text from components"""
        parts = []
        
        # Add scenario
        if data.get('scenario'):
            parts.append(data['scenario'])
        
        # Add sub-scenarios if present
        if data.get('sub_scenarios'):
            for key, value in data['sub_scenarios'].items():
                parts.append(f"{key}. {value}")
        
        # Add question stem
        if data.get('question_stem'):
            parts.append(data['question_stem'])
        
        # Add options
        for letter in ['א', 'ב', 'ג', 'ד', 'ה']:
            option_key = f"option_{self._hebrew_to_english(letter)}"
            if data.get(option_key):
                parts.append(f"{letter}. {data[option_key]}")
        
        return "\n\n".join(parts)
    
    def _hebrew_to_english(self, hebrew_letter: str) -> str:
        """Convert Hebrew letters to English equivalents"""
        mapping = {'א': 'a', 'ב': 'b', 'ג': 'c', 'ד': 'd', 'ה': 'e'}
        return mapping.get(hebrew_letter, 'a')
    
    def _parse_generated_question(self, text: str, topic: str, difficulty: str) -> dict:
        """Fallback parser if JSON fails"""
        # Basic extraction logic
        return {
            'question_text': text,
            'topic': topic,
            'difficulty': difficulty,
            'explanation': 'Generated question requires review'
        }
    
    async def generate_adaptive_questions(
        self,
        user_id: str,
        num_questions: int = 10
    ) -> List[dict]:
        """
        Generate questions adapted to user's weak points
        Uses historical performance to target specific topics and difficulty
        """
        # Get user's weak topics
        weak_topics = await self._get_weak_topics(user_id)
        
        questions = []
        for topic_data in weak_topics[:num_questions]:
            topic = topic_data['topic']
            difficulty = self._adjust_difficulty(topic_data['success_rate'])
            
            # Get examples from this topic
            examples = await self.supabase.table('questions')\
                .select('*')\
                .eq('topic', topic)\
                .order('question_number')\
                .limit(3)\
                .execute()
            
            # Generate new question
            new_q = await self.generate_similar_question(
                topic=topic,
                difficulty=difficulty,
                example_questions=examples.data,
                include_sub_scenarios=(difficulty == 'hard')
            )
            
            questions.append(new_q)
        
        return questions
    
    async def _get_weak_topics(self, user_id: str) -> List[dict]:
        """Get topics where user performs poorly"""
        # Query user answers grouped by topic
        result = await self.supabase.rpc('get_topic_performance', {
            'p_user_id': user_id
        }).execute()
        
        # Return topics with <70% success rate, ordered by importance
        return [
            topic for topic in result.data 
            if topic['success_rate'] < 0.70
        ]
    
    def _adjust_difficulty(self, success_rate: float) -> str:
        """Adjust difficulty based on user performance"""
        if success_rate < 0.50:
            return 'easy'
        elif success_rate < 0.70:
            return 'medium'
        else:
            return 'hard'
```

#### 3. RAG Chat Service

```python
# services/chat_service.py
from langchain.vectorstores.supabase import SupabaseVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

class ChatService:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.3)
        
        # Initialize vector store
        self.vector_store = SupabaseVectorStore(
            client=supabase_client,
            embedding=OpenAIEmbeddings(),
            table_name="document_embeddings",
            query_name="match_documents"
        )
    
    async def chat(self, user_id: str, message: str, history: List[dict]) -> dict:
        """
        AI Mentor chat with RAG
        """
        # Set up memory from history
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        for msg in history[-5:]:  # Last 5 messages for context
            memory.chat_memory.add_user_message(msg['message'])
            memory.chat_memory.add_ai_message(msg['response'])
        
        # Create retrieval chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 4}
            ),
            memory=memory,
            return_source_documents=True
        )
        
        # Custom system prompt
        qa_chain.combine_docs_chain.llm_chain.prompt.messages[0].prompt.template = """
        אתה מורה פרטי מומחה באתיקה ודיני ניירות ערך בישראל.
        
        תפקידך:
        - להסביר מושגים בצורה פשוטה וברורה
        - לתת דוגמאות מהחיים
        - לצטט סעיפים רלוונטיים מהחוק
        - לענות רק על שאלות הקשורות לנושא הבחינה
        
        אם השאלה לא קשורה למבחן, אמר: "שאלה זו אינה קשורה לנושא המבחן באתיקה ודיני ניירות ערך"
        
        השתמש במידע הבא כדי לענות:
        {context}
        """
        
        result = await qa_chain.acall({"question": message})
        
        # Save to database
        await self.supabase.table('chat_messages').insert({
            'user_id': user_id,
            'message': message,
            'response': result['answer'],
            'context_used': [doc.metadata for doc in result['source_documents']]
        }).execute()
        
        return {
            'answer': result['answer'],
            'sources': result['source_documents']
        }
```

#### 4. FastAPI Main App

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="AI Ethica LangChain API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
from core.supabase_client import get_supabase_client
from services.question_generator import QuestionGenerator
from services.chat_service import ChatService
from services.pdf_processor import PDFProcessor

supabase = get_supabase_client()
question_gen = QuestionGenerator(supabase)
chat_service = ChatService(supabase)
pdf_processor = PDFProcessor(supabase)

# Request Models
class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: List[dict] = []

class GenerateQuestionRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    count: int = 1

# Endpoints
@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """AI Mentor Chat"""
    try:
        result = await chat_service.chat(
            user_id=request.user_id,
            message=request.message,
            history=request.history
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generate-questions")
async def generate_questions(request: GenerateQuestionRequest):
    """Generate new questions"""
    try:
        # Get example questions from DB
        examples = await supabase.table('questions')\
            .select('*')\
            .eq('topic', request.topic)\
            .limit(5)\
            .execute()
        
        questions = []
        for _ in range(request.count):
            q = await question_gen.generate_similar_question(
                topic=request.topic,
                difficulty=request.difficulty,
                example_questions=examples.data
            )
            questions.append(q)
        
        return {'questions': questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ingest-pdf")
async def ingest_pdf(file_path: str, doc_type: str):
    """Process and ingest PDF"""
    try:
        if doc_type == "exam":
            questions = await pdf_processor.process_exam_pdf(file_path)
            # Save to database
            for q in questions:
                await supabase.table('questions').insert(q).execute()
            return {'processed': len(questions)}
        
        elif doc_type == "legal":
            await pdf_processor.process_legal_document(
                file_path,
                metadata={'type': 'legal_document'}
            )
            return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/explain")
async def explain_answer(question_id: str, user_answer: str):
    """Generate detailed explanation for incorrect answer"""
    # Get question from DB
    question = await supabase.table('questions')\
        .select('*')\
        .eq('id', question_id)\
        .single()\
        .execute()
    
    if not question.data:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Generate explanation using RAG
    prompt = f"""הסבר מדוע התשובה הנכונה היא {question.data['correct_answer']} 
    ולא {user_answer}.
    
    שאלה: {question.data['question_text']}
    התשובה שנבחרה: {user_answer}
    התשובה הנכונה: {question.data['correct_answer']}
    
    הסבר בצורה פשוטה וציין את הסעיף הרלוונטי בחוק."""
    
    result = await chat_service.chat(
        user_id="system",
        message=prompt,
        history=[]
    )
    
    return {'explanation': result['answer']}
```

---

## 6. Next.js Frontend Implementation

### Project Structure

```
nextjs-frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/
│   │   ├── practice/
│   │   ├── exam/
│   │   ├── weak-points/
│   │   ├── flashcards/
│   │   ├── chat/
│   │   ├── progress/
│   │   └── layout.tsx
│   ├── admin/
│   │   ├── dashboard/
│   │   ├── questions/
│   │   └── users/
│   ├── api/
│   │   ├── payment/
│   │   └── webhook/
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/              # shadcn components
│   ├── practice/
│   ├── exam/
│   ├── chat/
│   └── shared/
├── lib/
│   ├── supabase/
│   │   ├── client.ts
│   │   ├── server.ts
│   │   └── types.ts
│   ├── langchain/
│   │   └── client.ts
│   └── utils.ts
├── hooks/
│   ├── use-questions.ts
│   ├── use-chat.ts
│   └── use-progress.ts
├── stores/
│   └── exam-store.ts
└── types/
    └── index.ts
```

### Key Components

#### 1. Practice Mode Component

```typescript
// app/(dashboard)/practice/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useSupabase } from '@/lib/supabase/client';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function PracticePage() {
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [stats, setStats] = useState({ correct: 0, total: 0 });
  
  const supabase = useSupabase();
  
  useEffect(() => {
    loadNextQuestion();
  }, []);
  
  const loadNextQuestion = async () => {
    // Load random question from DB
    const { data } = await supabase
      .from('questions')
      .select('*')
      .limit(1)
      .single();
    
    setCurrentQuestion(data);
    setSelectedAnswer(null);
    setShowExplanation(false);
  };
  
  const handleAnswerSelect = async (answer: string) => {
    setSelectedAnswer(answer);
    setShowExplanation(true);
    
    const isCorrect = answer === currentQuestion.correct_answer;
    
    // Save answer
    await supabase.from('user_answers').insert({
      user_id: (await supabase.auth.getUser()).data.user?.id,
      question_id: currentQuestion.id,
      selected_answer: answer,
      is_correct: isCorrect,
      session_type: 'practice'
    });
    
    // Update weak points if wrong
    if (!isCorrect) {
      await supabase.rpc('increment_weak_point', {
        p_user_id: (await supabase.auth.getUser()).data.user?.id,
        p_question_id: currentQuestion.id
      });
    }
    
    setStats(prev => ({
      correct: prev.correct + (isCorrect ? 1 : 0),
      total: prev.total + 1
    }));
  };
  
  return (
    <div className="container max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">תרגול שאלות</h1>
        <p className="text-muted-foreground">
          נכון: {stats.correct} / {stats.total}
        </p>
      </div>
      
      {currentQuestion && (
        <Card className="p-6">
          <h2 className="text-xl mb-6">{currentQuestion.question_text}</h2>
          
          <div className="space-y-3">
            {['a', 'b', 'c', 'd', 'e'].map(option => (
              <Button
                key={option}
                onClick={() => handleAnswerSelect(option)}
                disabled={showExplanation}
                variant={
                  showExplanation
                    ? option === currentQuestion.correct_answer
                      ? 'default'
                      : selectedAnswer === option
                      ? 'destructive'
                      : 'outline'
                    : 'outline'
                }
                className="w-full justify-start text-right"
              >
                {option.toUpperCase()}. {currentQuestion[`option_${option}`]}
              </Button>
            ))}
          </div>
          
          {showExplanation && (
            <div className="mt-6 p-4 bg-muted rounded-lg">
              <h3 className="font-semibold mb-2">הסבר:</h3>
              <p>{currentQuestion.explanation}</p>
              {currentQuestion.law_reference && (
                <p className="text-sm text-muted-foreground mt-2">
                  מקור: {currentQuestion.law_reference}
                </p>
              )}
              
              <Button 
                onClick={loadNextQuestion}
                className="mt-4"
              >
                שאלה הבאה
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
```

#### 2. AI Chat Component

```typescript
// app/(dashboard)/chat/page.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);
  
  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      // Call LangChain API
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current-user-id',
          message: input,
          history: messages
        })
      });
      
      const data = await response.json();
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      }]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="p-4 border-b">
        <h1 className="text-2xl font-bold">מרצה AI</h1>
      </div>
      
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`mb-4 ${
              msg.role === 'user' ? 'text-left' : 'text-right'
            }`}
          >
            <div
              className={`inline-block p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-right">
            <div className="inline-block p-3 bg-muted rounded-lg">
              מקליד...
            </div>
          </div>
        )}
      </ScrollArea>
      
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="שאל שאלה..."
            className="flex-1"
          />
          <Button onClick={sendMessage} disabled={loading}>
            שלח
          </Button>
        </div>
      </div>
    </div>
  );
}
```

---

## 7. Key Features Implementation Guide

### Feature 1: Practice Mode
**Implementation:**
1. Query random questions from database
2. Track answers in real-time
3. Show immediate feedback (green/red)
4. Save to `user_answers` table
5. Update `weak_points` for incorrect answers

### Feature 2: Exam Simulator
**Implementation:**
1. Create exam session in `exam_sessions` table
2. Select 25 random questions
3. Implement 150-minute timer
4. Lock navigation (forward only)
5. Calculate and save results
6. Generate detailed analytics

### Feature 3: Weak Point Trainer
**Implementation:**
1. Query `weak_points` table for user
2. Create adaptive quiz based on error frequency
3. Use spaced repetition algorithm
4. Mark as resolved after 2 consecutive correct answers

### Feature 4: Flashcards
**Implementation:**
1. Swipe interface using Framer Motion
2. Spaced repetition algorithm (SM-2)
3. Track mastery level (0-5)
4. Schedule next review in `user_flashcard_progress`

### Feature 5: AI Mentor
**Implementation:**
1. LangChain RAG system with legal documents
2. Conversation history management
3. Context-aware responses
4. Source citation from embeddings

### Feature 6: Progress Dashboard
**Implementation:**
1. Aggregate data from `user_answers` and `exam_sessions`
2. Calculate success rate by topic
3. Visualize with Recharts
4. Show achievements and levels

### Feature 7: Push Notifications
**Implementation:**
1. Firebase Cloud Messaging integration
2. Scheduled notifications via Supabase Edge Functions
3. Triggers: inactivity, weak points, achievements

### Feature 8: Admin Dashboard
**Implementation:**
1. Protected routes with Supabase RLS
2. CRUD operations on all tables
3. Analytics dashboards
4. CSV import for bulk question upload

---

## 8. Deployment Architecture

### Production Stack

```
┌─────────────────────────────────────┐
│         Vercel (Next.js)            │
│  ┌──────────────────────────────┐   │
│  │   Frontend + API Routes      │   │
│  └──────────────┬───────────────┘   │
└─────────────────┼───────────────────┘
                  │
                  │
    ┌─────────────┴────────────┐
    │                          │
    ▼                          ▼
┌───────────────┐      ┌──────────────────┐
│   Supabase    │      │  Railway/Render  │
│   (Cloud)     │      │  (Python API)    │
│               │      │                  │
│ • PostgreSQL  │◄─────┤ • FastAPI        │
│ • pgvector    │      │ • LangChain      │
│ • Auth        │      │ • Docker         │
│ • Storage     │      │                  │
└───────────────┘      └──────────────────┘
```

### Environment Variables

```bash
# .env.local (Next.js)
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
LANGCHAIN_API_URL=https://your-api.railway.app
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# .env (LangChain API)
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
ALLOWED_ORIGINS=https://your-app.vercel.app
```

---

## 9. Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up Next.js project with TypeScript
- [ ] Configure Supabase project
- [ ] Design and create database schema
- [ ] Set up LangChain FastAPI project
- [ ] Implement authentication

### Phase 2: Core Features (Weeks 3-5)
- [ ] Build Practice Mode
- [ ] Build Exam Simulator
- [ ] Implement PDF ingestion pipeline
- [ ] Create vector embeddings for legal docs
- [ ] Build basic AI chat

### Phase 3: Advanced Features (Weeks 6-8)
- [ ] Weak Point Trainer with adaptive algorithm
- [ ] Flashcards with spaced repetition
- [ ] Progress Dashboard with analytics
- [ ] Enhanced AI explanations

### Phase 4: Polish & Launch (Weeks 9-10)
- [ ] Admin Dashboard
- [ ] Payment integration (Stripe)
- [ ] Push notifications
- [ ] Performance optimization
- [ ] User testing and bug fixes
- [ ] Deployment

---

## 10. Success Metrics

### Technical KPIs
- API response time < 500ms (95th percentile)
- Vector search recall > 90%
- AI explanation accuracy > 85%
- App load time < 3 seconds

### Product KPIs
- User pass rate improvement > 20%
- Daily active users > 1000
- Average session length > 15 minutes
- Question generation accuracy > 90%

---

## 11. Security Considerations

1. **Authentication:** Supabase Auth with JWT tokens
2. **Authorization:** Row Level Security (RLS) policies
3. **API Security:** Rate limiting on LangChain API
4. **Data Encryption:** SSL/TLS for all communications
5. **GDPR Compliance:** User data export and deletion
6. **Admin Access:** Multi-factor authentication required

---

This architecture provides a solid foundation for building AI Ethica with scalable, maintainable code. Start with Phase 1 and iterate based on user feedback.

---

## 12. Critical Implementation Notes Based on Real Exam Analysis

### Understanding Israeli Ethics Exam Complexity

After analyzing actual ISA exams, here are critical implementation requirements:

#### A. Question Complexity
**Real exam questions are NOT simple Q&A.** They are:
- **200-500 words long** with detailed business scenarios
- **Multi-layered**: Main scenario + sub-scenarios (I, II, III, IV, V, VI)
- **Require legal reasoning**, not just memorization
- **Test application** of multiple laws simultaneously
- **Include specific details**: names, percentages, amounts, dates

**Example Pattern:**
```
[200-word scenario about investment advisor Yonatan and clients]

לפניכם שישה בירורים: (Here are 6 checks:)
I. מקור הכספים... (Source of funds...)
II. עיסוקו של הלקוח... (Client's occupation...)
III. מטרת פתיחת החשבון... (Purpose of account...)
[etc.]

על פי צו איסור הלבנת הון, אילו מן הבירורים... (According to AML law, which checks...)

א. בירורים I, II, III ו-V בלבד (Only I, II, III and V)
ב. בירורים II, III ו-V בלבד (Only II, III and V)
[etc.]
```

#### B. Technical Implications

**1. Database Schema Must Support:**
```sql
-- Store complex structure
sub_scenarios JSONB  -- {"I": "text", "II": "text", ...}
legal_references TEXT[]  -- Multiple law citations
word_count INTEGER  -- Track complexity
```

**2. RAG System Must:**
- Retrieve **entire legal sections**, not fragments
- Handle **cross-referencing** between laws
- Understand **Hebrew legal terminology** precisely
- Support **multi-document synthesis** (question may test 3+ laws)

**3. Question Generation Must:**
- Create realistic **business scenarios** with Hebrew names
- Generate **internally consistent** multi-part questions
- Produce **nuanced options** where multiple seem correct
- Include proper **legal citations** (סעיף X בחוק Y)

**4. Frontend Considerations:**
```typescript
// Questions can be VERY long - need proper display
interface ComplexQuestion {
  scenario: string;  // 200-500 words
  subScenarios?: Record<string, string>;  // Roman numerals
  questionStem: string;
  options: {
    a: string;  // Each option can be 50-100 words
    b: string;
    c: string;
    d: string;
    e: string;
  };
}

// UI must support:
// - Collapsible sections for long scenarios
// - Highlighting of key information
// - Progress through multi-part questions
// - Easy navigation between question parts
```

#### C. AI Training Considerations

**Fine-tuning is HIGHLY RECOMMENDED** because:
1. **Legal language is specialized** - GPT-4 alone may not generate authentic Hebrew legal style
2. **Question structure is unique** - the I/II/III pattern with nuanced options
3. **Consistency is critical** - wrong legal interpretations can mislead students

**Recommended Approach:**
```python
# 1. Use RAG for legal accuracy (MUST HAVE)
retriever = SupabaseVectorStore(...)

# 2. Fine-tune GPT-4 on 100+ real questions for STYLE (RECOMMENDED)
# - Train on question structure
# - Train on answer explanations
# - Train on legal Hebrew terminology

# 3. Hybrid: RAG retrieves legal facts, Fine-tuned model generates question
chain = RetrievalQA.from_chain_type(
    llm=FineTunedGPT4(...),
    retriever=retriever,
    ...
)
```

#### D. Quality Assurance System

**CRITICAL**: Generated questions must be reviewed before use. Implement:

```python
# Add to database schema
CREATE TABLE question_review (
  question_id UUID REFERENCES questions(id),
  reviewer_id UUID,  -- Admin who reviewed
  status TEXT,  -- 'pending', 'approved', 'rejected'
  feedback TEXT,
  legal_accuracy_score INTEGER,  -- 1-5
  clarity_score INTEGER,  -- 1-5
  reviewed_at TIMESTAMP
);

# Only show 'approved' questions to students
# OR show 'pending' with disclaimer "This AI-generated question is under review"
```

#### E. Explanation Generation

Based on real answer keys, explanations must:
1. **Quote the relevant law**: "לפי סעיף 17(א) לחוק הייעוץ..."
2. **Explain WHY other options are wrong**
3. **Provide context** from case law or RSA guidance
4. **Use proper Hebrew legal terminology**

**Implementation:**
```python
async def generate_explanation(question_id: str, selected_answer: str):
    # 1. Retrieve question + correct answer
    question = await get_question(question_id)
    
    # 2. RAG: Find relevant legal sections
    legal_context = await rag_system.retrieve(
        query=question.legal_references,
        k=5
    )
    
    # 3. Generate explanation using context
    prompt = f"""הסבר מדוע התשובה הנכונה היא {question.correct_answer} 
    ולא {selected_answer}.
    
    שאלה: {question.question_text}
    
    תשובה שנבחרה: {selected_answer}. {question.options[selected_answer]}
    תשובה נכונה: {question.correct_answer}. {question.options[question.correct_answer]}
    
    הקשר משפטי:
    {legal_context}
    
    צור הסבר מפורט המסביר:
    1. למה התשובה הנכונה נכונה (עם ציטוט מהחוק)
    2. מדוע התשובה שנבחרה שגויה
    3. הנקודה המשפטית הקריטית
    """
    
    return await llm.agenerate(prompt)
```

#### F. Performance Optimization

**Challenge**: Questions are long (500+ words), options are long (50-100 words each)

**Solutions**:
1. **Lazy loading**: Load question text only when needed
2. **Caching**: Cache frequently accessed questions
3. **Compression**: Store long text with gzip in DB
4. **Pagination**: Don't load all 25 exam questions at once

```typescript
// Frontend: Virtual scrolling for long questions
import { VirtualScroller } from '@/components/ui/virtual-scroller';

function ExamMode() {
  return (
    <VirtualScroller
      items={questions}
      itemHeight={800}  // Approximate height for long questions
      renderItem={(q) => <QuestionCard question={q} />}
    />
  );
}
```

#### G. Suggested Development Priorities (UPDATED)

**Phase 1: Foundation (Weeks 1-3)**
- [ ] PDF parser for **complex Hebrew questions** ⭐ CRITICAL
- [ ] Database with support for multi-part questions
- [ ] Basic RAG system with legal documents
- [ ] Admin review dashboard for generated questions

**Phase 2: Core Features (Weeks 4-6)**
- [ ] Practice mode with **long-form questions**
- [ ] Exam simulator (25 questions, proper timing)
- [ ] Explanation generator using RAG
- [ ] Manual question import from existing PDFs

**Phase 3: AI Generation (Weeks 7-9)**
- [ ] Complex question generator ⭐ CRITICAL
- [ ] Fine-tuning on real questions (if budget allows)
- [ ] Quality scoring system
- [ ] Weak point adaptive system

**Phase 4: Launch (Week 10)**
- [ ] Full testing with real students
- [ ] Legal accuracy verification
- [ ] Performance optimization
- [ ] Payment integration

#### H. Cost Estimates

**OpenAI API Costs (Monthly for 1000 active users):**
- **Embeddings** (text-embedding-3-large): ~$50-100
- **Question Generation** (GPT-4 Turbo): ~$500-1000
- **Chat/Explanations** (GPT-4 Turbo): ~$1000-2000
- **Fine-tuning** (one-time): ~$500-1000
- **Total**: ~$2000-4000/month

**Can be reduced by:**
- Caching common explanations
- Using GPT-3.5 for some tasks
- Limiting AI generation to paying users