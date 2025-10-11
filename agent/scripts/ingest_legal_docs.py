"""
Legal Document Ingestion Pipeline
OCR → Semantic Chunking → Embeddings → Supabase

Usage:
    # Single file
    python scripts/ingest_legal_docs.py path/to/legal1.pdf

    # Multiple files
    python scripts/ingest_legal_docs.py legal_documents/*.pdf

    # Directory
    python scripts/ingest_legal_docs.py legal_documents/
"""
import sys
import argparse
from pathlib import Path
from typing import List
import json

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY, validate_config
from agent.ingestion.ocr_utils import GeminiOCR
from agent.ingestion.semantic_chunking import SemanticChunker

class LegalDocIngestion:
    """Pipeline for ingesting legal documents into Supabase"""

    def __init__(self):
        validate_config()

        print("🔧 Initializing ingestion pipeline...")

        # Initialize services
        self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.ocr = GeminiOCR()
        self.chunker = SemanticChunker()

        print("✅ Pipeline ready\n")

    def ingest_pdf(self, pdf_path: str, max_pages: int = None) -> dict:
        """
        Ingest a single PDF file

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process (None = all)

        Returns:
            Dictionary with ingestion results
        """
        pdf_name = Path(pdf_path).stem

        print("\n" + "="*70)
        print(f"📄 INGESTING: {pdf_name}")
        print("="*70)

        # Step 1: OCR
        print("\n[1/4] OCR Processing...")
        ocr_result = self.ocr.process_document(pdf_path, max_pages)

        # Step 2: Semantic Chunking
        print("\n[2/4] Semantic Chunking...")
        chunks = self.chunker.chunk_with_embeddings(ocr_result['full_document'])

        # Step 3: Prepare data for Supabase
        print(f"\n[3/4] Preparing {len(chunks)} chunks for database...")

        supabase_records = []
        for chunk in chunks:
            # Map pages to chunks (approximate based on position)
            # This is a simple heuristic - you can improve it
            approx_page = min(
                chunk['chunk_index'] // (len(chunks) // ocr_result['total_pages'] + 1) + 1,
                ocr_result['total_pages']
            )

            record = {
                'document_name': pdf_name,
                'page_number': approx_page,
                'chunk_index': chunk['chunk_index'],
                'content': chunk['content'],
                'embedding': chunk['embedding'],
                'metadata': {
                    'char_count': chunk['char_count'],
                    'word_count': chunk['word_count'],
                    'token_count_approx': chunk['token_count_approx'],
                    'total_pages': ocr_result['total_pages'],
                    'file_path': pdf_path
                }
            }

            supabase_records.append(record)

        # Step 4: Insert into Supabase
        print(f"[4/4] Inserting into Supabase...")

        try:
            # Batch insert (Supabase can handle large batches)
            response = self.supabase.table('legal_doc_chunks').insert(supabase_records).execute()

            print(f"✅ Successfully inserted {len(supabase_records)} chunks")

            result = {
                'success': True,
                'document_name': pdf_name,
                'total_pages': ocr_result['total_pages'],
                'total_chunks': len(chunks),
                'total_chars': ocr_result['char_count'],
                'total_words': ocr_result['word_count'],
                'records_inserted': len(supabase_records)
            }

            return result

        except Exception as e:
            print(f"❌ Error inserting into Supabase: {e}")
            result = {
                'success': False,
                'document_name': pdf_name,
                'error': str(e)
            }
            return result

    def ingest_multiple(self, pdf_paths: List[str], max_pages: int = None) -> List[dict]:
        """
        Ingest multiple PDF files

        Args:
            pdf_paths: List of PDF paths
            max_pages: Maximum pages per document

        Returns:
            List of ingestion results
        """
        results = []

        print(f"\n🚀 Starting batch ingestion of {len(pdf_paths)} documents\n")

        for i, pdf_path in enumerate(pdf_paths, 1):
            print(f"\n{'='*70}")
            print(f"Document {i}/{len(pdf_paths)}")
            print(f"{'='*70}")

            result = self.ingest_pdf(pdf_path, max_pages)
            results.append(result)

        # Summary
        print("\n" + "="*70)
        print("📊 INGESTION SUMMARY")
        print("="*70)

        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]

        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")

        if successful:
            total_chunks = sum(r['total_chunks'] for r in successful)
            total_pages = sum(r['total_pages'] for r in successful)
            print(f"\nTotal pages processed: {total_pages}")
            print(f"Total chunks created: {total_chunks}")

        if failed:
            print(f"\n❌ Failed documents:")
            for r in failed:
                print(f"   - {r['document_name']}: {r.get('error', 'Unknown error')}")

        return results

    def check_existing_documents(self) -> List[str]:
        """Get list of already ingested documents"""
        try:
            response = self.supabase.table('legal_doc_chunks')\
                .select('document_name')\
                .execute()

            # Get unique document names
            docs = list(set(row['document_name'] for row in response.data))

            if docs:
                print(f"📚 Found {len(docs)} existing documents in database:")
                for doc in sorted(docs):
                    print(f"   - {doc}")

            return docs

        except Exception as e:
            print(f"⚠️  Could not check existing documents: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(description='Ingest legal PDFs into Supabase')
    parser.add_argument('paths', nargs='+', help='PDF file(s) or directory to ingest')
    parser.add_argument('--max-pages', type=int, default=None, help='Max pages per document')
    parser.add_argument('--skip-existing', action='store_true', help='Skip already ingested docs')
    parser.add_argument('--check-only', action='store_true', help='Only check existing documents')

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = LegalDocIngestion()

    # Check existing if requested
    if args.check_only:
        pipeline.check_existing_documents()
        return

    # Get existing docs for skip check
    existing_docs = []
    if args.skip_existing:
        existing_docs = pipeline.check_existing_documents()

    # Collect all PDF paths
    pdf_paths = []
    for path_str in args.paths:
        path = Path(path_str)

        if path.is_file() and path.suffix.lower() == '.pdf':
            pdf_paths.append(str(path))
        elif path.is_dir():
            pdf_paths.extend([str(p) for p in path.glob('*.pdf')])
        elif '*' in path_str:
            # Glob pattern
            pdf_paths.extend([str(p) for p in Path('.').glob(path_str)])

    if not pdf_paths:
        print("❌ No PDF files found")
        sys.exit(1)

    # Filter out existing if requested
    if args.skip_existing:
        original_count = len(pdf_paths)
        pdf_paths = [p for p in pdf_paths if Path(p).stem not in existing_docs]
        skipped = original_count - len(pdf_paths)
        if skipped > 0:
            print(f"⏭️  Skipping {skipped} already ingested documents")

    if not pdf_paths:
        print("✅ All documents already ingested")
        return

    # Ingest
    results = pipeline.ingest_multiple(pdf_paths, args.max_pages)

    # Save results
    results_file = Path('ingestion_results.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Results saved to: {results_file}")


if __name__ == "__main__":
    main()
