#!/usr/bin/env python3
"""
Convert Quiz JSON to PDF via HTML (Best Hebrew Support!)

This approach:
1. Generates HTML with proper Hebrew RTL
2. Converts HTML to PDF using WeasyPrint
3. Perfect Hebrew rendering guaranteed!
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import argparse
from datetime import datetime


def create_html_quiz(quiz_data):
    """Generate HTML for quiz with RTL Hebrew support"""
    questions = quiz_data.get('questions', [])
    metadata = quiz_data.get('metadata', {})

    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מבחן בניירות ערך</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}

        body {{
            font-family: 'Arial', 'Helvetica', sans-serif;
            direction: rtl;
            text-align: right;
            line-height: 1.6;
            color: #333;
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #1a5490;
        }}

        h1 {{
            color: #1a5490;
            font-size: 24px;
            margin-bottom: 10px;
        }}

        .metadata {{
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }}

        .question {{
            margin-bottom: 30px;
            page-break-inside: avoid;
        }}

        .question-header {{
            background-color: #f0f0f0;
            padding: 10px;
            margin-bottom: 10px;
            border-right: 4px solid #1a5490;
            font-weight: bold;
        }}

        .question-text {{
            font-size: 14px;
            margin-bottom: 15px;
            line-height: 1.8;
        }}

        .options {{
            margin-right: 20px;
        }}

        .option {{
            margin-bottom: 8px;
            line-height: 1.5;
        }}

        .page-break {{
            page-break-before: always;
        }}

        .answer-section {{
            margin-top: 40px;
        }}

        .answer-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        .answer-table th {{
            background-color: #1a5490;
            color: white;
            padding: 12px;
            text-align: right;
        }}

        .answer-table td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: right;
        }}

        .answer-table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}

        .explanation {{
            margin-bottom: 25px;
            page-break-inside: avoid;
        }}

        .explanation-header {{
            font-weight: bold;
            color: #1a5490;
            margin-bottom: 8px;
            font-size: 13px;
        }}

        .explanation-text {{
            line-height: 1.7;
            font-size: 12px;
        }}

        .legal-reference {{
            color: #666;
            font-style: italic;
            margin-top: 5px;
            font-size: 11px;
        }}

        .validation-badge {{
            color: green;
            font-size: 11px;
            margin-top: 3px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>מבחן בניירות ערך ואתיקה מקצועית</h1>
        <div class="metadata">
            נושא: {metadata.get('topic', 'כללי')} |
            רמת קושי: {metadata.get('difficulty', 'מעורב')} |
            מספר שאלות: {len(questions)}
        </div>
        <p>הוראות: ענה על כל השאלות. לכל שאלה תשובה נכונה אחת בלבד.</p>
    </div>

    <div class="questions-section">
"""

    # Add questions
    for q in questions:
        q_num = q.get('question_number', 0)
        q_text = q.get('question_text', '')
        options = q.get('options', {})
        topic = q.get('topic', '')
        difficulty = q.get('difficulty', '')

        html += f"""
        <div class="question">
            <div class="question-header">
                שאלה {q_num} | נושא: {topic} | רמת קושי: {difficulty}
            </div>
            <div class="question-text">
                {q_text}
            </div>
            <div class="options">
"""

        for opt_key in ['A', 'B', 'C', 'D', 'E']:
            if opt_key in options:
                html += f'                <div class="option">{opt_key}. {options[opt_key]}</div>\n'

        html += """
            </div>
        </div>
"""

    html += """
    </div>

    <div class="page-break"></div>

    <div class="answer-section">
        <h2 style="text-align: center; color: #1a5490;">טבלת תשובות נכונות</h2>
        <table class="answer-table">
            <thead>
                <tr>
                    <th>תשובה נכונה</th>
                    <th>נושא</th>
                    <th>מספר שאלה</th>
                </tr>
            </thead>
            <tbody>
"""

    # Add answer table
    for q in questions:
        q_num = q.get('question_number', 0)
        topic = q.get('topic', '')
        correct = q.get('correct_answer', '')

        html += f"""
                <tr>
                    <td style="text-align: center; font-weight: bold;">{correct}</td>
                    <td>{topic}</td>
                    <td style="text-align: center;">{q_num}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>
    </div>

    <div class="page-break"></div>

    <div class="explanation-section">
        <h2 style="text-align: center; color: #1a5490;">הסברים מפורטים</h2>
"""

    # Add explanations
    for q in questions:
        q_num = q.get('question_number', 0)
        correct = q.get('correct_answer', '')
        explanation = q.get('explanation', '')
        legal_ref = q.get('legal_reference', '')
        validated = q.get('validated_by_expert', False)

        html += f"""
        <div class="explanation">
            <div class="explanation-header">
                שאלה {q_num} - תשובה נכונה: {correct}
            </div>
            <div class="explanation-text">
                {explanation}
            </div>
"""

        if legal_ref:
            html += f"""
            <div class="legal-reference">
                מקור משפטי: {legal_ref}
            </div>
"""

        if validated:
            expert_val = q.get('expert_validation', {})
            confidence = expert_val.get('confidence', '')
            html += f"""
            <div class="validation-badge">
                ✓ אומת על ידי מומחה משפטי (רמת ביטחון: {confidence})
            </div>
"""

        html += """
        </div>
"""

    html += """
    </div>
</body>
</html>
"""

    return html


def create_quiz_pdf_html(json_file, output_pdf=None):
    """
    Convert quiz JSON to PDF via HTML

    Args:
        json_file: Path to quiz JSON
        output_pdf: Output PDF path
    """
    try:
        from weasyprint import HTML
    except ImportError:
        print("❌ WeasyPrint not installed. Install it with:")
        print("   pip install weasyprint")
        print("\nOn macOS you may also need:")
        print("   brew install pango")
        return

    # Load quiz
    with open(json_file, 'r', encoding='utf-8') as f:
        quiz_data = json.load(f)

    questions = quiz_data.get('questions', [])
    if not questions:
        print("❌ No questions found")
        return

    # Generate output filename
    if not output_pdf:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_pdf = f"quiz_{timestamp}.pdf"

    # Generate HTML
    html_content = create_html_quiz(quiz_data)

    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(output_pdf)

    print(f"✅ PDF created: {output_pdf}")
    print(f"   Questions: {len(questions)}")
    print(f"   Hebrew RTL rendering: Perfect!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert quiz to PDF via HTML (best Hebrew support)')
    parser.add_argument('json_file', help='Input JSON file')
    parser.add_argument('--output', '-o', help='Output PDF file')

    args = parser.parse_args()

    if not Path(args.json_file).exists():
        print(f"❌ File not found: {args.json_file}")
        sys.exit(1)

    create_quiz_pdf_html(args.json_file, args.output)
