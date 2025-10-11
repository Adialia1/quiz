#!/usr/bin/env python
"""
Batch ingest all legal documents from legal_documents/ folder

Usage:
    python scripts/ingest_all_legal_docs.py
    python scripts/ingest_all_legal_docs.py --max-pages 5  # Test mode
    python scripts/ingest_all_legal_docs.py --skip-existing  # Skip already ingested
"""
import sys
import subprocess
from pathlib import Path

def main():
    """Run ingestion for all PDFs in legal_documents folder"""

    print("🚀 Batch Legal Document Ingestion")
    print("="*70 + "\n")

    # Check if legal_documents folder exists
    docs_folder = Path("legal_documents")

    if not docs_folder.exists():
        print("❌ Error: legal_documents/ folder not found")
        print("   Create it with: mkdir legal_documents")
        print("   Then add your PDF files to that folder")
        sys.exit(1)

    # Find all PDFs
    pdf_files = list(docs_folder.glob("*.pdf"))

    if not pdf_files:
        print("❌ No PDF files found in legal_documents/")
        print("   Add PDF files to the legal_documents/ folder")
        sys.exit(1)

    print(f"📁 Found {len(pdf_files)} PDF(s):")
    for pdf in sorted(pdf_files):
        print(f"   - {pdf.name}")
    print()

    # Build command
    cmd = ["python", "scripts/ingest_legal_docs.py", "legal_documents/"]

    # Pass through any command line arguments
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
        print(f"📋 Extra arguments: {' '.join(sys.argv[1:])}\n")

    # Show full command
    print(f"🔄 Running: {' '.join(cmd)}\n")
    print("="*70 + "\n")

    # Run the ingestion script
    try:
        result = subprocess.run(cmd, check=True)

        print("\n" + "="*70)
        print("✅ Batch ingestion complete!")
        print("="*70)

        sys.exit(result.returncode)

    except subprocess.CalledProcessError as e:
        print("\n" + "="*70)
        print("❌ Ingestion failed")
        print("="*70)
        sys.exit(e.returncode)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
