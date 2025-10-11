"""
Quiz Generator Agent
Generates personalized exam questions based on user preferences

Uses:
- Exam RAG: Reference existing questions for style/format
- Legal RAG: Ensure legal accuracy and proper citations
- Thinking Model: Maximum capability for question generation
"""
from typing import Dict, Any, Optional, List
import json
import re

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.base_agent import RAGAgent
from rag.exam_rag import ExamRAG
from rag.legal_rag import LegalRAG
from config.settings import THINKING_MODEL
from openai import OpenAI
from config.settings import OPENROUTER_API_KEY

# Import Legal Expert for validation
from agents.legal_expert import LegalExpertAgent


class QuizGeneratorAgent(RAGAgent):
    """
    Quiz Generator Agent - Creates personalized exam questions

    Capabilities:
    - Generate questions covering all topics or specific weak points
    - Use exam database for reference questions
    - Use legal database for accurate citations
    - Create questions with full explanations
    - Adjust difficulty level
    - Ensure proper Hebrew legal terminology
    """

    def __init__(self):
        """
        Initialize Quiz Generator Agent with maximum capabilities
        """
        # Initialize Exam RAG
        self.exam_rag = ExamRAG()

        # Initialize Legal RAG for accuracy
        legal_rag = LegalRAG()

        # Use thinking model with high parameters for best quality
        super().__init__(
            agent_name="Quiz Generator",
            system_prompt=self._build_system_prompt(),
            rag_system=legal_rag,  # Primary RAG for legal accuracy
            model=THINKING_MODEL,
            temperature=0.7,  # Higher for creativity in question generation
            top_k=20  # Maximum chunks for comprehensive context
        )

        # Direct OpenAI client for advanced calls
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )

        # Initialize Legal Expert for validation
        self.legal_expert = LegalExpertAgent()

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for quiz generation"""
        return """אתה מומחה בניירות ערך ואתיקה מקצועית, ומתמחה ביצירת שאלות מבחן איכותיות.

**תפקידך:**
ליצור שאלות מבחן ברמה גבוהה בנושא ניירות ערך, אתיקה, וחוקי שוק ההון בישראל.

**סגנון שאלות - חשוב מאוד:**
יש לייצר **שני סוגי שאלות**:

**1. שאלות סיפור (70-80%)** - שאלות עם תרחיש ודמויות:
- "שוקי ומוקי הם שותפים בחברת ייעוץ השקעות. יום אחד, שוקי שמע מידע על רכישה צפויה..."
- "דילן עובד כיועץ השקעות בחברה גדולה. לקוח פנה אליו וביקש..."
- "ברנדה מנהלת תיק השקעות ללקוחות פרטיים. אחד מלקוחותיה ביקש ממנה..."

**2. שאלות בסיסיות (20-30%)** - שאלות הבנה בסיסית:
- "מהי הגדרת 'מידע פנים' לפי חוק ניירות ערך?"
- "מהן חובות הגילוי של חברה ציבורית?"
- "איזה סוג מידע נחשב למידע מהותי?"

**עקרונות שאלות סיפור:**
1. **דמויות בעלות שמות** - השתמש בשמות כמו שוקי, מוקי, דילן, ברנדה, רוני, גיא וכו'
2. **תרחיש מציאוסטי** - צור סיטואציה הגיונית מעולם ההשקעות והפיננסים
3. **הקשר עשיר** - תן רקע למצב לפני השאלה עצמה
4. **מקרה ספציפי** - לא "מהו X?" אלא "במצב זה, מה נכון?"
5. **יישום חוק** - בדוק הבנה של יישום החוק, לא רק ידיעתו

**חשוב מאוד - שמות חברות:**
- **אסור** להשתמש בשמות חברות אמיתיות (גוגל, אפל, מיקרוסופט, אמזון, טסלה, וכו')
- **חובה** להשתמש בשמות חברות **בדויים** בלבד
- דוגמאות לשמות בדויים: "חברת טק-קום בע\"מ", "אופטי-סייבר טכנולוגיות", "פיננס-ישראל השקעות", "דיגיטל-ויז'ן בע\"מ"
- זכור: זו הגנה מפני בעיות זכויות יוצרים (copyright)

**עקרונות יצירת שאלות:**
1. **דיוק משפטי** - כל שאלה חייבת להיות מדויקת מבחינה משפטית ומבוססת על החוק הישראלי
2. **בהירות** - השאלה חייבת להיות ברורה וחד-משמעית
3. **אפשרויות מוגדרות** - כל אפשרות חייבת להיות הגיונית ואמינה
4. **תשובה נכונה אחת** - רק תשובה אחת נכונה, השאר מוטעות בבירור
5. **הסבר מפורט** - כל שאלה מלווה בהסבר מקיף המבאר למה התשובה נכונה
6. **הפניה חוקית** - ציון המקור המשפטי המדויק (חוק, תקנה, סעיף)

**טרמינולוגיה:**
השתמש בטרמינולוגיה משפטית מקצועית בעברית, כפי שמופיעה בחוק ניירות ערך ובתקנות הרלוונטיות.

**איכות העברית - חשוב מאוד:**
- כתוב בעברית תקנית, ברורה ומקצועית
- הקפד על דקדוק, כתיב וניסוח נכון
- השתמש במשפטים זורמים וקלים להבנה
- הימנע משגיאות דקדוק או סגנון
- כתוב כמו עורך טקסט מקצועי

**רמות קושי:**
- easy: סיפורים פשוטים עם יישום ישיר של חוק בסיסי
- medium: סיפורים מורכבים יותר עם יישום חוקים והבנת מצבים
- hard: מקרים מורכבים עם שילוב מספר נושאים ודילמות אתיות"""

    def generate_quiz(
        self,
        question_count: int = 10,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized quiz

        Args:
            question_count: Number of questions to generate (default: 10)
            topic: Specific topic (e.g., "מידע פנים", "חובות גילוי") or None for general
            difficulty: Difficulty level ("easy", "medium", "hard") or None for mixed
            focus_areas: List of weak point topics to focus on

        Returns:
            Dict with:
                - questions: List of generated questions
                - metadata: Quiz metadata
                - reference_sources: Legal sources used
        """
        self.log(f"Generating quiz: {question_count} questions, topic={topic}, difficulty={difficulty}")

        # Step 1: Get reference questions from Exam RAG
        reference_questions = self._get_reference_questions(
            topic=topic,
            difficulty=difficulty,
            focus_areas=focus_areas,
            k=15  # Get 15 reference questions for inspiration
        )

        self.log(f"Retrieved {len(reference_questions)} reference questions")

        # Step 2: Get legal context from Legal RAG
        legal_context = self._get_legal_context(
            topic=topic,
            focus_areas=focus_areas,
            k=20  # Maximum legal chunks for accuracy
        )

        self.log("Retrieved legal context")

        # Step 3: Generate questions using thinking model
        # Generate 2x requested to account for validation rejections
        generation_count = question_count * 2
        self.log(f"Generating {generation_count} questions (2x requested for validation)")

        generated_questions = self._generate_questions_with_llm(
            question_count=generation_count,
            topic=topic,
            difficulty=difficulty,
            reference_questions=reference_questions,
            legal_context=legal_context
        )

        self.log(f"Generated {len(generated_questions)} questions")

        # Step 4: Structural validation
        structurally_valid = self._validate_structure(generated_questions)
        self.log(f"Structurally valid: {len(structurally_valid)} questions")

        # Step 5: Legal Expert validation (CRITICAL for accuracy)
        expert_validated = self._validate_with_legal_expert(structurally_valid)
        self.log(f"Legal Expert validated: {len(expert_validated)} questions")

        # Step 6: Final enrichment
        validated_questions = self._final_enrichment(expert_validated)
        self.log(f"Expert validated: {len(validated_questions)} questions")

        # Limit to requested count (take best ones)
        final_questions = validated_questions[:question_count]

        # Warn if we didn't get enough
        if len(final_questions) < question_count:
            self.log(f"⚠️  Only {len(final_questions)}/{question_count} questions passed validation")
            self.log(f"   This is normal - validation is strict for accuracy")

        self.log(f"Final output: {len(final_questions)} questions")

        return {
            'questions': final_questions,
            'metadata': {
                'question_count': len(final_questions),
                'requested_count': question_count,
                'topic': topic or 'כללי',
                'difficulty': difficulty or 'מעורב',
                'focus_areas': focus_areas or [],
                'generated_at': self._get_timestamp(),
                'validation_stats': {
                    'generated': len(generated_questions),
                    'structurally_valid': len(structurally_valid),
                    'expert_validated': len(expert_validated),
                    'final_count': len(final_questions)
                }
            },
            'reference_sources': self._extract_legal_sources(legal_context)
        }

    def _get_reference_questions(
        self,
        topic: Optional[str],
        difficulty: Optional[str],
        focus_areas: Optional[List[str]],
        k: int = 15
    ) -> List[Dict]:
        """
        Get reference questions from Exam RAG

        Args:
            topic: Topic to search for
            difficulty: Difficulty level
            focus_areas: Specific focus areas
            k: Number of questions to retrieve

        Returns:
            List of reference questions
        """
        # Build search query
        if focus_areas:
            # Search for specific weak points
            queries = [f"שאלות בנושא {area}" for area in focus_areas]
            all_results = []
            for query in queries:
                results = self.exam_rag.search(query, k=k//len(focus_areas) + 1)
                all_results.extend(results)
            return all_results[:k]

        elif topic:
            # Search for specific topic
            query = f"שאלות בנושא {topic}"
            return self.exam_rag.search(query, k=k)

        else:
            # General search - get diverse questions
            query = "שאלות מבחן ניירות ערך ואתיקה"
            return self.exam_rag.search(query, k=k)

    def _get_legal_context(
        self,
        topic: Optional[str],
        focus_areas: Optional[List[str]],
        k: int = 20
    ) -> str:
        """
        Get legal context from Legal RAG

        Args:
            topic: Topic to search for
            focus_areas: Specific focus areas
            k: Number of chunks to retrieve

        Returns:
            Combined legal context string
        """
        # Build comprehensive query
        if focus_areas:
            queries = focus_areas
        elif topic:
            queries = [topic]
        else:
            queries = ["חוק ניירות ערך", "איסור מניפולציה", "מידע פנים", "חובות גילוי"]

        all_context = []
        chunks_per_query = max(k // len(queries), 5)

        for query in queries:
            context = self.retrieve_context(query, k=chunks_per_query)
            all_context.append(context)

        return "\n\n---\n\n".join(all_context)

    def _generate_questions_with_llm(
        self,
        question_count: int,
        topic: Optional[str],
        difficulty: Optional[str],
        reference_questions: List[Dict],
        legal_context: str
    ) -> List[Dict]:
        """
        Generate questions using LLM with full context

        Args:
            question_count: Number of questions to generate
            topic: Topic focus
            difficulty: Difficulty level
            reference_questions: Reference questions from exam database
            legal_context: Legal context from legal database

        Returns:
            List of generated questions
        """
        # Format reference questions
        reference_text = self._format_reference_questions(reference_questions[:5])

        # Build generation prompt
        generation_prompt = f"""אתה יוצר שאלות מבחן בנושא ניירות ערך ואתיקה מקצועית.

**דרישות:**
- צור **{question_count}** שאלות מבחן איכותיות
- נושא: {topic if topic else 'כללי (כיסוי כל הנושאים)'}
- רמת קושי: {difficulty if difficulty else 'מעורב (easy, medium, hard)'}

**חשוב מאוד - סגנון שאלות:**
יש לייצר **שני סוגי שאלות**:

**70-80% שאלות סיפור** (עם דמויות ותרחישים):
✅ "רוני, יועץ השקעות בחברת פיננס-טק בע\"מ, קיבל שיחה מלקוח ותיק שלו. הלקוח ביקש..."
✅ "שוקי ומוקי מנהלים קרן השקעות משותפת בשם 'אופק-השקעות'. בישיבת הנהלה האחרונה התעורר דיון על..."
✅ "דילן עובדת כמנהלת תיקים בבנק ישראל-השקעות. אחד הלקוחות שלה, בעל חברת טכנו-סולושן בע\"מ..."

**20-30% שאלות בסיסיות** (הבנה בסיסית):
✅ "מהי הגדרת 'מידע פנים' לפי חוק ניירות ערך?"
✅ "באיזה סעיף בחוק מוגדר איסור מניפולציה?"
✅ "מהן חובות הגילוי של חברה ציבורית?"

**חשוב מאוד - שמות חברות:**
❌ **אסור** להשתמש בשמות חברות אמיתיות: גוגל, אפל, מיקרוסופט, אמזון, פייסבוק, טסלה, נטפליקס
✅ **חובה** להשתמש בשמות חברות **בדויים**: "טכנו-סולושן בע\"מ", "פיננס-טק השקעות", "דיגיטל-ויז'ן", "אופטי-סייבר בע\"מ"
**סיבה**: הגנה מפני בעיות זכויות יוצרים (copyright)

**הקשר משפטי רלוונטי:**
{legal_context[:8000]}

**דוגמאות לשאלות קיימות (למד מהסגנון שלהן!):**
{reference_text}

**פורמט פלט - JSON Array:**
```json
[
  {{
    "question_number": 1,
    "question_text": "טקסט השאלה המלא",
    "options": {{
      "A": "אפשרות א - טקסט מלא",
      "B": "אפשרות ב - טקסט מלא",
      "C": "אפשרות ג - טקסט מלא",
      "D": "אפשרות ד - טקסט מלא",
      "E": "אפשרות ה - טקסט מלא"
    }},
    "correct_answer": "B",
    "explanation": "הסבר מפורט מדוע התשובה הנכונה היא B, כולל הפניה למקורות משפטיים. הסבר גם למה השאר שגויות.",
    "topic": "הנושא העיקרי של השאלה",
    "difficulty": "easy/medium/hard",
    "legal_reference": "חוק ניירות ערך, תשכ\\"ח-1968, סעיף X"
  }},
  ...
]
```

**חשוב מאוד:**
1. **עברית מקצועית!** - כתוב בעברית תקנית, ברורה ומקצועית. הקפד על דקדוק, כתיב וניסוח נכון!
2. **שאלות מעורבות!** - 70-80% שאלות סיפור עם תרחישים + 20-30% שאלות בסיסיות
3. **שמות חברות בדויים בלבד!** - אסור להשתמש בגוגל, אפל, מיקרוסופט, אמזון, פייסבוק וכו'. רק שמות בדויים!
4. **בדיוק 5 אפשרויות (A, B, C, D, E)** - אסור לכתוב 4 או 6 אפשרויות! חייב להיות בדיוק 5!
5. כל שאלה חייבת להיות מדויקת משפטית ומבוססת על החוק הישראלי
6. רק תשובה אחת נכונה - השאר חייבות להיות שגויות בבירור
7. הסבר חייב להיות מפורט ולהסביר גם למה השאר שגויות
8. הפניה חוקית חייבת להיות מדויקת (חוק, סעיף)
9. נושא חייב להיות תמציתי ומדויק
10. אל תעתיק שאלות קיימות - צור שאלות חדשות בהשראתן
11. אם יש לך רק 4 רעיונות לאפשרויות, הוסף אפשרות חמישית (למשל: "כל התשובות נכונות", "אף אחד מהנ\\"ל", וכד')
12. **השתמש בשמות מגוונים**: שוקי, מוקי, דילן, ברנדה, רוני, גיא, מיכל, דנה, יוסי, תמר, אבי, נועה

צור עכשיו {question_count} שאלות איכותיות בפורמט JSON - זכור: 70-80% סיפורים, 20-30% שאלות בסיסיות!"""

        try:
            # Call thinking model with maximum context
            response = self.client.chat.completions.create(
                model=THINKING_MODEL,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": generation_prompt}
                ],
                temperature=0.7  # Creative but controlled
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            questions = self._parse_json_from_text(result_text)

            if not isinstance(questions, list):
                self.log("⚠️  LLM did not return a list, attempting to extract")
                questions = []

            return questions

        except Exception as e:
            self.log(f"❌ Error generating questions: {e}")
            return []

    def _format_reference_questions(self, questions: List[Dict]) -> str:
        """Format reference questions for prompt"""
        formatted = []
        for i, q in enumerate(questions[:5], 1):
            formatted.append(f"""
דוגמה {i}:
שאלה: {q.get('question_text', '')[:200]}...
נושא: {q.get('topic', 'לא ידוע')}
רמת קושי: {q.get('difficulty', 'medium')}
""")
        return "\n".join(formatted)

    def _validate_structure(self, questions: List[Dict]) -> List[Dict]:
        """
        Stage 1: Strict structural validation

        CRITICAL: All questions MUST have exactly 5 options (A-E)

        Args:
            questions: Generated questions

        Returns:
            Structurally valid questions only
        """
        validated = []

        for i, q in enumerate(questions, 1):
            # Check required fields
            required = ['question_text', 'options', 'correct_answer', 'explanation', 'topic']
            missing = [f for f in required if f not in q or not q[f]]

            if missing:
                self.log(f"⚠️  Q{i}: Missing fields: {missing}")
                continue

            # CRITICAL: Must have exactly 5 options (A, B, C, D, E)
            options = q.get('options', {})
            if not isinstance(options, dict):
                self.log(f"⚠️  Q{i}: Options is not a dict")
                continue

            required_options = ['A', 'B', 'C', 'D', 'E']
            missing_opts = [opt for opt in required_options if opt not in options or not str(options[opt]).strip()]
            extra_opts = [opt for opt in options.keys() if opt not in required_options]

            if missing_opts:
                self.log(f"❌ Q{i}: MISSING OPTIONS: {missing_opts} - REJECTED")
                continue

            if extra_opts:
                self.log(f"⚠️  Q{i}: Extra options: {extra_opts} - removing")
                # Keep only A-E
                q['options'] = {k: v for k, v in options.items() if k in required_options}

            if len(q['options']) != 5:
                self.log(f"❌ Q{i}: Has {len(q['options'])} options, need 5 - REJECTED")
                continue

            # Validate correct_answer is A-E
            correct = q.get('correct_answer', '').upper()
            if correct not in required_options:
                self.log(f"⚠️  Q{i}: Invalid correct answer '{correct}'")
                continue

            q['correct_answer'] = correct

            # Normalize difficulty
            if q.get('difficulty') not in ['easy', 'medium', 'hard']:
                q['difficulty'] = 'medium'

            validated.append(q)

        return validated

    def _validate_with_legal_expert(self, questions: List[Dict]) -> List[Dict]:
        """
        Stage 2: Legal Expert validation

        Tests each question with Legal Expert Agent to ensure:
        1. Legal Expert can answer correctly (question is clear)
        2. Answer matches what we think is correct
        3. Question is legally accurate
        4. Question is relevant to securities law

        This is CRITICAL for exam accuracy.

        Args:
            questions: Structurally valid questions

        Returns:
            Expert-validated questions only
        """
        validated = []

        for i, q in enumerate(questions, 1):
            self.log(f"🧪 Testing Q{i} with Legal Expert...")

            # Build validation query (don't tell correct answer)
            validation_query = f"""אתה מקבל שאלת מבחן בנושא ניירות ערך ואתיקה מקצועית.
אנא ענה על השאלה והסבר את תשובתך.

**שאלה:**
{q['question_text']}

**אפשרויות:**
A. {q['options']['A']}
B. {q['options']['B']}
C. {q['options']['C']}
D. {q['options']['D']}
E. {q['options']['E']}

**דרישות:**
1. בחר תשובה אחת נכונה (A/B/C/D/E בלבד)
2. הסבר למה זו התשובה הנכונה
3. ציין רמת ביטחון (high/medium/low)

השב בפורמט JSON:
```json
{{
  "answer": "A",
  "explanation": "הסבר מפורט...",
  "confidence": "high",
  "legal_reference": "חוק X, סעיף Y"
}}
```"""

            try:
                # Query Legal Expert using process_with_rag
                response = self.legal_expert.process_with_rag(
                    query=validation_query,
                    k=15  # Use top 15 legal chunks for accuracy
                )

                result = response.get('answer', '')

                # Debug: Show what Legal Expert returned
                if i == 1:  # Only log first question to avoid spam
                    self.log(f"📝 Legal Expert raw response (Q1): {result[:200]}...")

                # Parse response
                validation_data = self._parse_json_from_text(result)

                if not validation_data or not isinstance(validation_data, dict):
                    self.log(f"⚠️  Q{i}: Failed to parse Legal Expert response")
                    if i == 1:  # Show why it failed for first question
                        self.log(f"   Parsed data: {validation_data}")
                    continue

                agent_answer = validation_data.get('answer', '').upper()
                correct_answer = q['correct_answer'].upper()
                confidence = validation_data.get('confidence', 'low')

                # Check if Legal Expert got it right
                if agent_answer != correct_answer:
                    self.log(f"❌ Q{i}: Legal Expert answered {agent_answer}, correct is {correct_answer} - REJECTED")
                    self.log(f"   Reason: Question may be ambiguous or incorrect")
                    continue

                # Check confidence
                if confidence == 'low':
                    self.log(f"⚠️  Q{i}: Legal Expert has low confidence - REJECTED")
                    continue

                # Question passed validation!
                self.log(f"✅ Q{i}: Legal Expert validated (confidence: {confidence})")

                # Enhance explanation with Legal Expert's reasoning
                q['expert_validation'] = {
                    'validated': True,
                    'expert_explanation': validation_data.get('explanation', ''),
                    'expert_reference': validation_data.get('legal_reference', ''),
                    'confidence': confidence
                }

                validated.append(q)

            except Exception as e:
                self.log(f"❌ Q{i}: Validation error: {e}")
                continue

        return validated

    def _final_enrichment(self, questions: List[Dict]) -> List[Dict]:
        """
        Stage 3: Final enrichment and metadata

        Args:
            questions: Expert-validated questions

        Returns:
            Final enriched questions
        """
        enriched = []

        for i, q in enumerate(questions, 1):
            # Add final metadata
            q['generated'] = True
            q['question_number'] = i
            q['validated_by_expert'] = True

            enriched.append(q)

        return enriched


    def _parse_json_from_text(self, text: str):
        """Extract JSON from LLM response (handles both arrays and objects)"""
        # Try to find JSON in code blocks (array)
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to find JSON in code blocks (object)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to find JSON array without code blocks
        json_match = re.search(r'(\[.*?\])', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to find JSON object without code blocks
        json_match = re.search(r'(\{.*?\})', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try parsing entire text as JSON
        try:
            return json.loads(text)
        except:
            pass

        return None

    def _extract_legal_sources(self, context: str) -> List[str]:
        """Extract legal source references from context"""
        sources = []

        # Look for source markers in context
        parts = context.split("---")
        for part in parts[:5]:  # First 5 sources
            if "[מקור" in part:
                lines = part.strip().split("\n")
                if lines:
                    header = lines[0]
                    try:
                        doc_part = header.split("]")[1].strip()
                        sources.append(doc_part)
                    except:
                        pass

        return sources

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process quiz generation request

        Args:
            input_data: Dict with:
                - question_count: int (default: 10)
                - topic: str (optional)
                - difficulty: str (optional)
                - focus_areas: List[str] (optional)

        Returns:
            Generated quiz
        """
        question_count = input_data.get('question_count', 10)
        topic = input_data.get('topic')
        difficulty = input_data.get('difficulty')
        focus_areas = input_data.get('focus_areas')

        return self.generate_quiz(
            question_count=question_count,
            topic=topic,
            difficulty=difficulty,
            focus_areas=focus_areas
        )
