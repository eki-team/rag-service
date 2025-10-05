# Quick Test del Evaluador RAG
# =============================
# Script para probar el evaluador con una sola query antes de ejecutar el full benchmark

import asyncio
import httpx
import re
from eval_rag_nasa import (
    call_rag,
    calculate_grounded_ratio,
    count_citations,
    extract_tags_from_query,
    RAG_ENDPOINT,
    TOP_K
)

async def quick_test():
    print("="*80)
    print("QUICK TEST - NASA RAG EVALUATOR")
    print("="*80)
    print(f"Endpoint: {RAG_ENDPOINT}")
    print(f"Top-K: {TOP_K}\n")
    
    # Test query
    query = "What are the effects of microgravity on bone density in mice?"
    print(f"Query: {query}\n")
    
    # Extract tags
    tags = extract_tags_from_query(query)
    print(f"🏷️  Auto-extracted tags: {tags}\n")
    
    # Call RAG
    print("🔄 Calling RAG endpoint...")
    try:
        response = await call_rag(query)
        
        print(f"✅ Response received!\n")
        
        # Metrics
        answer = response["answer"]
        citations = response.get("citations", [])
        metrics = response.get("metrics", {})
        
        print("📊 METRICS:")
        print(f"  Latency: {metrics.get('latency_ms', 0):.0f}ms")
        print(f"  Retrieved: {metrics.get('retrieved_k', 0)} chunks")
        print(f"  Grounded Ratio: {metrics.get('grounded_ratio', 0):.2%}")
        print(f"  Citations: {count_citations(answer)}")
        print()
        
        # Answer preview
        print("📝 ANSWER (first 300 chars):")
        print(answer[:300] + "..." if len(answer) > 300 else answer)
        print()
        
        # Citations preview
        print(f"📚 CITATIONS ({len(citations)}):")
        for idx, cit in enumerate(citations[:3], 1):
            print(f"  [{idx}] {cit.get('source_id', 'N/A')}")
            print(f"      Section: {cit.get('section', 'N/A')}")
            print(f"      Snippet: {cit.get('snippet', '')[:80]}...")
        if len(citations) > 3:
            print(f"  ... and {len(citations) - 3} more")
        print()
        
        # Grounded ratio analysis
        gr = calculate_grounded_ratio(answer)
        sentences = re.split(r'[.!?]+', answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        print("🔍 GROUNDED RATIO ANALYSIS:")
        print(f"  Total sentences: {len(sentences)}")
        print(f"  Sentences with [N]: {int(gr * len(sentences))}")
        print(f"  Grounded ratio: {gr:.2%}")
        
        if gr < 0.6:
            print("  ⚠️  WARNING: Low citation coverage (<60%)")
        elif gr < 0.8:
            print("  ⚡ Good coverage, room for improvement")
        else:
            print("  ✅ EXCELLENT citation coverage!")
        
        print("\n" + "="*80)
        print("✅ QUICK TEST COMPLETE")
        print("="*80)
        print("\nTo run full evaluation:")
        print("  python eval_rag_nasa.py")
        
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
