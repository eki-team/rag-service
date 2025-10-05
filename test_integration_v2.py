"""
Test completo del Advanced RAG v2.0 integrado
==============================================

Prueba todos los componentes:
1. TAG_DICT extraction (extracted vs hardcoded)
2. BM25 retrieval
3. RRF fusion (Dense + BM25)
4. Cross-encoder reranking
5. Full pipeline E2E
"""
import logging
import asyncio
from app.services.rag.extract_tag_dict import extract_tags_from_nasa_txt, expand_query_with_tag_dict
from app.services.rag.bm25_retriever import BM25Retriever
from app.services.rag.rrf_fusion import fuse_results
from app.services.rag.cross_encoder_reranker import CrossEncoderReranker

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_tag_dict_extraction():
    """Test 1: TAG_DICT extraction from nasa.txt"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: TAG_DICT EXTRACTION")
    logger.info("="*80)
    
    # Extract
    tag_dict = extract_tags_from_nasa_txt("contexts/nasa.txt")
    
    logger.info(f"✅ Extracted {len(tag_dict)} normalized terms")
    logger.info(f"   Sample terms: {list(tag_dict.keys())[:15]}")
    
    # Test expansion
    test_query = "How does microgravity affect bone density in mice?"
    expansions = expand_query_with_tag_dict(tag_dict, test_query)
    
    logger.info(f"\n🧪 Test query: {test_query}")
    logger.info(f"📊 Expansions ({len(expansions)}): {expansions[:20]}")
    
    return tag_dict


def test_bm25_retrieval():
    """Test 2: BM25 lexical retrieval"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: BM25 RETRIEVAL")
    logger.info("="*80)
    
    # Mock chunks (scientific text)
    test_chunks = [
        {
            "source_id": "chunk_1",
            "text": "Microgravity exposure during spaceflight significantly reduces bone mineral density in mice by 20-30%. Osteoblast activity decreases while osteoclast activity increases, leading to net bone loss.",
            "section": "Results",
            "doi": "10.1234/example1"
        },
        {
            "source_id": "chunk_2",
            "text": "The International Space Station (ISS) provides a unique environment for studying long-term spaceflight effects on biological systems, including skeletal health and immune function.",
            "section": "Introduction",
            "doi": "10.1234/example2"
        },
        {
            "source_id": "chunk_3",
            "text": "Hindlimb unloading (HU) in rodents simulates microgravity-induced bone loss observed in astronauts. This ground-based model shows similar molecular pathways to actual spaceflight.",
            "section": "Methods",
            "doi": "10.1234/example3"
        },
        {
            "source_id": "chunk_4",
            "text": "Cosmic radiation exposure during deep space missions poses significant health risks including DNA damage, increased cancer risk, and cardiovascular effects.",
            "section": "Discussion",
            "doi": "10.1234/example4"
        },
        {
            "source_id": "chunk_5",
            "text": "Bone remodeling in microgravity involves complex interactions between osteoblasts (bone-forming cells) and osteoclasts (bone-resorbing cells). The balance shifts toward resorption.",
            "section": "Results",
            "doi": "10.1234/example1"
        },
    ]
    
    # Initialize BM25
    retriever = BM25Retriever(test_chunks)
    
    # Test query
    query = "How does microgravity affect bone density in mice?"
    
    # Search without expansion
    results_plain = retriever.search(query, top_k=3)
    
    logger.info(f"\n🔍 Query: {query}")
    logger.info(f"📊 BM25 Results (no expansion):")
    for i, result in enumerate(results_plain, 1):
        logger.info(f"  [{i}] Score: {result['bm25_score']:.3f} | ID: {result['source_id']}")
        logger.info(f"      Text: {result['text'][:80]}...")
    
    # Search with expansion
    expanded_terms = ["weightlessness", "skeletal", "μg", "osteoblast"]
    results_expanded = retriever.search(query, expanded_terms=expanded_terms, top_k=3)
    
    logger.info(f"\n🏷️ With expansion: {expanded_terms}")
    logger.info(f"📊 BM25 Results (with expansion):")
    for i, result in enumerate(results_expanded, 1):
        logger.info(f"  [{i}] Score: {result['bm25_score']:.3f} | ID: {result['source_id']}")
        logger.info(f"      Text: {result['text'][:80]}...")
    
    return test_chunks


def test_rrf_fusion(test_chunks):
    """Test 3: RRF fusion (Dense + BM25)"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: RRF FUSION")
    logger.info("="*80)
    
    # Mock dense results (sorted by similarity)
    dense_results = [
        {"source_id": "chunk_1", "text": test_chunks[0]['text'], "similarity_score": 0.92},
        {"source_id": "chunk_5", "text": test_chunks[4]['text'], "similarity_score": 0.88},
        {"source_id": "chunk_3", "text": test_chunks[2]['text'], "similarity_score": 0.85},
        {"source_id": "chunk_2", "text": test_chunks[1]['text'], "similarity_score": 0.78},
    ]
    
    # Mock BM25 results (sorted by BM25 score)
    bm25_results = [
        {"source_id": "chunk_1", "text": test_chunks[0]['text'], "bm25_score": 8.5},
        {"source_id": "chunk_3", "text": test_chunks[2]['text'], "bm25_score": 7.2},
        {"source_id": "chunk_4", "text": test_chunks[3]['text'], "bm25_score": 6.8},
        {"source_id": "chunk_5", "text": test_chunks[4]['text'], "bm25_score": 6.1},
    ]
    
    logger.info(f"📊 Dense results: {[r['source_id'] for r in dense_results]}")
    logger.info(f"📊 BM25 results: {[r['source_id'] for r in bm25_results]}")
    
    # Fuse
    fused = fuse_results(dense_results, bm25_results, k=60, top_k=5)
    
    logger.info(f"\n🔀 RRF Fused Results (k=60):")
    for i, result in enumerate(fused, 1):
        logger.info(f"  [{i}] RRF Score: {result['rrf_score']:.4f} | ID: {result['source_id']}")
    
    logger.info(f"\n💡 Expected: chunk_1 should rank highest (appears in both)")
    
    return fused


def test_cross_encoder_reranking(test_chunks):
    """Test 4: Cross-encoder reranking"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: CROSS-ENCODER RERANKING")
    logger.info("="*80)
    
    # Initialize cross-encoder (will download model first time)
    logger.info("🧠 Loading cross-encoder model...")
    reranker = CrossEncoderReranker()
    
    # Test query
    query = "How does microgravity affect bone density in mice?"
    
    # Rerank
    logger.info(f"\n🔍 Query: {query}")
    logger.info(f"📦 Reranking {len(test_chunks)} chunks...")
    
    reranked = reranker.rerank(
        query=query,
        chunks=test_chunks,
        top_k=3,
        mmr_lambda=0.7,
        max_per_doc=2,
        apply_section_boost=True
    )
    
    logger.info(f"\n📊 Cross-Encoder Results:")
    for i, result in enumerate(reranked, 1):
        logger.info(f"  [{i}] Score: {result['cross_encoder_score']:.3f}")
        logger.info(f"      Section: {result.get('section', 'N/A')}")
        logger.info(f"      ID: {result['source_id']}")
        logger.info(f"      Text: {result['text'][:80]}...")
    
    return reranked


async def test_full_pipeline():
    """Test 5: Full pipeline E2E (requires server running)"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: FULL PIPELINE E2E")
    logger.info("="*80)
    
    logger.info("⚠️  This test requires the RAG server running:")
    logger.info("    uvicorn app.main:app --reload --port 8000")
    logger.info("")
    logger.info("🔄 Skipping for now (run manually after server starts)")
    
    # TODO: Uncomment when server is running
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         "http://localhost:8000/chat",
    #         json={"query": "How does microgravity affect bone density?", "top_k": 8}
    #     )
    #     result = response.json()
    #     logger.info(f"✅ Response: {result['answer'][:200]}...")


def main():
    """Run all tests"""
    logger.info("\n" + "="*80)
    logger.info("ADVANCED RAG v2.0 - INTEGRATION TESTS")
    logger.info("="*80)
    
    # Test 1: TAG_DICT extraction
    tag_dict = test_tag_dict_extraction()
    
    # Test 2: BM25 retrieval
    test_chunks = test_bm25_retrieval()
    
    # Test 3: RRF fusion
    fused = test_rrf_fusion(test_chunks)
    
    # Test 4: Cross-encoder reranking
    reranked = test_cross_encoder_reranking(test_chunks)
    
    # Test 5: Full pipeline (skipped if server not running)
    asyncio.run(test_full_pipeline())
    
    logger.info("\n" + "="*80)
    logger.info("✅ ALL TESTS COMPLETED!")
    logger.info("="*80)
    logger.info("\nNext steps:")
    logger.info("  1. Start server: uvicorn app.main:app --reload --port 8000")
    logger.info("  2. Test full pipeline: python test_eval_quick.py")
    logger.info("  3. Run evaluation: python eval_rag_nasa.py")
    logger.info("")


if __name__ == "__main__":
    main()
