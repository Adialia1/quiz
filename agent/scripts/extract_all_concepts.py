"""
Extract All Concepts and Rules Script

This script:
1. Fetches all topics from the API (/api/exams/practice/topics)
2. For each topic, queries legal_expert with MAX top_k to get ALL rules/concepts
3. For each concept, asks legal_expert for detailed explanation
4. Generates a structured JSON dataset of concepts

Usage:
    python scripts/extract_all_concepts.py --output concepts_dataset.json
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import argparse
from typing import List, Dict, Any
from tqdm import tqdm
import os
from supabase import create_client, Client

from agent.agents.legal_expert import LegalExpertAgent
from agent.config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY


def get_all_topics() -> List[str]:
    """
    Get all topics from the database

    Returns:
        List of topic names
    """
    print("📚 Fetching all topics from database...")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Get all unique topics from ai_generated_questions
    result = supabase.table("ai_generated_questions")\
        .select("topic")\
        .eq("is_active", True)\
        .execute()

    # Extract unique topics
    topics = list(set([q['topic'] for q in result.data]))

    print(f"✅ Found {len(topics)} topics")
    return sorted(topics)


def extract_concepts_for_topic(
    legal_expert: LegalExpertAgent,
    topic: str,
    max_top_k: int = 200
) -> List[Dict[str, Any]]:
    """
    Extract all concepts/rules for a specific topic using MAX top_k

    Args:
        legal_expert: Initialized LegalExpertAgent
        topic: The topic name
        max_top_k: Maximum number of chunks to retrieve (super high for completeness)

    Returns:
        List of raw concept chunks
    """
    print(f"\n🔍 Extracting concepts for topic: {topic}")
    print(f"   Using top_k={max_top_k} for maximum coverage...")

    # Build query to get ALL information about this topic
    # Use a more focused query to avoid getting irrelevant chunks
    query = f"""
    מהם כל החוקים, הכללים והמושגים החשובים בנושא: "{topic}"?

    אנא כלול:
    - הגדרות של מושגים מרכזיים
    - כללים וחוקים ספציפיים
    - דוגמאות והסברים
    - חריגים וסייגים
    """

    # Query with MAXIMUM top_k to get everything
    result = legal_expert.process({
        "query": query,
        "k": max_top_k
    })

    # Parse the context to extract individual concepts
    context = result.get('context', '')

    # Split by source markers
    chunks = context.split('---')

    concepts = []
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk or len(chunk) < 50:  # Skip very short chunks
            continue

        # Extract document name and page if available
        doc_name = "Unknown"
        page_num = "N/A"
        content = chunk

        if "[מקור" in chunk:
            lines = chunk.split('\n', 1)
            if len(lines) > 1:
                header = lines[0]
                content = lines[1].strip()

                # Parse header: [מקור X] DocumentName - עמוד Y
                try:
                    doc_part = header.split(']')[1].strip()
                    if ' - עמוד' in doc_part:
                        doc_name, page_part = doc_part.split(' - עמוד')
                        doc_name = doc_name.strip()
                        page_num = page_part.strip()
                    else:
                        doc_name = doc_part
                except:
                    pass

        concepts.append({
            'chunk_id': i,
            'topic': topic,
            'content': content,
            'source_document': doc_name,
            'source_page': page_num
        })

    print(f"   ✅ Extracted {len(concepts)} concept chunks")
    return concepts


def enrich_concept_with_explanation(
    legal_expert: LegalExpertAgent,
    concept_chunk: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enrich a concept chunk with detailed explanation from legal_expert

    Args:
        legal_expert: Initialized LegalExpertAgent
        concept_chunk: Raw concept chunk

    Returns:
        Enriched concept with explanation, examples, etc.
    """
    topic = concept_chunk['topic']
    content = concept_chunk['content']

    # Build enrichment query
    query = f"""
    בהתבסס על המידע הבא מנושא "{topic}":

    {content[:500]}...

    אנא ספק:
    1. **כותרת** - כותרת קצרה ותמציתית למושג/כלל זה (עד 10 מילים)
    2. **הסבר מפורט** - הסבר ברור ומובן של המושג
    3. **דוגמה** - דוגמה מעשית אחת (אם רלוונטי)
    4. **נקודות מפתח** - 2-3 נקודות חשובות לזכור

    החזר בפורמט JSON:
    ```json
    {{
      "title": "כותרת המושג",
      "explanation": "הסבר מפורט...",
      "example": "דוגמה מעשית...",
      "key_points": ["נקודה 1", "נקודה 2", "נקודה 3"]
    }}
    ```
    """

    try:
        # Get enrichment from legal expert (normal mode, not max top_k)
        result = legal_expert.process({
            "query": query,
            "k": 10  # Normal k for explanation
        })

        answer = result.get('answer', '')

        # Parse JSON from answer
        enrichment = parse_json_from_text(answer)

        # Merge with original chunk
        enriched = {
            **concept_chunk,
            'title': enrichment.get('title', f"מושג בנושא {topic}"),
            'explanation': enrichment.get('explanation', content[:200]),
            'example': enrichment.get('example', ''),
            'key_points': enrichment.get('key_points', []),
            'raw_content': content  # Keep original
        }

        return enriched

    except Exception as e:
        print(f"   ⚠️  Error enriching concept: {e}")

        # Check if rate limit error
        if "rate" in str(e).lower() or "429" in str(e):
            print(f"   ⏸️  Rate limit hit, waiting 60 seconds...")
            import time
            time.sleep(60)
            # Retry once
            try:
                result = legal_expert.process({"query": query, "k": 10})
                answer = result.get('answer', '')
                enrichment = parse_json_from_text(answer)
                return {
                    **concept_chunk,
                    'title': enrichment.get('title', f"מושג בנושא {topic}"),
                    'explanation': enrichment.get('explanation', content[:200]),
                    'example': enrichment.get('example', ''),
                    'key_points': enrichment.get('key_points', []),
                    'raw_content': content
                }
            except:
                pass

        # Return with basic info
        return {
            **concept_chunk,
            'title': f"מושג בנושא {topic}",
            'explanation': content[:300],
            'example': '',
            'key_points': [],
            'raw_content': content
        }


def parse_json_from_text(text: str) -> Dict[str, Any]:
    """Parse JSON from text that might contain code blocks"""
    import re

    # Try to extract JSON from code blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except Exception as e:
            print(f"      ⚠️  Failed to parse JSON from code block: {e}")

    # Try to find JSON without code blocks (greedy match for nested objects)
    json_match = re.search(r'\{(?:[^{}]|\{[^{}]*\})*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except Exception as e:
            print(f"      ⚠️  Failed to parse JSON without code block: {e}")

    # Try parsing entire response
    try:
        return json.loads(text)
    except:
        pass

    return {}


def main():
    parser = argparse.ArgumentParser(description='Extract all concepts from legal RAG')
    parser.add_argument(
        '--output',
        type=str,
        default='concepts_dataset.json',
        help='Output JSON file path'
    )
    parser.add_argument(
        '--max-top-k',
        type=int,
        default=200,
        help='Maximum top_k for extraction (default: 200)'
    )
    parser.add_argument(
        '--skip-enrichment',
        action='store_true',
        help='Skip enrichment step (faster, but less detailed)'
    )
    parser.add_argument(
        '--limit-topics',
        type=int,
        default=None,
        help='Limit number of topics to process (for testing)'
    )

    args = parser.parse_args()

    print("="*70)
    print("🚀 Concept Extraction Script")
    print("="*70)

    # Initialize legal expert
    print("\n🔧 Initializing Legal Expert Agent...")
    legal_expert = LegalExpertAgent(
        temperature=0.1,
        use_thinking_model=False
    )
    print("✅ Legal Expert ready\n")

    # Get all topics
    topics = get_all_topics()

    if args.limit_topics:
        topics = topics[:args.limit_topics]
        print(f"⚠️  Limited to {args.limit_topics} topics for testing\n")

    # Extract concepts for each topic
    all_concepts = []
    seen_content_hashes = set()  # For deduplication

    print(f"\n📊 Processing {len(topics)} topics...\n")

    for topic_idx, topic in enumerate(topics, 1):
        print(f"\n[{topic_idx}/{len(topics)}] Processing: {topic}")
        print("-" * 70)

        # Step 1: Extract raw concepts with MAX top_k
        raw_concepts = extract_concepts_for_topic(
            legal_expert,
            topic,
            max_top_k=args.max_top_k
        )

        # Step 2: Enrich each concept with explanation
        if not args.skip_enrichment:
            print(f"   📝 Enriching {len(raw_concepts)} concepts...")

            for i, concept in enumerate(tqdm(raw_concepts, desc="   Enriching")):
                # Deduplicate based on content hash
                content_hash = hash(concept.get('content', '')[:200])
                if content_hash in seen_content_hashes:
                    continue  # Skip duplicate

                seen_content_hashes.add(content_hash)
                enriched = enrich_concept_with_explanation(legal_expert, concept)
                all_concepts.append(enriched)
        else:
            print(f"   ⏭️  Skipping enrichment (--skip-enrichment flag)")
            for concept in raw_concepts:
                content_hash = hash(concept.get('content', '')[:200])
                if content_hash not in seen_content_hashes:
                    seen_content_hashes.add(content_hash)
                    all_concepts.append(concept)

    # Save to JSON
    print(f"\n💾 Saving {len(all_concepts)} concepts to {args.output}...")

    output_data = {
        'metadata': {
            'total_concepts': len(all_concepts),
            'total_topics': len(topics),
            'max_top_k_used': args.max_top_k,
            'enriched': not args.skip_enrichment
        },
        'topics': topics,
        'concepts': all_concepts
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Dataset saved to {args.output}")

    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"Topics processed: {len(topics)}")
    print(f"Total concepts extracted: {len(all_concepts)}")
    print(f"Average concepts per topic: {len(all_concepts) / len(topics):.1f}")
    print(f"Output file: {args.output}")
    print("="*70)


if __name__ == "__main__":
    main()
