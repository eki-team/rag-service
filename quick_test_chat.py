"""
Script rápido para probar el endpoint /api/chat sin necesidad de Postman.
Ejecutar: python quick_test_chat.py
"""
import httpx
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check"""
    print("🏥 Testing health check...")
    try:
        response = httpx.get(f"{BASE_URL}/diag/health", timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat_simple():
    """Test chat sin filtros"""
    print("\n💬 Testing simple chat...")
    
    payload = {
        "query": "What are the effects of microgravity on mice?"
    }
    
    print(f"📤 Request: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        response = httpx.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        
        data = response.json()
        print(f"\n📥 Response:")
        print(f"   Answer (preview): {data['answer'][:200]}...")
        print(f"   Citations: {len(data.get('citations', []))}")
        print(f"   Latency: {data.get('metrics', {}).get('latency_ms', 0):.2f}ms")
        print(f"   Retrieved: {data.get('metrics', {}).get('retrieved_k', 0)} chunks")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat_with_filters():
    """Test chat con filtros"""
    print("\n🔍 Testing chat with filters...")
    
    payload = {
        "query": "How does spaceflight affect immune response?",
        "filters": {
            "organism": ["Mus musculus"],
            "mission_env": ["ISS"]
        },
        "top_k": 5
    }
    
    print(f"📤 Request: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        response = httpx.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        
        data = response.json()
        print(f"\n📥 Response:")
        print(f"   Answer (preview): {data['answer'][:200]}...")
        print(f"   Citations: {len(data.get('citations', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_embedding():
    """Test embedding generation"""
    print("\n🧠 Testing embedding generation...")
    
    payload = {
        "text": "microgravity effects on immune system"
    }
    
    print(f"📤 Request: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        response = httpx.post(
            f"{BASE_URL}/diag/emb",
            json=payload,
            timeout=10
        )
        elapsed = time.time() - start
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Time: {elapsed*1000:.2f}ms")
        
        data = response.json()
        print(f"\n📥 Response:")
        print(f"   Model: {data.get('model')}")
        print(f"   Dimensions: {data.get('dimensions')}")
        print(f"   Vector (first 5): {data.get('embedding', [])[:5]}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 NASA RAG Service - Quick Test")
    print("=" * 60)
    print(f"\n🌐 Base URL: {BASE_URL}")
    print("\n⚠️  Asegúrate de que el servicio esté corriendo:")
    print("   uvicorn app.main:app --reload --port 8000")
    print("\n" + "=" * 60)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Embedding", test_embedding),
        ("Simple Chat", test_chat_simple),
        ("Chat with Filters", test_chat_with_filters),
    ]
    
    results = []
    for name, test_func in tests:
        success = test_func()
        results.append((name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\n🎯 Total: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron! El endpoint está listo para Postman.")
    else:
        print("\n⚠️  Algunos tests fallaron. Verifica que:")
        print("   1. El servicio esté corriendo (uvicorn)")
        print("   2. MongoDB esté conectado")
        print("   3. OpenAI API key esté configurada")
        print("   4. El modelo de embeddings esté cargado")

if __name__ == "__main__":
    main()
