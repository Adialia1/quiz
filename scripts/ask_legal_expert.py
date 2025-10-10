#!/usr/bin/env python
"""
Ask Legal Expert Agent
Simple script to ask predefined questions to Legal Expert Agent
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents import LegalExpertAgent


def print_answer(question, result):
    """Print formatted answer"""
    print("\n" + "="*80)
    print(f"❓ Question: {question}")
    print("="*80)

    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        return

    print(f"\n📝 Answer:\n")
    print(result['answer'])

    if result.get('sources'):
        print("\n" + "─"*80)
        print("📚 Legal Sources:")
        print("─"*80)
        for i, source in enumerate(result['sources'][:5], 1):
            print(f"  [{i}] {source['document']} (עמוד {source['page']})")
        if len(result['sources']) > 5:
            print(f"  ... and {len(result['sources']) - 5} more sources")

    print("="*80)


def main():
    """Main function"""
    print("\n🤖 AI Ethica - Legal Expert Agent")
    print("="*80)

    # Initialize Legal Expert Agent
    print("\n🔧 Initializing Legal Expert Agent...")

    # use_thinking_model=True uses stronger reasoning model (Gemini 2.5 Pro)
    # Good for: complex questions, multi-part analysis, reasoning tasks
    agent = LegalExpertAgent(top_k=15, use_thinking_model=True)

    print("✅ Ready!\n")

    # ============================================================
    # YOUR QUESTIONS HERE - Add or modify as needed
    # ============================================================

    questions = [
        """
        מגנזיום" בע"מ הינה חברה פרטית המבצעת השקעות בחברות שונות בתחומים מגוונים. מגנזיום ניהלה בחודשים האחרונים משא-ומתן עם החברה הציבורית "וולף" בע"מ,
שמניותיה נסחרות בבורסה לניירות ערך בתל אביב. וולף מייצרת ומוכרת מעילי פרווה ברשת חנויות ."WOLF" וולף ומגנזיום היו קרובות לחתימת הסכם לביצוע המיזם המשותף הבא: מגנזיום תנצל את הקשרים והידע שלה בתחום הנדל"ן והמימון במזרח אירופה ותסייע לוולף לפתוח חנויות WOLF במזרח אירופה. מגנזיום תקבל אופציה לרכוש עד 10% מוולף.
ימים ספורים לפני החתימה על ההסכם התקשר ניר, המשמש כסמנכ"ל וכדירקטור בחברת מגנזיום ומכיר את פרטי העיסקה, אל מנהל תיק ההשקעות הפרטי שלו, אורן, היודע מה תפקידו של ניר. ניר התלבט לגבי התועלת שתצמח למגנזיום מן המיזם והתנאים העומדים להיחתם עם וולף ולכן רצה לשמוע את דעתו של אורן, אותה החשיב מאוד. אורן הקשיב לתיאור העיסקה ובסוף השיחה אמר לניר: "נשמע לי שזה כיוון מעניין מאוד, יש כאן סיכון נמוך עם סיכוי סביר להצליח, אני הייתי עושה את העיסקה." ניר השיב "תודה אחי, תמיד טוב לשמוע ממך עצה טובה."
בשעות שלאחר סיום שיחת הטלפון רכש אורן מניות של וולף לתיקים של הלקוחות שלו. בנוסף, התקשר אורן אל דניאלה, עימה הוא מצוי בקשר רומנטי, ואמר לה: "כדאי לך לקנות מניות של חברת וולף, שמעתי ממישהו בחברה שהולכת להיות שם עיסקה מעולה שתתפרסם בשוק מחרתיים."
דניאלה רכשה מניות של וולף בסך 9,900 ש"ח. יומיים לאחר מכן דיווחה וולף אודות העיסקה ושער המניה שלה עלה באופן מיידי ב- 10% . דניאלה נתנה את הוראת המכירה למניות בתוך 25 דקות מן הדיווח על ידי וולף והוראת המכירה בוצעה עד סוף יום המסחר.
בנסיבות המתוארות, איזה מההיגדים הבאים הוא הנכון ביותר?


ניר לא עבר עבירה של שימוש במידע פנים, משום שהוא אינו איש פנים בחברת וולף,
אלא משמש כדירקטור ונושא-משרה בחברת מגנזיום, שהינה חברה פרטית.
.א
ניר לא עבר עבירה של שימוש במידע פנים, משום שלא היתה לו כל כוונת רווח אישית
בעת שהתייעץ עם אורן לגבי ביצוע העיסקה.
.ב
מאחר שניר אינו איש פנים בחברת וולף, אורן לא עבר עבירה של שימוש במידע פנים.
.ג
ניר ביצע שימוש במידע פנים בכך שנועץ עם אורן, שהיה פעיל בשוק ההון.
.ד
ניר עבר עבירה של שימוש במידע פנים, משום שהרוויח רווח כספי ישיר מן ההתייעצות
עם אורן.
.ה


תחזירי לי תשובה של לפי התשובות שננתי
""",
    ]

    # ============================================================
    # Process each question
    # ============================================================

    for i, question in enumerate(questions, 1):
        print(f"\n{'🔹'*40}")
        print(f"Question {i}/{len(questions)}")
        print(f"{'🔹'*40}")

        result = agent.process({
            "query": question,
            "k": 15  # Number of legal chunks to retrieve
        })

        print_answer(question, result)

    print("\n✅ All questions processed!\n")


if __name__ == "__main__":
    main()
