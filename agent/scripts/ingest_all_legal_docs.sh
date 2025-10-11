#!/bin/bash
# Ingest all legal PDFs from legal_documents folder

echo "🚀 Ingesting all legal documents..."
echo ""

# Check if legal_documents folder exists
if [ ! -d "legal_documents" ]; then
    echo "❌ Error: legal_documents/ folder not found"
    echo "   Create it with: mkdir legal_documents"
    exit 1
fi

# Count PDFs
pdf_count=$(ls legal_documents/*.pdf 2>/dev/null | wc -l)

if [ "$pdf_count" -eq 0 ]; then
    echo "❌ No PDF files found in legal_documents/"
    exit 1
fi

echo "📁 Found $pdf_count PDF(s) in legal_documents/"
echo ""

# Run ingestion (the script already handles directory input)
python scripts/ingest_legal_docs.py legal_documents/ "$@"
