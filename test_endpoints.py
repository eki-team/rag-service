"""
Test básico de endpoints - NASA RAG Service
"""
import httpx
import asyncio
import json


BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing GET /health...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


async def test_diag_health():
    """Test diagnostic health"""
    print("\n🔍 Testing GET /diag/health...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/diag/health")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200


async def test_embedding():
    """Test embedding endpoint"""
    print("\n🔍 Testing POST /diag/emb...")
    payload = {"text": "microgravity immune response"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/diag/emb", json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Model: {data['model']}")
                print(f"Dimensions: {data['dimensions']}")
                return True
            else:
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_chat():
    """Test chat endpoint (requires data in Cosmos)"""
    print("\n🔍 Testing POST /api/chat...")
    payload = {
        "query": "What are the effects of microgravity on immune response?",
        "top_k": 3,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/api/chat", json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Answer length: {len(data['answer'])} chars")
                print(f"Citations: {len(data['citations'])}")
                print(f"Latency: {data['metrics']['latency_ms']}ms")
                return True
            else:
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"⚠️ Error (expected if no data in Cosmos): {e}")
            return False


async def main():
    """Run all tests"""
    print("🧪 NASA RAG Service - Basic Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Health
    results.append(("Health", await test_health()))
    
    # Test 2: Diagnostic health
    results.append(("Diag Health", await test_diag_health()))
    
    # Test 3: Embedding (requires OpenAI key)
    results.append(("Embedding", await test_embedding()))
    
    # Test 4: Chat (requires Cosmos data)
    results.append(("Chat", await test_chat()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n📈 Total: {passed}/{total} passed")


if __name__ == "__main__":
    asyncio.run(main())
