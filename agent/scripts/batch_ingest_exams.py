#!/usr/bin/env python3
"""
Batch Parallel Exam Ingestion Script
Processes all PDF exams in documents/exams/ directory in parallel

Usage:
    python scripts/batch_ingest_exams.py
    python scripts/batch_ingest_exams.py --workers 4
    python scripts/batch_ingest_exams.py --no-enrichment  # Skip legal enrichment (faster)
    python scripts/batch_ingest_exams.py --dry-run  # Test without ingesting
"""
import sys
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict
import time
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from agent.ingestion.llm_exam_parser import LLMExamParser
from agent.scripts.ingest_exam_questions import ExamQuestionIngestion


def process_single_pdf(
    pdf_path: str,
    use_enrichment: bool = True,
    dry_run: bool = False
) -> Dict:
    """
    Process a single PDF file

    Args:
        pdf_path: Path to PDF file
        use_enrichment: Whether to use legal enrichment
        dry_run: If True, parse but don't ingest

    Returns:
        Dict with results
    """
    start_time = time.time()
    pdf_name = Path(pdf_path).name

    try:
        print(f"\n{'='*70}")
        print(f"📄 Processing: {pdf_name}")
        print(f"{'='*70}")

        # Initialize parser
        parser = LLMExamParser()

        # Parse PDF
        result = parser.parse_pdf(pdf_path, verbose=True)

        questions = result['questions']
        metadata = result['metadata']

        if not questions:
            return {
                'pdf': pdf_name,
                'success': False,
                'error': 'No questions extracted',
                'questions_extracted': 0,
                'time_taken': time.time() - start_time
            }

        # If dry run, stop here
        if dry_run:
            return {
                'pdf': pdf_name,
                'success': True,
                'questions_extracted': len(questions),
                'questions_ingested': 0,
                'time_taken': time.time() - start_time,
                'dry_run': True
            }

        # Ingest to database
        print(f"\n🔄 Ingesting {len(questions)} questions to database...")

        pipeline = ExamQuestionIngestion(use_legal_enrichment=use_enrichment)

        # Convert to ingestion format
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                'question': q.get('question_text', ''),
                'options': q.get('options', {}),
                'correct_answer': q.get('correct_answer', ''),
                'topic': 'Securities Ethics',  # Default topic
                'difficulty': 'medium',
                'source': pdf_name,
                'metadata': {
                    'page_number': q.get('page_number'),
                    'question_number': q.get('question_number')
                }
            })

        # Ingest
        ingest_result = pipeline.ingest_questions(formatted_questions)

        return {
            'pdf': pdf_name,
            'success': ingest_result.get('success', False),
            'questions_extracted': len(questions),
            'questions_ingested': ingest_result.get('inserted', 0),
            'time_taken': time.time() - start_time
        }

    except Exception as e:
        print(f"\n❌ Error processing {pdf_name}: {e}")
        import traceback
        traceback.print_exc()

        return {
            'pdf': pdf_name,
            'success': False,
            'error': str(e),
            'questions_extracted': 0,
            'questions_ingested': 0,
            'time_taken': time.time() - start_time
        }


def batch_ingest_exams(
    exams_dir: str = "documents/exams",
    workers: int = 3,
    use_enrichment: bool = True,
    dry_run: bool = False,
    limit: int = None
):
    """
    Process all PDF exams in parallel

    Args:
        exams_dir: Directory containing exam PDFs
        workers: Number of parallel workers
        use_enrichment: Whether to use legal enrichment
        dry_run: If True, parse but don't ingest
        limit: Max number of PDFs to process (for testing)
    """
    print("="*70)
    print("🚀 BATCH PARALLEL EXAM INGESTION")
    print("="*70)

    # Find all PDFs
    exams_path = Path(exams_dir)
    if not exams_path.exists():
        print(f"❌ Directory not found: {exams_dir}")
        sys.exit(1)

    pdf_files = sorted(exams_path.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ No PDF files found in {exams_dir}")
        sys.exit(1)

    # Limit for testing
    if limit:
        pdf_files = pdf_files[:limit]

    print(f"\n📚 Found {len(pdf_files)} PDF files")
    print(f"👷 Using {workers} parallel workers")
    print(f"🤖 Legal enrichment: {'Enabled' if use_enrichment else 'Disabled'}")
    print(f"🔍 Dry run: {'Yes (no ingestion)' if dry_run else 'No (will ingest)'}")
    print()

    # Show files
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf.name}")

    print(f"\n{'='*70}")
    input("Press ENTER to start processing... (Ctrl+C to cancel)")
    print(f"{'='*70}\n")

    start_time = time.time()
    results = []

    # Process in parallel
    with ProcessPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_pdf = {
            executor.submit(
                process_single_pdf,
                str(pdf),
                use_enrichment,
                dry_run
            ): pdf.name
            for pdf in pdf_files
        }

        # Collect results as they complete
        for future in as_completed(future_to_pdf):
            pdf_name = future_to_pdf[future]
            try:
                result = future.result()
                results.append(result)

                # Print summary
                if result['success']:
                    print(f"\n✅ {result['pdf']}: "
                          f"{result['questions_extracted']} extracted, "
                          f"{result.get('questions_ingested', 0)} ingested "
                          f"({result['time_taken']:.1f}s)")
                else:
                    print(f"\n❌ {result['pdf']}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"\n❌ {pdf_name}: Unexpected error: {e}")
                results.append({
                    'pdf': pdf_name,
                    'success': False,
                    'error': str(e),
                    'questions_extracted': 0,
                    'questions_ingested': 0
                })

    total_time = time.time() - start_time

    # Print final summary
    print(f"\n{'='*70}")
    print("📊 BATCH INGESTION SUMMARY")
    print(f"{'='*70}\n")

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    total_extracted = sum(r['questions_extracted'] for r in results)
    total_ingested = sum(r.get('questions_ingested', 0) for r in results)

    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print(f"📝 Total questions extracted: {total_extracted}")
    print(f"💾 Total questions ingested: {total_ingested}")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes ({total_time:.1f}s)")

    if total_extracted > 0:
        print(f"⚡ Average time per question: {total_time/total_extracted:.1f}s")
        print(f"📈 Questions per minute: {total_extracted/(total_time/60):.1f}")

    if failed:
        print(f"\n❌ Failed PDFs:")
        for r in failed:
            print(f"   - {r['pdf']}: {r.get('error', 'Unknown error')}")

    # Detailed results table
    print(f"\n{'='*70}")
    print("📋 DETAILED RESULTS")
    print(f"{'='*70}\n")
    print(f"{'PDF Name':<40} {'Extracted':>10} {'Ingested':>10} {'Time':>8}")
    print("-"*70)

    for r in sorted(results, key=lambda x: x['pdf']):
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['pdf']:<38} "
              f"{r['questions_extracted']:>10} "
              f"{r.get('questions_ingested', 0):>10} "
              f"{r.get('time_taken', 0):>7.1f}s")

    print(f"{'='*70}\n")

    # Save results to file
    results_file = f"batch_ingest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import json
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_files': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'total_extracted': total_extracted,
            'total_ingested': total_ingested,
            'total_time': total_time,
            'results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"📄 Results saved to: {results_file}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Batch ingest all exam PDFs in parallel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDFs with 3 workers (default)
  python scripts/batch_ingest_exams.py

  # Use 5 workers for faster processing
  python scripts/batch_ingest_exams.py --workers 5

  # Skip enrichment to save time/cost
  python scripts/batch_ingest_exams.py --no-enrichment

  # Test mode: parse but don't ingest
  python scripts/batch_ingest_exams.py --dry-run

  # Test with only 3 files
  python scripts/batch_ingest_exams.py --limit 3
        """
    )

    parser.add_argument(
        '--dir',
        default='documents/exams',
        help='Directory containing exam PDFs (default: documents/exams)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='Number of parallel workers (default: 3)'
    )
    parser.add_argument(
        '--no-enrichment',
        action='store_true',
        help='Skip legal enrichment (faster, no explanations/references)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse PDFs but do not ingest to database'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of PDFs to process (for testing)'
    )

    args = parser.parse_args()

    batch_ingest_exams(
        exams_dir=args.dir,
        workers=args.workers,
        use_enrichment=not args.no_enrichment,
        dry_run=args.dry_run,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
