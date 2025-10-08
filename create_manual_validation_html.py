#!/usr/bin/env python3
"""
Create HTML file for manual validation
Shows original page images alongside chunks for easy visual comparison
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from rag import week1_pipeline
from pdf2image import convert_from_path

load_dotenv()


def create_validation_html(pdf_path: Path, max_pages: int = 3):
    """
    Create HTML file with:
    - Original page images (screenshots of PDF)
    - Chunked text output
    - Side-by-side comparison

    Args:
        pdf_path: Path to PDF file
        max_pages: Number of pages to process
    """

    print("="*80)
    print("CREATING MANUAL VALIDATION HTML")
    print("="*80)

    # Step 1: Convert PDF to images
    print(f"\n📄 Converting PDF pages to images...")
    images = convert_from_path(str(pdf_path), dpi=300, first_page=1, last_page=max_pages)

    # Save images
    image_dir = Path('validation_images')
    image_dir.mkdir(exist_ok=True)

    image_paths = []
    for i, image in enumerate(images, 1):
        img_path = image_dir / f'page_{i}.png'
        image.save(img_path, 'PNG')
        image_paths.append(img_path)
        print(f"   ✅ Saved page {i} image")

    # Step 2: Run chunking pipeline
    print(f"\n🔄 Running Week 1 chunking pipeline with Gemini 2.0...")
    result = week1_pipeline(pdf_path, max_pages=max_pages)
    chunks = result.get('chunks', [])
    metadata_list = result.get('structured_pages', [])

    # Step 3: Create HTML
    print(f"\n🌐 Creating HTML validation file...")

    html_content = f"""
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manual Chunk Validation - Gemini 2.0 OCR</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            margin: 15px 0 0 0;
            opacity: 0.95;
            font-size: 16px;
        }}
        .stats {{
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-label {{
            font-size: 12px;
            opacity: 0.9;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }}
        .comparison {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        }}
        .page-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            font-size: 22px;
            font-weight: bold;
        }}
        .side-by-side {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 20px;
        }}
        .original-section, .chunk-section {{
            padding: 20px;
            border-radius: 8px;
        }}
        .original-section {{
            background: #fff9e6;
            border: 2px solid #ffd700;
        }}
        .chunk-section {{
            background: #e6f7ff;
            border: 2px solid #1890ff;
        }}
        .section-title {{
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid rgba(0,0,0,0.1);
        }}
        .pdf-image {{
            width: 100%;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-top: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .chunk-text {{
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.8;
            direction: rtl;
            text-align: right;
            max-height: 700px;
            overflow-y: auto;
            border: 2px solid #e8e8e8;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }}
        .metadata {{
            background: linear-gradient(135deg, #e0f7fa 0%, #e1f5fe 100%);
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            border-right: 5px solid #00bcd4;
        }}
        .metadata-item {{
            margin: 12px 0;
            font-size: 14px;
        }}
        .metadata-label {{
            font-weight: bold;
            color: #00838f;
        }}
        .validation-section {{
            background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%);
            padding: 25px;
            border-radius: 8px;
            margin-top: 25px;
            border: 3px solid #8bc34a;
        }}
        .validation-title {{
            font-weight: bold;
            color: #558b2f;
            font-size: 20px;
            margin-bottom: 20px;
        }}
        .checklist {{
            list-style: none;
            padding: 0;
        }}
        .checklist li {{
            padding: 12px 15px;
            background: white;
            margin: 8px 0;
            border-radius: 6px;
            border-right: 4px solid #8bc34a;
        }}
        .checklist li:before {{
            content: "☐ ";
            margin-left: 10px;
            font-size: 20px;
            color: #8bc34a;
        }}
        .rating {{
            margin-top: 20px;
            padding: 20px;
            background: white;
            border-radius: 8px;
        }}
        .rating-label {{
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 16px;
        }}
        .rating-buttons {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .rating-btn {{
            padding: 12px 20px;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
        }}
        .rating-btn:hover {{
            background: #f5f5f5;
            transform: scale(1.05);
        }}
        .rating-btn.selected {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
        }}
        .summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-top: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        @media (max-width: 768px) {{
            .side-by-side {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 אימות ידני של Chunks - Gemini 2.0 Flash</h1>
        <p>השווה את העמודים המקוריים עם ה-chunks שנוצרו באמצעות Gemini 2.0 OCR</p>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-label">מספר עמודים</div>
                <div class="stat-value">{max_pages}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">סה"כ Chunks</div>
                <div class="stat-value">{len(chunks)}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">ממוצע גודל Chunk</div>
                <div class="stat-value">{sum(len(c) for c in chunks) // len(chunks) if chunks else 0:,}</div>
            </div>
        </div>
    </div>
"""

    # Add page comparisons
    for i, (chunk, structured, img_path) in enumerate(zip(chunks, metadata_list, image_paths), 1):
        keywords_str = ', '.join(structured.get('keywords', [])[:10]) if isinstance(structured.get('keywords'), list) else 'לא נמצאו'
        legal_sections_str = ', '.join(structured.get('legal_sections', [])[:10]) if isinstance(structured.get('legal_sections'), list) else 'לא נמצאו'
        key_concepts_str = ', '.join(structured.get('key_concepts', [])[:10]) if isinstance(structured.get('key_concepts'), list) else 'לא נמצאו'

        html_content += f"""
    <div class="comparison">
        <div class="page-header">📄 עמוד {i} מתוך {max_pages}</div>

        <div class="side-by-side">
            <div class="original-section">
                <div class="section-title">📄 עמוד מקורי (PDF)</div>
                <img src="{img_path}" class="pdf-image" alt="Page {i}">
            </div>

            <div class="chunk-section">
                <div class="section-title">✨ Chunk שנוצר (Gemini 2.0)</div>
                <div class="chunk-text">{chunk}</div>
                <div style="margin-top: 15px; font-size: 13px; color: #666; text-align: center;">
                    📏 גודל: <strong>{len(chunk):,}</strong> תווים
                </div>

                <div class="metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">🏷️ כותרת:</span> {structured.get('title', 'ללא כותרת')}
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">🔑 מילות מפתח:</span> {keywords_str}
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">⚖️ סעיפים משפטיים:</span> {legal_sections_str}
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">💡 מושגים מרכזיים:</span> {key_concepts_str}
                    </div>
                </div>
            </div>
        </div>

        <div class="validation-section">
            <div class="validation-title">✅ שאלות לבדיקה ידנית</div>
            <ul class="checklist">
                <li>הטקסט בעברית קריא ונכון? (ללא (cid:) או שיבושים)</li>
                <li>הטבלאות והמבנה נשמרו באופן מלא?</li>
                <li>הסעיפים המשפטיים זוהו נכון?</li>
                <li>המטא-דאטה (מילות מפתח, מושגים) מדויקת ורלוונטית?</li>
                <li>ה-chunk יהיה שימושי ל-RAG retrieval?</li>
            </ul>

            <div class="rating">
                <div class="rating-label">דרג את איכות ה-chunk הזה:</div>
                <div class="rating-buttons">
                    <button class="rating-btn" onclick="rate({i}, 1)">1</button>
                    <button class="rating-btn" onclick="rate({i}, 2)">2</button>
                    <button class="rating-btn" onclick="rate({i}, 3)">3</button>
                    <button class="rating-btn" onclick="rate({i}, 4)">4</button>
                    <button class="rating-btn" onclick="rate({i}, 5)">5</button>
                    <button class="rating-btn" onclick="rate({i}, 6)">6</button>
                    <button class="rating-btn" onclick="rate({i}, 7)">7</button>
                    <button class="rating-btn" onclick="rate({i}, 8)">8</button>
                    <button class="rating-btn" onclick="rate({i}, 9)">9</button>
                    <button class="rating-btn" onclick="rate({i}, 10)">10</button>
                </div>
                <div id="score-{i}" style="margin-top: 15px; font-weight: bold; color: #667eea; font-size: 16px;"></div>
            </div>
        </div>
    </div>
"""

    # Add summary and JavaScript
    total_keywords = sum(len(s.get('keywords', [])) for s in metadata_list if isinstance(s.get('keywords'), list))
    total_legal = sum(len(s.get('legal_sections', [])) for s in metadata_list if isinstance(s.get('legal_sections'), list))

    html_content += f"""
    <div class="summary">
        <h2>📊 סיכום תוצאות</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
                <div style="font-size: 14px; opacity: 0.9;">סה"כ Chunks</div>
                <div style="font-size: 28px; font-weight: bold;">{len(chunks)}</div>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
                <div style="font-size: 14px; opacity: 0.9;">ממוצע גודל</div>
                <div style="font-size: 28px; font-weight: bold;">{sum(len(c) for c in chunks) // len(chunks):,} תווים</div>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
                <div style="font-size: 14px; opacity: 0.9;">סה"כ מילות מפתח</div>
                <div style="font-size: 28px; font-weight: bold;">{total_keywords}</div>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
                <div style="font-size: 14px; opacity: 0.9;">סה"כ סעיפים משפטיים</div>
                <div style="font-size: 28px; font-weight: bold;">{total_legal}</div>
            </div>
        </div>
        <div id="average-score" style="margin-top: 25px; font-size: 20px; text-align: center; padding: 20px; background: rgba(255,255,255,0.2); border-radius: 8px;"></div>
    </div>

    <script>
        const ratings = {{}};

        function rate(page, score) {{
            ratings[page] = score;

            // Update UI
            const container = document.querySelectorAll(`#score-${{page}}`)[0].parentElement;
            container.querySelectorAll('.rating-btn').forEach(btn => {{
                btn.classList.remove('selected');
            }});
            event.target.classList.add('selected');

            document.getElementById(`score-${{page}}`).innerHTML = `✅ הציון שלך: ${{score}}/10`;

            // Calculate average
            const scores = Object.values(ratings);
            if (scores.length > 0) {{
                const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
                const percentage = (avg / 10 * 100).toFixed(0);
                let emoji = '🎯';
                if (avg >= 9) emoji = '🌟';
                else if (avg >= 7) emoji = '✅';
                else if (avg >= 5) emoji = '⚠️';
                else emoji = '❌';

                document.getElementById('average-score').innerHTML =
                    `${{emoji}} <strong>ממוצע הציונים שלך: ${{avg.toFixed(1)}}/10</strong> (${{percentage}}%) | בדקת ${{scores.length}} מתוך {len(chunks)} chunks`;
            }}
        }}
    </script>
</body>
</html>
"""

    # Save HTML file
    html_file = Path('manual_validation.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ HTML validation file created: {html_file}")
    print(f"✅ Page images saved in: {image_dir}")

    return html_file


def main():
    """Create manual validation HTML"""

    legal_pdf = Path('examples/legal3.pdf')

    if not legal_pdf.exists():
        print(f"❌ Error: {legal_pdf} not found")
        return

    print("\n📋 How many pages to validate?")
    try:
        max_pages = int(input("Enter number (1-10, default 3): ").strip() or "3")
        max_pages = min(max(1, max_pages), 10)
    except:
        max_pages = 3

    html_file = create_validation_html(legal_pdf, max_pages=max_pages)

    print("\n" + "="*80)
    print(f"MANUAL VALIDATION READY!")
    print("="*80)
    print(f"\n🌐 Open this file in your browser:")
    print(f"   {html_file.absolute()}")
    print(f"\n📖 Instructions:")
    print(f"   1. Open {html_file} in Chrome/Safari/Firefox")
    print(f"   2. Compare original PDF images with chunks")
    print(f"   3. Check the validation questions")
    print(f"   4. Rate each chunk 1-10")
    print(f"   5. See your average score at the bottom")
    print(f"\n🎯 What to Look For:")
    print(f"   ✅ Clean Hebrew text (no CID errors)")
    print(f"   ✅ Complete content extraction")
    print(f"   ✅ Accurate legal section identification")
    print(f"   ✅ Useful metadata for RAG")
    print(f"   ✅ Proper structure preservation")

    # Try to open in browser
    import webbrowser
    print(f"\n🚀 Opening in browser...")
    webbrowser.open(f'file://{html_file.absolute()}')


if __name__ == '__main__':
    main()
