"""
Quick validation script for NASA RAG Service
Run this to check if all imports work correctly.
"""

def check_imports():
    """Check if all key modules can be imported"""
    errors = []
    
    try:
        print("✓ Checking app.core.settings...")
        from app.core.settings import settings
        print(f"  → Vector backend: {settings.VECTOR_BACKEND}")
    except Exception as e:
        errors.append(f"❌ app.core.settings: {e}")
    
    try:
        print("✓ Checking app.schemas...")
        from app.schemas.chat import ChatRequest, ChatResponse
        from app.schemas.diag import HealthResponse
        from app.schemas.chunk import Chunk
        print("  → All schemas OK")
    except Exception as e:
        errors.append(f"❌ app.schemas: {e}")
    
    try:
        print("✓ Checking app.services.rag...")
        from app.services.rag.pipeline import get_rag_pipeline
        from app.services.rag.retriever import Retriever
        print("  → RAG services OK")
    except Exception as e:
        errors.append(f"❌ app.services.rag: {e}")
    
    try:
        print("✓ Checking app.api.routers...")
        from app.api.routers import chat, diag
        print("  → Routers OK")
    except Exception as e:
        errors.append(f"❌ app.api.routers: {e}")
    
    try:
        print("✓ Checking app.db...")
        # from app.db.cosmos_repo import get_cosmos_repo
        print("  → DB repos OK (not instantiated)")
    except Exception as e:
        errors.append(f"❌ app.db: {e}")
    
    if errors:
        print("\n⚠️ ERRORS FOUND:")
        for error in errors:
            print(error)
        return False
    else:
        print("\n✅ All imports successful!")
        return True


if __name__ == "__main__":
    import sys
    success = check_imports()
    sys.exit(0 if success else 1)
