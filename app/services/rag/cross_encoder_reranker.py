"""
Cross-Encoder Reranker for Advanced RAG v2.0
Replaces custom 8-signal scorer with state-of-the-art cross-encoder
"""
from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Cross-Encoder reranker with section boosting and MMR diversity
    
    Model: cross-encoder/ms-marco-MiniLM-L-6-v2
    - Input: (query, passage) pairs
    - Output: Relevance score (0-1)
    - Trained on MS MARCO passage ranking dataset
    
    Features:
    - Cross-encoder scoring
    - Section boost post-processing
    - MMR diversity (λ=0.7)
    - Max 2 chunks per document
    """
    
    # Section boost weights (as per your spec)
    SECTION_BOOST = {
        'abstract': 0.10,
        'results': 0.10,
        'discussion': 0.07,
        'conclusion': 0.07,
        'methods': 0.03,
        'introduction': 0.03,
        'intro': 0.03
    }
    
    EXCLUDE_SECTIONS = {'references', 'author', 'legal', 'disclaimer'}
    
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize cross-encoder model
        
        Args:
            model_name: HuggingFace model name
        """
        logger.info(f"🧠 Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info(f"✅ Cross-encoder ready")
    
    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 10,
        mmr_lambda: float = 0.7,
        max_per_doc: int = 2,
        apply_section_boost: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks using cross-encoder
        
        Args:
            query: User query
            chunks: Chunks to rerank (typically top 24 from RRF)
            top_k: Number of results to return (default 10)
            mmr_lambda: MMR diversity parameter (0=max diversity, 1=max relevance)
            max_per_doc: Maximum chunks per document
            apply_section_boost: Apply section-based boosting
        
        Returns:
            Reranked chunks with cross_encoder_score
        """
        if not chunks:
            return []
        
        logger.info(f"🔄 Reranking {len(chunks)} chunks with cross-encoder...")
        
        # 1. Score all (query, passage) pairs
        pairs = [(query, chunk['text']) for chunk in chunks]
        scores = self.model.predict(pairs)
        
        # Normalize scores to 0-1 range if needed
        scores = np.array(scores)
        if scores.max() > 1.0:
            scores = (scores - scores.min()) / (scores.max() - scores.min())
        
        # 2. Apply section boost
        if apply_section_boost:
            scores = self._apply_section_boost(chunks, scores)
        
        # 3. Filter excluded sections
        valid_indices = [
            i for i, chunk in enumerate(chunks)
            if not self._is_excluded_section(chunk)
        ]
        
        chunks_valid = [chunks[i] for i in valid_indices]
        scores_valid = scores[valid_indices]
        
        # 4. Sort by score
        sorted_indices = np.argsort(-scores_valid)
        chunks_sorted = [chunks_valid[i] for i in sorted_indices]
        scores_sorted = scores_valid[sorted_indices]
        
        # 5. Apply MMR diversity
        if mmr_lambda < 1.0:
            chunks_sorted, scores_sorted = self._apply_mmr(
                query, chunks_sorted, scores_sorted, top_k, mmr_lambda
            )
        
        # 6. Enforce max chunks per document
        chunks_final = self._enforce_max_per_doc(chunks_sorted, max_per_doc)
        
        # 7. Limit to top_k
        chunks_final = chunks_final[:top_k]
        
        # 8. Attach scores
        for i, chunk in enumerate(chunks_final):
            chunk['cross_encoder_score'] = float(scores_sorted[i] if i < len(scores_sorted) else 0.0)
            chunk['rerank_position'] = i + 1
        
        logger.info(f"✅ Reranking complete: {len(chunks_final)} chunks (top score: {chunks_final[0]['cross_encoder_score']:.3f})")
        
        return chunks_final
    
    def _apply_section_boost(self, chunks: List[Dict], scores: np.ndarray) -> np.ndarray:
        """Apply section-based boosting"""
        boosted_scores = scores.copy()
        
        for i, chunk in enumerate(chunks):
            section = chunk.get('section', '').lower()
            boost = self.SECTION_BOOST.get(section, 0.0)
            
            if boost > 0:
                boosted_scores[i] += boost
                logger.debug(f"  Section '{section}' boosted by +{boost:.2f}")
        
        return boosted_scores
    
    def _is_excluded_section(self, chunk: Dict) -> bool:
        """Check if chunk is from excluded section"""
        section = chunk.get('section', '').lower()
        return any(excl in section for excl in self.EXCLUDE_SECTIONS)
    
    def _apply_mmr(
        self,
        query: str,
        chunks: List[Dict],
        scores: np.ndarray,
        top_k: int,
        lambda_param: float
    ) -> tuple:
        """
        Apply Maximal Marginal Relevance (MMR) for diversity
        
        MMR formula: MMR = λ * Relevance - (1-λ) * max Similarity to selected
        """
        if len(chunks) <= top_k:
            return chunks, scores
        
        selected = []
        selected_scores = []
        remaining = list(range(len(chunks)))
        
        # Select first (highest relevance)
        first_idx = 0
        selected.append(chunks[first_idx])
        selected_scores.append(scores[first_idx])
        remaining.remove(first_idx)
        
        # Select rest using MMR
        while len(selected) < top_k and remaining:
            mmr_scores = []
            
            for idx in remaining:
                relevance = scores[idx]
                
                # Calculate max similarity to already selected
                max_sim = self._max_similarity(chunks[idx], selected)
                
                # MMR score
                mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                mmr_scores.append((idx, mmr))
            
            # Select highest MMR
            best_idx, best_mmr = max(mmr_scores, key=lambda x: x[1])
            selected.append(chunks[best_idx])
            selected_scores.append(scores[best_idx])
            remaining.remove(best_idx)
        
        return selected, np.array(selected_scores)
    
    def _max_similarity(self, chunk: Dict, selected: List[Dict]) -> float:
        """
        Calculate maximum similarity to selected chunks
        
        Simple approach: token overlap (Jaccard similarity)
        """
        chunk_tokens = set(chunk['text'].lower().split())
        
        max_sim = 0.0
        for sel_chunk in selected:
            sel_tokens = set(sel_chunk['text'].lower().split())
            
            intersection = len(chunk_tokens & sel_tokens)
            union = len(chunk_tokens | sel_tokens)
            
            if union > 0:
                sim = intersection / union
                max_sim = max(max_sim, sim)
        
        return max_sim
    
    def _enforce_max_per_doc(self, chunks: List[Dict], max_per_doc: int) -> List[Dict]:
        """Limit chunks per document"""
        doc_counts = {}
        filtered = []
        
        for chunk in chunks:
            doc_id = chunk.get('doi') or chunk.get('url') or chunk.get('document_id')
            
            if doc_id not in doc_counts:
                doc_counts[doc_id] = 0
            
            if doc_counts[doc_id] < max_per_doc:
                filtered.append(chunk)
                doc_counts[doc_id] += 1
        
        return filtered


# Singleton
_cross_encoder_reranker: Optional[CrossEncoderReranker] = None


def get_cross_encoder_reranker() -> CrossEncoderReranker:
    """Get or create cross-encoder reranker"""
    global _cross_encoder_reranker
    if _cross_encoder_reranker is None:
        _cross_encoder_reranker = CrossEncoderReranker()
    return _cross_encoder_reranker


if __name__ == "__main__":
    # Test cross-encoder reranker
    logging.basicConfig(level=logging.INFO)
    
    # Mock chunks
    test_chunks = [
        {
            "source_id": "1",
            "text": "Microgravity significantly reduces bone density in mice by 20-30%.",
            "section": "Results",
            "doi": "10.1234/example1"
        },
        {
            "source_id": "2",
            "text": "Spaceflight conditions affect various biological systems.",
            "section": "Introduction",
            "doi": "10.1234/example1"
        },
        {
            "source_id": "3",
            "text": "Bone loss during spaceflight is caused by reduced osteoblast activity.",
            "section": "Discussion",
            "doi": "10.1234/example2"
        },
        {
            "source_id": "4",
            "text": "References to previous studies on microgravity effects.",
            "section": "References",
            "doi": "10.1234/example3"
        },
    ]
    
    # Initialize reranker
    reranker = CrossEncoderReranker()
    
    # Test query
    query = "How does microgravity affect bone density in mice?"
    
    # Rerank
    results = reranker.rerank(query, test_chunks, top_k=3)
    
    print(f"\n🔍 Query: {query}")
    print(f"📊 Reranked Results (top {len(results)}):")
    for i, result in enumerate(results, 1):
        print(f"  [{i}] Score: {result['cross_encoder_score']:.3f}")
        print(f"      Section: {result.get('section', 'N/A')}")
        print(f"      Text: {result['text'][:80]}...")
