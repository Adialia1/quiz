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
       .25 בית ההשקעות "מיטב גמלא שוקי הון" השקיע מכספי ה"נוסטרו" שלו (כספים של בית ההשקעות ולא של לקוחות) בחברה ציבורית בשם "גמא-פון", שמניותיה שייווקו סולר. בית ההשקעות הינו המשקיע המוסדי הגדול ביותר בגמא-פון, והוא מחזיק כ- 15% ממניותיה, בשווי שוק כולל של כ-500 מיליון ש"ח. בימים הקרובים אמורה להתקיים הנפקה לציבור של חברת בת בשם "דלתא-פון" שאמורה להיות מתחרה חדשה בתחום שירותי הסלולר. דלתא-פון מתכננת לנצל את כספי ההנפקה לצורך מימון פריסה של אנטנות בטכנולוגיה חדישה וטובה יותר מגמא-פון, והיא צפויה לשאוב אליה מיליוני לקוחות ולכבוש את השוק בתוך זמן קצר, אם ההנפקה תצליח ורשת האנטנות החדשה תיפרס. מאד חשוב לדלתא-פון בתהליכים להנפקה לציבור, ירד שער מניותיה של גמא-פון בחדות, לאור ציפיות השוק לפגיעה בהכנסותיה. עם זאת, האנליסטים המסקרים את ההנפקה הצפויה חלוקים בדעתם לגבי הכדאיות של ההשקעה בדלתא-פון; חלקם סבור כי יתרונה של טכנולוגיית הסלולר עבר, וכי טכנולוגיות חדישות שיוצגו בתוך שנים ספורות יחליפו אותה ויהפכו את ההשקעה בתשתיות סלולר למיותרת.
ועדת ההשקעות של "מיטב גמלא שוקי הון" החליטה לא לרכוש מניות בהנפקה הקרובה של "דלתא-פון" על מנת שלא לסכן את ההשקעה של בית ההשקעות ב"גמא-פון".
סמי הינו יועץ השקעות בעל רישיון בבית ההשקעות "מיטב גמלא שוקי הון". אחד מלקוחותיו התקשר אליו על מנת להתייעץ עימו בנוגע לרכישת מניות בהנפקה המתרקבת של דלתא-פון, בסכום משמעותי.

בנסיבות המתוארות, איזה מן ההיגדים הבאים הוא הנכון ביותר?

א. סמי אינו רשאי כלל לתת ייעוץ השקעות בשיחה טלפונית, אלא אם הסכים הלקוח לקבלת הייעוץ בשיחת הטלפון שתירשם על ידו ביחס לאותה עסקה.
ב. מאחר שדעת האנליסטים חלוקות לגבי כדאיות ההנפקה, אין בסיטואציה המתוארת כל ניגוד עניינים.
ג. סמי חייב להודיע ללקוח על קיום ניגוד עניינים, והוא אינו רשאי לייעץ ללקוח לגבי כדאיות ההשקעה בדלתא-פון, אלא אם הסכים הלקוח לקבלת הייעוץ בשיחת הטלפון שתירשם על ידו ביחס לאותה עסקה.
ד. סמי חייב להודיע ללקוח, בשיחה שתירשם על ידו, על קיום ניגוד עניינים, ולאחר מכן הוא רשאי לייעץ ללקוח לגבי כדאיות ההשקעה בדלתא-פון, בין אם הלקוח הסכים למתן הייעוץ ובין אם לאו.
ה. כל ההיגדים האחרים שגויים.

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
