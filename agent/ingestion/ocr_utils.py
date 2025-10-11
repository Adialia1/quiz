"""
OCR utilities for converting PDFs to markdown using Gemini 2.0 Flash
Ported from test_semantic_chunking_colab.ipynb
"""
import os
import base64
import time
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from pdf2image import convert_from_path
from openai import OpenAI

import sys
sys.path.append(str(Path(__file__).parent.parent))

from agent.config.settings import (
    OPENROUTER_API_KEY,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
    OCR_DPI,
    OCR_MAX_PAGES,
    OCR_RATE_LIMIT_DELAY
)

class GeminiOCR:
    """OCR processor using Gemini 2.0 Flash via OpenRouter"""

    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )

        # Hebrew-optimized OCR prompt
        self.ocr_prompt = """אתה מומחה ב-OCR של מסמכים משפטיים בעברית.

המר את תמונת העמוד הזה ל-Markdown באיכות מושלמת.

דרישות:
1. **טקסט עברית מדויק** - כל מילה חייבת להיות מדויקת
2. **שמור מבנה טבלאות** - המר טבלאות ל-Markdown tables
3. **שמור היררכיה** - כותרות, סעיפים, תתי-סעיפים
4. **זיהוי סעיפים משפטיים** - סעיף, תקנה, פרק, סעיף משנה
5. **ספרור מדויק** - שמור כל מספור של סעיפים

החזר **רק** את ה-Markdown, ללא הסברים."""

    def pdf_to_markdown(
        self,
        pdf_path: str,
        max_pages: Optional[int] = OCR_MAX_PAGES,
        verbose: bool = True
    ) -> List[str]:
        """
        Convert PDF to markdown using Gemini 2.0 Flash

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process (None = all)
            verbose: Print progress messages

        Returns:
            List of markdown strings (one per page)
        """
        if verbose:
            print(f"\n🔄 Converting PDF to images ({OCR_DPI} DPI)...")

        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=OCR_DPI)

        if max_pages:
            images = images[:max_pages]

        if verbose:
            print(f"✅ Processing {len(images)} pages with {GEMINI_MODEL}...\n")

        page_markdowns = []

        for i, image in enumerate(images, 1):
            if verbose:
                print(f"   Page {i}/{len(images)}...", end=' ')

            try:
                # Convert image to base64
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

                # Call Gemini OCR
                response = self.client.chat.completions.create(
                    model=GEMINI_MODEL,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.ocr_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }],
                    max_tokens=GEMINI_MAX_TOKENS,
                    temperature=GEMINI_TEMPERATURE
                )

                markdown = response.choices[0].message.content.strip()

                # Clean up markdown wrapper if present
                if markdown.startswith('```markdown'):
                    markdown = markdown[len('```markdown'):].strip()
                if markdown.endswith('```'):
                    markdown = markdown[:-3].strip()

                page_markdowns.append(markdown)

                if verbose:
                    print("✅")

                # Rate limiting
                time.sleep(OCR_RATE_LIMIT_DELAY)

            except Exception as e:
                if verbose:
                    print(f"❌ {e}")
                page_markdowns.append(f"[Error on page {i}: {e}]")

        return page_markdowns

    def process_document(
        self,
        pdf_path: str,
        max_pages: Optional[int] = OCR_MAX_PAGES
    ) -> dict:
        """
        Process a PDF document and return structured data

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process

        Returns:
            Dictionary with document metadata and content
        """
        pdf_name = Path(pdf_path).stem

        print(f"\n📄 Processing: {pdf_name}")
        print("="*60)

        page_markdowns = self.pdf_to_markdown(pdf_path, max_pages)

        # Combine pages
        full_document = '\n\n'.join(page_markdowns)

        result = {
            'document_name': pdf_name,
            'file_path': pdf_path,
            'total_pages': len(page_markdowns),
            'page_markdowns': page_markdowns,
            'full_document': full_document,
            'char_count': len(full_document),
            'word_count': len(full_document.split())
        }

        print(f"\n✅ OCR Complete:")
        print(f"   Pages: {result['total_pages']}")
        print(f"   Characters: {result['char_count']:,}")
        print(f"   Words: {result['word_count']:,}")

        return result


def test_ocr():
    """Test OCR on a single PDF"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ocr_utils.py <pdf_path> [max_pages]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None

    ocr = GeminiOCR()
    result = ocr.process_document(pdf_path, max_pages)

    # Show preview
    print(f"\n📄 Preview (first 500 chars):")
    print("="*60)
    print(result['full_document'][:500])
    print("="*60)


if __name__ == "__main__":
    test_ocr()
