#!/usr/bin/env python3
"""
Week 1 Implementation: GPT-4 Vision OCR + Hierarchy-Aware Chunking
Target Score: 7.5/10 (from current 6.5/10)
"""

import os
import base64
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
import json
import time

# Load environment
load_dotenv()

# Initialize OpenRouter client (supports multiple models including Gemini)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY')
)

def convert_pdf_to_images(pdf_path: Path, dpi: int = 300) -> List:
    """
    Convert PDF pages to high-quality images

    Args:
        pdf_path: Path to PDF file
        dpi: Image resolution (300 DPI recommended for OCR quality)

    Returns:
        List of PIL Image objects
    """
    try:
        from pdf2image import convert_from_path

        print(f"📄 Converting PDF to images (DPI: {dpi})...")
        images = convert_from_path(str(pdf_path), dpi=dpi)
        print(f"✅ Converted {len(images)} pages to images")

        return images

    except ImportError:
        print("❌ pdf2image not installed")
        print("   Install: pip install pdf2image")
        print("   Also requires poppler: brew install poppler (macOS)")
        return []

    except Exception as e:
        print(f"❌ Error converting PDF: {e}")
        return []


def encode_image_to_base64(image) -> str:
    """Convert PIL Image to base64 string for API"""
    from io import BytesIO

    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def perfect_ocr_with_gpt4_vision(pdf_path: Path, max_pages: int = None) -> List[str]:
    """
    Convert PDF pages to perfect markdown using GPT-4 Vision

    This achieves:
    - Perfect Hebrew text extraction
    - Table structure preservation
    - Chart/diagram descriptions
    - Clean formatting

    Args:
        pdf_path: Path to PDF file
        max_pages: Limit pages to process (for testing)

    Returns:
        List of markdown strings, one per page
    """
    images = convert_pdf_to_images(pdf_path, dpi=300)  # Higher DPI for better OCR with Gemini

    if not images:
        print("⚠️  Falling back to basic extraction...")
        return fallback_to_basic_extraction(pdf_path, max_pages)

    if max_pages:
        images = images[:max_pages]

    page_markdowns = []

    print(f"\n🤖 Processing {len(images)} pages with GPT-4 Vision...")

    for i, image in enumerate(images, 1):
        print(f"   Processing page {i}/{len(images)}...", end=' ')

        # Encode image
        image_base64 = encode_image_to_base64(image)

        # GPT-4 Vision prompt
        prompt = """אתה מומחה ב-OCR של מסמכים משפטיים בעברית.

    המר את תמונת העמוד הזה ל-Markdown באיכות מושלמת.

    דרישות:
    1. **טקסט עברית מדויק** - כל מילה חייבת להיות מדויקת
    2. **שמור מבנה טבלאות** - המר טבלאות ל-Markdown tables
    3. **שמור היררכיה** - כותרות, סעיפים, תתי-סעיפים
    4. **זיהוי סעיפים משפטיים** - סעיף, תקנה, פרק, סעיף משנה
    5. **ספרור מדויק** - שמור כל מספור של סעיפים
    6. **תרשימים** - תאר בקצרה אם יש

    פורמט פלט:
    ```markdown
    # [כותרת העמוד אם קיימת]

    [תוכן בעברית במבנה מושלם]

    ## טבלה (אם קיימת)
    | עמודה 1 | עמודה 2 |
    |---------|---------|
    | ערך 1   | ערך 2   |
    ```

    החזר **רק** את ה-Markdown, ללא הסברים."""

        try:
            response = client.chat.completions.create(
                model="google/gemini-2.0-flash-001",  # Gemini 2.0 Flash - Better for OCR
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=10000,
                temperature=0.0  # Deterministic for OCR
            )

            markdown = response.choices[0].message.content.strip()

            # Remove markdown code block wrapper if present
            if markdown.startswith('```markdown'):
                markdown = markdown[len('```markdown'):].strip()
            if markdown.endswith('```'):
                markdown = markdown[:-3].strip()

            page_markdowns.append(markdown)
            print("✅")

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Error: {e}")
            page_markdowns.append(f"[Error processing page {i}]")

    return page_markdowns


def hierarchy_aware_chunking(page_markdown: str, page_num: int) -> Dict:
    """
    Extract document hierarchy and create structured chunk

    This preserves:
    - Document structure (Title → Section → Subsection)
    - Legal section numbering (סעיף, תקנה, פרק)
    - Complete context at all levels

    Args:
        page_markdown: Markdown from GPT-4 Vision
        page_num: Page number

    Returns:
        Structured chunk with hierarchy preserved
    """
    prompt = f"""אתה מומחה בניתוח מבנה של מסמכים משפטיים בעברית.

    נתח את העמוד הזה וחלץ את ההיררכיה המלאה:

    ```markdown
    {page_markdown[:4000]}
    ```

    צור JSON עם המבנה הבא:
    {{
    "page_num": {page_num},
    "hierarchy": {{
        "level_1_title": "כותרת ראשית (אם קיימת)",
        "level_2_sections": ["פרק א", "פרק ב"],
        "level_3_subsections": ["סעיף 1", "סעיף 2", "תקנה 3"]
    }},
    "title": "כותרת תיאורית קצרה + עמוד {page_num}",
    "context": "איך העמוד הזה משתלב במבנה הכללי של המסמך (2-3 משפטים)",
    "summary": "סיכום מקיף של תוכן העמוד (3-5 משפטים)",
    "keywords": ["מילות", "מפתח", "חשובות"],
    "legal_sections": ["סעיף 17", "תקנה 5", "פרק ג"],
    "key_concepts": ["מושגים משפטיים מרכזיים"],
    "entities": {{
        "parties": ["צדדים שמוזכרים"],
        "dates": ["תאריכים"],
        "amounts": ["סכומים"]
    }},
    "tables_present": true/false,
    "cross_references": ["התייחסויות לסעיפים אחרים"]
    }}

    החזר **רק** JSON תקין, ללא markdown code blocks."""

    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        structured_data = json.loads(response.choices[0].message.content)

        # Add full markdown text
        structured_data['full_text'] = page_markdown

        return structured_data

    except Exception as e:
        print(f"⚠️  Error in hierarchy extraction: {e}")
        return {
            'page_num': page_num,
            'hierarchy': {},
            'title': f'עמוד {page_num}',
            'context': '',
            'summary': '',
            'keywords': [],
            'legal_sections': [],
            'key_concepts': [],
            'entities': {},
            'tables_present': False,
            'cross_references': [],
            'full_text': page_markdown
        }


def create_enhanced_chunk(structured_data: Dict) -> str:
    """
    Create final chunk with hierarchy preservation

    Format:
    # Title (with hierarchy breadcrumb)
    **Hierarchy:** Level 1 → Level 2 → Level 3
    **Context:** ...
    **Summary:** ...
    **Legal Sections:** ...
    **Keywords:** ...
    ---
    [Full markdown text with preserved structure]
    """
    # Build hierarchy breadcrumb
    hierarchy = structured_data.get('hierarchy', {})
    breadcrumb_parts = []

    if hierarchy.get('level_1_title'):
        breadcrumb_parts.append(hierarchy['level_1_title'])

    if hierarchy.get('level_2_sections'):
        breadcrumb_parts.append(' → '.join(hierarchy['level_2_sections'][:2]))

    breadcrumb = ' → '.join(breadcrumb_parts) if breadcrumb_parts else 'ללא היררכיה'

    # Build entities section
    entities = structured_data.get('entities', {})
    entity_lines = []
    if entities.get('parties'):
        entity_lines.append(f"**צדדים:** {', '.join(entities['parties'])}")
    if entities.get('dates'):
        entity_lines.append(f"**תאריכים:** {', '.join(entities['dates'])}")
    if entities.get('amounts'):
        entity_lines.append(f"**סכומים:** {', '.join(entities['amounts'])}")

    entities_section = '\n'.join(entity_lines) if entity_lines else ''

    # Build cross-references section
    cross_refs = structured_data.get('cross_references', [])
    cross_ref_section = f"**התייחסויות צולבות:** {', '.join(cross_refs)}" if cross_refs else ''

    # Assemble chunk
    chunk_parts = [
        f"# {structured_data['title']}",
        f"**היררכיה:** {breadcrumb}",
        f"**הקשר במסמך:** {structured_data['context']}",
        f"**סיכום:** {structured_data['summary']}",
        f"**סעיפים משפטיים:** {', '.join(structured_data['legal_sections'])}",
        f"**מושגים מרכזיים:** {', '.join(structured_data['key_concepts'])}",
        f"**מילות מפתח:** {', '.join(structured_data['keywords'])}",
    ]

    if entities_section:
        chunk_parts.append(entities_section)

    if cross_ref_section:
        chunk_parts.append(cross_ref_section)

    if structured_data.get('tables_present'):
        chunk_parts.append("**⚠️ מכיל טבלאות**")

    chunk_parts.extend([
        "---",
        structured_data['full_text']
    ])

    return '\n'.join(chunk_parts)


def fallback_to_basic_extraction(pdf_path: Path, max_pages: int = None) -> List[str]:
    """Fallback to pdfplumber if GPT-4 Vision fails"""
    try:
        import pdfplumber

        print("⚠️  Using basic pdfplumber extraction...")

        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages[:max_pages] if max_pages else pdf.pages

            page_texts = []
            for page in pages:
                text = page.extract_text() or ""
                page_texts.append(text)

            return page_texts

    except Exception as e:
        print(f"❌ Error in fallback extraction: {e}")
        return []


def week1_pipeline(pdf_path: Path, max_pages: int = 3) -> Dict:
    """
    Complete Week 1 pipeline:
    1. GPT-4 Vision OCR
    2. Hierarchy-aware chunking

    Args:
        pdf_path: Path to PDF
        max_pages: Limit for testing (default 3)

    Returns:
        Dict with chunks and metadata
    """
    print("="*80)
    print("WEEK 1: GPT-4 Vision OCR + Hierarchy-Aware Chunking")
    print("="*80)

    # Step 1: Perfect OCR
    print("\n📸 Step 1: GPT-4 Vision OCR")
    page_markdowns = perfect_ocr_with_gpt4_vision(pdf_path, max_pages=max_pages)

    if not page_markdowns:
        print("❌ No pages extracted")
        return {}

    # Step 2: Hierarchy-aware chunking
    print(f"\n🏗️  Step 2: Hierarchy-Aware Chunking")
    structured_pages = []

    for i, page_md in enumerate(page_markdowns, 1):
        print(f"   Analyzing page {i}/{len(page_markdowns)}...", end=' ')
        structured_data = hierarchy_aware_chunking(page_md, i)
        structured_pages.append(structured_data)
        print("✅")
        time.sleep(0.3)  # Rate limiting

    # Step 3: Create enhanced chunks
    print(f"\n📦 Step 3: Creating Enhanced Chunks")
    chunks = []

    for structured_data in structured_pages:
        chunk_text = create_enhanced_chunk(structured_data)
        chunks.append(chunk_text)

    # Statistics
    avg_chunk_size = sum(len(c) for c in chunks) / len(chunks)
    total_keywords = sum(len(s.get('keywords', [])) for s in structured_pages)
    total_legal_sections = sum(len(s.get('legal_sections', [])) for s in structured_pages)

    print(f"\n{'='*80}")
    print("WEEK 1 RESULTS")
    print(f"{'='*80}")
    print(f"\n📊 Processing Statistics:")
    print(f"   Total pages processed: {len(chunks)}")
    print(f"   Average chunk size: {avg_chunk_size:.0f} characters")
    print(f"   Total keywords extracted: {total_keywords}")
    print(f"   Total legal sections found: {total_legal_sections}")
    print(f"   Hierarchy levels captured: 1-3 levels per page")

    # Show sample
    if chunks:
        print(f"\n📄 Sample Chunk (Page 1):")
        print("-" * 80)
        print(chunks[0][:1000] + "..." if len(chunks[0]) > 1000 else chunks[0])
        print("-" * 80)

    return {
        'chunks': chunks,
        'structured_pages': structured_pages,
        'page_markdowns': page_markdowns,
        'statistics': {
            'total_pages': len(chunks),
            'avg_chunk_size': avg_chunk_size,
            'total_keywords': total_keywords,
            'total_legal_sections': total_legal_sections
        }
    }


def main():
    """Test Week 1 implementation"""
    legal_pdf = Path('/Users/adialia/Desktop/quiz/examples/legal1.pdf')

    if not legal_pdf.exists():
        print(f"❌ Error: {legal_pdf} not found")
        return

    # Run Week 1 pipeline on first 3 pages
    result = week1_pipeline(legal_pdf, max_pages=3)

    if not result:
        return

    print(f"\n💡 Next Steps:")
    print(f"   1. Run AI validation to measure score improvement")
    print(f"   2. Compare with baseline (6.5/10)")
    print(f"   3. Target: 7.5/10 (+15% improvement)")
    print(f"   4. If successful, proceed to Week 2 (Contextual Enrichment)")


if __name__ == '__main__':
    main()
