#!/usr/bin/env python3
"""Test script para verificar el sistema de citaciones mejorado"""

from app.services.rag.pipeline import RAGPipeline
from app.core.config import get_settings

def test_enhanced_citations():
    """Probar el sistema de citaciones mejorado"""
    try:
        print("🔍 Inicializando RAG Pipeline...")
        settings = get_settings()
        rag = RAGPipeline(settings)
        
        # Test query with space biology content
        test_query = "plant growth in microgravity"
        print(f"📝 Query: {test_query}")
        
        # Process query
        result = rag.process_query(test_query)
        
        print(f"📊 Citations encontradas: {len(result.citations)}")
        
        if result.citations:
            citation = result.citations[0]
            print("\n📑 Muestra de citación mejorada:")
            print(f"   - Document ID: {getattr(citation, 'document_id', 'N/A')}")
            print(f"   - Source URL: {getattr(citation, 'source_url', 'N/A')}")
            print(f"   - Title: {getattr(citation, 'title', 'N/A')}")
            print(f"   - Source Type: {getattr(citation, 'source_type', 'N/A')}")
            
            if hasattr(citation, 'metadata') and citation.metadata:
                print(f"   - Metadata keys: {list(citation.metadata.keys())}")
        
        print(f"\n💬 Respuesta (muestra): {result.answer[:100]}...")
        print("✅ Sistema funcionando correctamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_enhanced_citations()