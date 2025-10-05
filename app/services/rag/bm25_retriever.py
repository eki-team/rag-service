"""
BM25 Lexical Retriever for Advanced RAG v2.0
Implements BM25Okapi for lexical search to complement dense retrieval
"""
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import logging
import re

logger = logging.getLogger(__name__)


class BM25Retriever:
    """
    BM25 lexical retriever for scientific text
    
    Features:
    - Tokenization with scientific term preservation
    - BM25Okapi scoring
    - Query expansion support
    """
    
    def __init__(self, chunks: List[Dict[str, Any]]):
        """
        Initialize BM25 index from chunks
        
        Args:
            chunks: List of chunk dicts with 'text', 'source_id', 'doi', etc.
        """
        logger.info(f"🔍 Initializing BM25 index with {len(chunks)} chunks...")
        
        self.chunks = chunks
        self.chunk_ids = [chunk.get('source_id', idx) for idx, chunk in enumerate(chunks)]
        
        # Tokenize corpus
        corpus_tokens = [self._tokenize(chunk['text']) for chunk in chunks]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(corpus_tokens)
        
        logger.info(f"✅ BM25 index ready ({len(corpus_tokens)} documents)")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text with scientific term preservation
        
        Features:
        - Lowercase
        - Preserve hyphenated terms (e.g., "multi-omics")
        - Preserve abbreviations (e.g., "mGy", "Gy")
        - Remove stopwords (optional)
        """
        text = text.lower()
        
        # Preserve hyphenated terms and abbreviations
        # Split on whitespace and punctuation except hyphens
        tokens = re.findall(r'\b[\w-]+\b', text)
        
        # Optional: Remove very short tokens (1 char) except units
        tokens = [t for t in tokens if len(t) > 1 or t in ['g', '%']]
        
        return tokens
    
    def search(
        self,
        query: str,
        expanded_terms: Optional[List[str]] = None,
        top_k: int = 25,
        boost_expanded: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25
        
        Args:
            query: User query
            expanded_terms: Optional list of expansion terms from TAG_DICT
            top_k: Number of results to return
            boost_expanded: Weight for expanded terms (0-1)
        
        Returns:
            List of chunks with BM25 scores
        """
        # Tokenize query
        query_tokens = self._tokenize(query)
        
        # Add expanded terms with lower weight
        if expanded_terms:
            expanded_tokens = []
            for term in expanded_terms:
                expanded_tokens.extend(self._tokenize(term))
            
            # Weight: 100% for original query, boost_expanded for expansions
            query_tokens = query_tokens + [t for t in expanded_tokens for _ in range(int(boost_expanded * 10))]
            
            logger.debug(f"🏷️ Expanded query: {len(query_tokens)} tokens (original: {len(self._tokenize(query))})")
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Create results with scores
        results = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx].copy()
            chunk['bm25_score'] = float(score)
            results.append(chunk)
        
        # Sort by score descending
        results.sort(key=lambda x: x['bm25_score'], reverse=True)
        
        # Return top_k
        top_results = results[:top_k]
        
        if top_results:
            logger.info(f"✅ BM25 retrieved {len(top_results)} chunks (top score: {top_results[0]['bm25_score']:.3f})")
        
        return top_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get BM25 index statistics"""
        return {
            "total_chunks": len(self.chunks),
            "index_type": "BM25Okapi",
            "avg_doc_len": self.bm25.avgdl if hasattr(self.bm25, 'avgdl') else None
        }


# Singleton for BM25 retriever (loaded once at startup)
_bm25_retriever: Optional[BM25Retriever] = None


def init_bm25_retriever(chunks: List[Dict[str, Any]]):
    """Initialize BM25 retriever (call at startup)"""
    global _bm25_retriever
    _bm25_retriever = BM25Retriever(chunks)
    logger.info("✅ BM25 retriever initialized")


def get_bm25_retriever() -> Optional[BM25Retriever]:
    """Get BM25 retriever instance"""
    return _bm25_retriever


if __name__ == "__main__":
    # Test BM25 retriever
    logging.basicConfig(level=logging.INFO)
    
    # Mock chunks
    test_chunks = [
        {"source_id": "1", "text": "Microgravity affects bone density in mice, causing significant bone loss."},
        {"source_id": "2", "text": "Spaceflight induces muscle atrophy and skeletal changes in astronauts."},
        {"source_id": "3", "text": "Radiation exposure during space missions impacts DNA repair mechanisms."},
        {"source_id": "4", "text": "The ISS environment provides unique conditions for studying weightlessness effects."},
        {"source_id": "5", "text": "Bone remodeling in microgravity involves osteoblast and osteoclast activity."},
    ]
    
    # Initialize
    retriever = BM25Retriever(test_chunks)
    
    # Test query
    query = "How does microgravity affect bone density?"
    results = retriever.search(query, top_k=3)
    
    print(f"\n🔍 Query: {query}")
    print(f"📊 Top {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"  [{i}] Score: {result['bm25_score']:.3f}")
        print(f"      Text: {result['text'][:80]}...")
    
    # Test with expansion
    expanded = ["weightlessness", "μg", "skeletal"]
    results_expanded = retriever.search(query, expanded_terms=expanded, top_k=3)
    
    print(f"\n🏷️ With expansion: {expanded}")
    print(f"📊 Top {len(results_expanded)} results:")
    for i, result in enumerate(results_expanded, 1):
        print(f"  [{i}] Score: {result['bm25_score']:.3f}")
        print(f"      Text: {result['text'][:80]}...")
