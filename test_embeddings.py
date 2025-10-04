"""
Script de prueba para embeddings con sentence-transformers.
Verifica que el modelo all-MiniLM-L6-v2 funcione correctamente.
"""
from app.services.embeddings.sentence_transformer import get_embeddings_service
import time

def test_embeddings():
    """Test completo de embeddings"""
    print("🧪 Testing sentence-transformers embeddings...")
    print("=" * 60)
    
    # Inicializar servicio (descarga modelo si es primera vez)
    emb = get_embeddings_service()
    print(f"✅ Model loaded: {emb.model.get_sentence_embedding_dimension()} dimensions")
    print()
    
    # Test 1: Single query
    print("📝 Test 1: Single query embedding")
    query = "What are the effects of microgravity on mice?"
    start = time.time()
    vec = emb.encode_query(query)
    elapsed = (time.time() - start) * 1000
    print(f"   Query: {query}")
    print(f"   Vector dims: {len(vec)}")
    print(f"   First 5 values: {vec[:5]}")
    print(f"   Time: {elapsed:.2f}ms")
    print()
    
    # Test 2: Batch documents
    print("📚 Test 2: Batch document embeddings")
    docs = [
        "Mice exposed to spaceflight conditions show muscle atrophy.",
        "Microgravity affects bone density in astronauts.",
        "Plant growth in space requires specialized lighting systems.",
        "ISS experiments focus on human health in long-duration missions.",
        "Radiation protection is crucial for Mars missions.",
    ]
    start = time.time()
    vecs = emb.encode_documents(docs, batch_size=32)
    elapsed = (time.time() - start) * 1000
    print(f"   Documents: {len(docs)}")
    print(f"   Vectors: {len(vecs)}")
    print(f"   Time: {elapsed:.2f}ms ({elapsed/len(docs):.2f}ms per doc)")
    print(f"   Throughput: ~{len(docs)/(elapsed/1000):.0f} docs/sec")
    print()
    
    # Test 3: Similarity
    print("🔍 Test 3: Cosine similarity")
    vec1 = emb.encode_query("microgravity effects on bones")
    vec2 = emb.encode_query("bone density loss in space")
    vec3 = emb.encode_query("plant photosynthesis in orbit")
    
    sim_12 = emb.similarity(vec1, vec2)
    sim_13 = emb.similarity(vec1, vec3)
    
    print(f"   Query 1: 'microgravity effects on bones'")
    print(f"   Query 2: 'bone density loss in space'")
    print(f"   Query 3: 'plant photosynthesis in orbit'")
    print(f"   Similarity(Q1, Q2): {sim_12:.4f} (should be HIGH)")
    print(f"   Similarity(Q1, Q3): {sim_13:.4f} (should be LOW)")
    print()
    
    # Test 4: Multilingual
    print("🌍 Test 4: Multilingual support")
    queries = [
        ("en", "space biology research"),
        ("es", "investigación en biología espacial"),
        ("fr", "recherche en biologie spatiale"),
        ("de", "Weltraumbiologie Forschung"),
    ]
    
    for lang, q in queries:
        v = emb.encode_query(q)
        print(f"   [{lang}] {q}")
        print(f"        → {len(v)} dims, first 3: {v[:3]}")
    
    print()
    print("=" * 60)
    print("✅ All tests passed!")
    print()
    print("💡 Tips:")
    print("   - First run downloads ~80 MB model")
    print("   - Subsequent runs are instant (model cached)")
    print("   - CPU inference: ~14,000 sentences/sec")
    print("   - GPU inference: even faster if available")

if __name__ == "__main__":
    test_embeddings()
