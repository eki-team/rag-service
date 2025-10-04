"""
Test rápido de OpenAI embeddings
Verifica que la API key funciona y genera embeddings correctamente
"""
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.embeddings import get_embeddings_service
from app.core.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_openai_embeddings():
    """Test básico de OpenAI embeddings"""
    
    print("="*60)
    print("🧪 Testing OpenAI Embeddings")
    print("="*60)
    
    # Verificar configuración
    print(f"\n📋 Configuration:")
    print(f"  - OPENAI_API_KEY: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Missing'}")
    print(f"  - EMBEDDING_MODEL: {settings.EMBEDDING_MODEL}")
    print(f"  - EMBEDDING_DIMENSIONS: {settings.EMBEDDING_DIMENSIONS}")
    
    if not settings.OPENAI_API_KEY:
        print("\n❌ Error: OPENAI_API_KEY no está configurado en .env")
        return False
    
    try:
        # Inicializar servicio
        print("\n🔄 Initializing OpenAI embeddings service...")
        embeddings_service = get_embeddings_service()
        print(f"✅ Service initialized: {embeddings_service.model_name}")
        
        # Test 1: Embedding simple
        print("\n🧪 Test 1: Single embedding")
        test_text = "microgravity effects on immune system"
        print(f"  Text: '{test_text}'")
        
        embedding = embeddings_service.encode_query(test_text)
        print(f"  ✅ Generated embedding: {len(embedding)} dimensions")
        print(f"  Sample: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
        
        # Verificar dimensiones
        expected_dims = 1536
        if len(embedding) != expected_dims:
            print(f"  ❌ Error: Expected {expected_dims} dims, got {len(embedding)}")
            return False
        
        # Test 2: Múltiples embeddings
        print("\n🧪 Test 2: Batch embeddings")
        test_texts = [
            "spaceflight effects on bone density",
            "radiation exposure in deep space",
            "plant growth in microgravity"
        ]
        print(f"  Processing {len(test_texts)} texts...")
        
        embeddings = embeddings_service.encode_documents(test_texts, batch_size=10)
        print(f"  ✅ Generated {len(embeddings)} embeddings")
        
        for i, emb in enumerate(embeddings):
            print(f"    {i+1}. {len(emb)} dims - [{emb[0]:.4f}, {emb[1]:.4f}, ...]")
        
        # Test 3: Similitud
        print("\n🧪 Test 3: Similarity calculation")
        vec1 = embeddings[0]
        vec2 = embeddings[1]
        vec3 = embeddings[2]
        
        sim_12 = embeddings_service.similarity(vec1, vec2)
        sim_13 = embeddings_service.similarity(vec1, vec3)
        sim_23 = embeddings_service.similarity(vec2, vec3)
        
        print(f"  Text 1 vs Text 2: {sim_12:.4f}")
        print(f"  Text 1 vs Text 3: {sim_13:.4f}")
        print(f"  Text 2 vs Text 3: {sim_23:.4f}")
        
        # Resumen
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"  - Model: {embeddings_service.model_name}")
        print(f"  - Dimensions: {embeddings_service.dimensions}")
        print(f"  - Single embedding: ✅")
        print(f"  - Batch embeddings: ✅")
        print(f"  - Similarity calculation: ✅")
        print("\n🚀 OpenAI embeddings are ready to use!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_openai_embeddings()
    sys.exit(0 if success else 1)
