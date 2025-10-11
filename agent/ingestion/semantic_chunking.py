"""
Semantic chunking using StatisticalChunker from semantic-chunkers
Ported from test_semantic_chunking_colab.ipynb
"""
from typing import List, Dict
from semantic_chunkers import StatisticalChunker
from semantic_router.encoders import HuggingFaceEncoder

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agent.config.settings import EMBEDDING_MODEL

class SemanticChunker:
    """Wrapper for semantic chunking with StatisticalChunker"""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize semantic chunker

        Args:
            model_name: HuggingFace model for embeddings
        """
        print(f"🤖 Loading encoder: {model_name}...")
        self.encoder = HuggingFaceEncoder(name=model_name)
        self.chunker = StatisticalChunker(encoder=self.encoder)
        print("✅ Semantic chunker ready")

    def chunk_document(self, document_text: str, verbose: bool = True) -> List[Dict]:
        """
        Chunk a document using StatisticalChunker

        Args:
            document_text: Full document text
            verbose: Print progress info

        Returns:
            List of chunk dictionaries with content and metadata
        """
        if verbose:
            print(f"📊 Chunking document ({len(document_text):,} chars)...")

        # Chunk using StatisticalChunker
        chunks_raw = self.chunker(docs=[document_text])

        # Extract and structure chunks
        chunks = []
        for i, chunk in enumerate(chunks_raw[0]):
            content = chunk.content if hasattr(chunk, 'content') else str(chunk)

            chunk_data = {
                'chunk_index': i,
                'content': content,
                'char_count': len(content),
                'word_count': len(content.split()),
                'token_count_approx': int(len(content.split()) * 1.3)  # Approximation
            }

            chunks.append(chunk_data)

        if verbose:
            total_tokens = sum(c['token_count_approx'] for c in chunks)
            avg_tokens = total_tokens / len(chunks) if chunks else 0

            print(f"✅ Created {len(chunks)} chunks")
            print(f"   Avg size: {avg_tokens:.0f} tokens")
            print(f"   Total tokens: {total_tokens:,}")

        return chunks

    def chunk_with_embeddings(self, document_text: str) -> List[Dict]:
        """
        Chunk document and generate embeddings for each chunk

        Args:
            document_text: Full document text

        Returns:
            List of chunks with embeddings
        """
        chunks = self.chunk_document(document_text, verbose=True)

        print(f"🔄 Generating embeddings for {len(chunks)} chunks...")

        for i, chunk in enumerate(chunks):
            if i % 10 == 0 and i > 0:
                print(f"   Progress: {i}/{len(chunks)}...")

            # Generate embedding
            embedding = self.encoder([chunk['content']])[0]

            # Convert to list if it's a numpy array, otherwise use as-is
            if hasattr(embedding, 'tolist'):
                chunk['embedding'] = embedding.tolist()
            else:
                chunk['embedding'] = embedding

        print(f"✅ Embeddings generated")

        return chunks

    def analyze_chunks(self, chunks: List[Dict]):
        """
        Print chunk analysis statistics

        Args:
            chunks: List of chunk dictionaries
        """
        if not chunks:
            print("⚠️  No chunks to analyze")
            return

        sizes = [c['token_count_approx'] for c in chunks]

        print("\n" + "="*60)
        print("CHUNK ANALYSIS")
        print("="*60)
        print(f"Total chunks: {len(chunks)}")
        print(f"Avg size: {sum(sizes)/len(sizes):.0f} tokens")
        print(f"Min size: {min(sizes)} tokens")
        print(f"Max size: {max(sizes)} tokens")
        print(f"Total tokens: {sum(sizes):,}")

        # Show size distribution
        print(f"\nSize distribution:")
        ranges = [(0, 200), (200, 400), (400, 600), (600, 800), (800, float('inf'))]

        for min_size, max_size in ranges:
            count = sum(1 for s in sizes if min_size <= s < max_size)
            if count > 0:
                label = f"{min_size}-{max_size}" if max_size != float('inf') else f"{min_size}+"
                print(f"   {label:>10} tokens: {count:>3} chunks")

        print("="*60)


def test_chunking():
    """Test chunking on sample text"""
    sample_text = """
    חוק ניירות ערך, התשכ"ח-1968

    פרק א': הגדרות

    סעיף 1: הגדרות
    בחוק זה -
    "ניירות ערך" - מניות, אגרות חוב, זכויות במקרקעין.

    סעיף 2: רשות ניירות ערך
    הרשות אחראית על פיקוח השוק.

    פרק ב': איסורים

    סעיף 3: שימוש במידע פנים
    אדם שמחזיק במידע פנים לא יסחר בניירות ערך.
    """ * 10  # Repeat to create longer document

    chunker = SemanticChunker()
    chunks = chunker.chunk_document(sample_text)
    chunker.analyze_chunks(chunks)

    # Show first chunk
    if chunks:
        print(f"\n📄 First chunk preview:")
        print("="*60)
        print(chunks[0]['content'][:300])
        print("="*60)


if __name__ == "__main__":
    test_chunking()
