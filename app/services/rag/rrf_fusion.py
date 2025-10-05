"""
RRF (Reciprocal Rank Fusion) for Advanced RAG v2.0
Combines dense (embedding) and sparse (BM25) retrieval results
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RRFFusion:
    """
    Reciprocal Rank Fusion (RRF) combiner
    
    Formula: score(d) = sum(1 / (k + rank_i(d)))
    where k is a constant (typically 60) and rank_i is the rank in retriever i
    
    Reference: Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009).
    "Reciprocal rank fusion outperforms condorcet and individual rank learning methods."
    """
    
    def __init__(self, k: int = 60):
        """
        Initialize RRF fusion
        
        Args:
            k: RRF constant (default 60, as per your spec)
        """
        self.k = k
        logger.info(f"🔀 RRF Fusion initialized (k={k})")
    
    def fuse(
        self,
        dense_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        top_k: int = 24,
        dense_weight: float = 1.0,
        bm25_weight: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Fuse dense and BM25 results using RRF
        
        Args:
            dense_results: Results from dense retrieval (embeddings)
            bm25_results: Results from BM25 retrieval
            top_k: Number of results to return
            dense_weight: Weight for dense scores (default 1.0)
            bm25_weight: Weight for BM25 scores (default 1.0)
        
        Returns:
            Fused and ranked results
        """
        logger.info(f"🔀 Fusing {len(dense_results)} dense + {len(bm25_results)} BM25 results")
        
        # Create score dict: chunk_id -> RRF score
        rrf_scores = {}
        chunk_map = {}  # chunk_id -> full chunk dict
        
        # Process dense results
        for rank, chunk in enumerate(dense_results):
            chunk_id = self._get_chunk_id(chunk)
            score = dense_weight / (self.k + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + score
            chunk_map[chunk_id] = chunk
        
        # Process BM25 results
        for rank, chunk in enumerate(bm25_results):
            chunk_id = self._get_chunk_id(chunk)
            score = bm25_weight / (self.k + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + score
            
            # Add to chunk_map if not already present
            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = chunk
        
        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Create fused results
        fused_results = []
        for chunk_id in sorted_ids[:top_k]:
            chunk = chunk_map[chunk_id].copy()
            chunk['rrf_score'] = rrf_scores[chunk_id]
            fused_results.append(chunk)
        
        logger.info(f"✅ RRF fusion complete: {len(fused_results)} results (top score: {fused_results[0]['rrf_score']:.4f})")
        
        return fused_results
    
    def _get_chunk_id(self, chunk: Dict[str, Any]) -> str:
        """
        Get unique identifier for chunk
        
        Priority: source_id > document_id > index
        """
        return (
            chunk.get('source_id') or
            chunk.get('document_id') or
            chunk.get('id') or
            str(hash(chunk.get('text', '')))
        )


def fuse_results(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = 60,
    top_k: int = 24
) -> List[Dict[str, Any]]:
    """
    Convenience function for RRF fusion
    
    Args:
        dense_results: Dense retrieval results
        bm25_results: BM25 retrieval results
        k: RRF constant
        top_k: Number of results to return
    
    Returns:
        Fused results
    """
    fusion = RRFFusion(k=k)
    return fusion.fuse(dense_results, bm25_results, top_k=top_k)


if __name__ == "__main__":
    # Test RRF fusion
    logging.basicConfig(level=logging.INFO)
    
    # Mock results
    dense_results = [
        {"source_id": "A", "text": "Result A from dense", "similarity_score": 0.95},
        {"source_id": "B", "text": "Result B from dense", "similarity_score": 0.90},
        {"source_id": "C", "text": "Result C from dense", "similarity_score": 0.85},
        {"source_id": "D", "text": "Result D from dense", "similarity_score": 0.80},
    ]
    
    bm25_results = [
        {"source_id": "B", "text": "Result B from BM25", "bm25_score": 25.5},
        {"source_id": "E", "text": "Result E from BM25", "bm25_score": 22.0},
        {"source_id": "A", "text": "Result A from BM25", "bm25_score": 20.0},
        {"source_id": "F", "text": "Result F from BM25", "bm25_score": 18.0},
    ]
    
    # Fuse
    fusion = RRFFusion(k=60)
    fused = fusion.fuse(dense_results, bm25_results, top_k=5)
    
    print(f"\n📊 Fused Results (top {len(fused)}):")
    for i, result in enumerate(fused, 1):
        print(f"  [{i}] ID: {result['source_id']}, RRF Score: {result['rrf_score']:.4f}")
    
    # Expected: B (appears in both) should rank highest
    # Then A (appears in both)
    # Then C, D, E, F (single appearance)
