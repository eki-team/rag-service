"""
Test del Advanced RAG System
=============================

Verifica:
1. TAG_DICT expansion
2. Reranker scoring
3. Pipeline end-to-end (requiere servidor corriendo)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.rag.tag_dict import get_expanded_terms, get_matched_keys, expand_query_text

print("="*80)
print("TEST 1: TAG_DICT EXPANSION")
print("="*80)

test_queries = [
    "How does microgravity affect mouse bone density?",
    "What are the effects of radiation on arabidopsis?",
    "How does the ISS environment impact immune function?",
    "Gene expression changes in C. elegans during spaceflight",
]

for query in test_queries:
    print(f"\n🔍 Query: {query}")
    
    # Get matched keys
    matched_keys = get_matched_keys(query)
    print(f"   🏷️  Matched keys: {matched_keys}")
    
    # Get expanded terms
    expanded_terms = get_expanded_terms(query)
    print(f"   📝 Expanded terms ({len(expanded_terms)}): {list(expanded_terms)[:10]}...")
    
    # Get expanded query
    query_expanded = expand_query_text(query)
    print(f"   🔄 Expanded query preview: {query_expanded[:150]}...")

print("\n" + "="*80)
print("TEST 2: RERANKER SIGNALS")
print("="*80)

from app.services.rag.reranker import AdvancedReranker

query = "microgravity effects on bone"
expanded_terms = get_expanded_terms(query)

# Mock chunks
mock_chunks = [
    {
        "text": "Abstract: Microgravity exposure in mice leads to significant bone density loss. Osteoclast activity increased by 45%.",
        "score": 0.85,
        "section": "Abstract",
        "url": "https://www.nasa.gov/study123",
        "year": 2023,
        "doi": "10.1038/s41586-023-12345",
    },
    {
        "text": "Methods: We used RNA-seq to analyze gene expression in skeletal tissue samples from spaceflight missions.",
        "score": 0.72,
        "section": "Methods",
        "url": "https://science.org/study456",
        "year": 2018,
    },
    {
        "text": "Results: Bone mineral density decreased by 15% after 30 days of microgravity exposure in the ISS.",
        "score": 0.88,
        "section": "Results",
        "url": "https://www.nature.com/study789",
        "year": 2024,
    },
]

reranker = AdvancedReranker(
    query=query,
    expanded_terms=expanded_terms,
    top_rerank=3,
    top_synthesis=3,
)

reranked = reranker.rerank(mock_chunks)

print(f"\n🔄 Reranked {len(mock_chunks)} chunks:")
for idx, chunk in enumerate(reranked, start=1):
    signals = chunk.get("_debug_signals", {})
    print(f"\n   [{idx}] Section: {chunk['section']}")
    print(f"       Final Score: {signals.get('final', 0):.3f}")
    print(f"       Signals:")
    print(f"         - Sim: {signals.get('sim', 0):.3f}")
    print(f"         - Sec Boost: {signals.get('sec_boost', 0):.3f}")
    print(f"         - Keyword: {signals.get('keyword_overlap', 0):.3f}")
    print(f"         - Authority: {signals.get('authority', 0):.3f}")
    print(f"         - Recency: {signals.get('recency', 0):.3f}")

print("\n" + "="*80)
print("TEST 3: PIPELINE END-TO-END (requiere servidor)")
print("="*80)
print("\n⚠️  Para probar el pipeline completo, ejecuta:")
print("    1. Terminal 1: uvicorn app.main:app --reload --port 8000")
print("    2. Terminal 2: python test_advanced_rag.py --pipeline")
print("\n✅ Tests básicos completados!")
print("="*80)
