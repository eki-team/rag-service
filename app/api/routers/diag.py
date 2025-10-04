"""
NASA Biology RAG - Diagnostic Router
Endpoints /diag/* para health, embeddings, retrieval, audit.
"""
from fastapi import APIRouter, HTTPException, Query
from app.schemas.diag import (
    HealthResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalChunk,
    AuditResponse,
    AuditResult,
)
from app.core.settings import settings
from app.services.rag.repository import get_repository_service
from app.services.rag.pipeline import get_rag_pipeline
import httpx
import logging
import json
from pathlib import Path
from time import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diag", tags=["diagnostics"])


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check del servicio"""
    try:
        repo_service = get_repository_service()
        is_healthy = repo_service.health_check()
        
        return HealthResponse(
            status="ok" if is_healthy else "degraded",
            service="nasa-rag",
            vector_backend=settings.VECTOR_BACKEND,
            models={
                "chat": settings.OPENAI_CHAT_MODEL,
                "embed": f"{settings.EMBEDDING_MODEL} (OpenAI, {settings.EMBEDDING_DIMENSIONS}D)",
            },
            nasa_mode=settings.NASA_MODE,
            guided_enabled=settings.NASA_GUIDED_ENABLED,
        )
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return HealthResponse(
            status="error",
            service="nasa-rag",
            vector_backend=settings.VECTOR_BACKEND,
            models={},
            nasa_mode=settings.NASA_MODE,
            guided_enabled=False,
        )


@router.post("/emb", response_model=EmbeddingResponse)
async def get_embedding(request: EmbeddingRequest):
    """Generar embedding de un texto usando OpenAI (debug)"""
    try:
        from app.services.embeddings import get_embeddings_service
        
        emb_service = get_embeddings_service()
        embedding = emb_service.encode_query(request.text)
        
        return EmbeddingResponse(
            text=request.text,
            embedding=embedding,
            model=settings.EMBEDDING_MODEL,
            dimensions=len(embedding),
        )
    
    except Exception as e:
        logger.error(f"❌ Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieval", response_model=RetrievalResponse)
async def test_retrieval(request: RetrievalRequest):
    """Test de retrieval (sin síntesis LLM)"""
    try:
        start = time()
        pipeline = get_rag_pipeline()
        
        # Generar embedding (síncrono, rápido)
        query_vec = pipeline._get_embedding(request.query)
        
        # Retrieval
        from app.schemas.chat import FilterFacets
        filters_obj = FilterFacets(**request.filters) if request.filters else None
        
        chunks = pipeline.retriever.retrieve(
            query_vec=query_vec,
            filters=filters_obj,
            top_k=request.top_k,
        )
        
        # Formatear response
        retrieval_chunks = []
        for chunk in chunks:
            retrieval_chunks.append(RetrievalChunk(
                source_id=chunk.get("source_id", ""),
                title=chunk.get("title", ""),
                section=chunk.get("section"),
                doi=chunk.get("doi"),
                osdr_id=chunk.get("osdr_id"),
                similarity=chunk.get("final_score", 0.0),
                text=chunk.get("text", "")[:500],  # Limitar texto
                metadata={
                    "organism": chunk.get("organism"),
                    "mission_env": chunk.get("mission_env"),
                    "year": chunk.get("year"),
                    "exposure": chunk.get("exposure"),
                },
            ))
        
        latency = (time() - start) * 1000
        
        return RetrievalResponse(
            query=request.query,
            chunks=retrieval_chunks,
            latency_ms=round(latency, 2),
            total_found=len(chunks),
        )
    
    except Exception as e:
        logger.error(f"❌ Retrieval test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieval_audit", response_model=AuditResponse)
async def retrieval_audit():
    """
    Audit de retrieval usando queries doradas.
    Lee CONTEXT/golden_queries.json y evalúa recall@k.
    """
    try:
        # Cargar golden queries
        golden_path = Path("CONTEXT/golden_queries.json")
        if not golden_path.exists():
            logger.warning("⚠️ golden_queries.json not found, returning empty audit")
            return AuditResponse(queries=[], avg_recall=0.0, avg_precision=0.0)
        
        with open(golden_path, "r") as f:
            golden_queries = json.load(f)
        
        pipeline = get_rag_pipeline()
        results = []
        
        for query_data in golden_queries:
            query_id = query_data["id"]
            query_text = query_data["query"]
            expected_sources = set(query_data["expected_sources"])
            filters = query_data.get("filters")
            
            # Retrieval
            query_vec = await pipeline._get_embedding(query_text)
            from app.schemas.chat import FilterFacets
            filters_obj = FilterFacets(**filters) if filters else None
            
            chunks = pipeline.retriever.retrieve(
                query_vec=query_vec,
                filters=filters_obj,
                top_k=8,
            )
            
            retrieved_sources = set(c.get("source_id", "") for c in chunks)
            
            # Calcular recall y precision
            tp = len(expected_sources & retrieved_sources)
            recall = tp / len(expected_sources) if expected_sources else 0.0
            precision = tp / len(retrieved_sources) if retrieved_sources else 0.0
            
            missing = list(expected_sources - retrieved_sources)
            
            results.append(AuditResult(
                query_id=query_id,
                recall_at_k=round(recall, 3),
                precision_at_k=round(precision, 3),
                retrieved=list(retrieved_sources),
                expected=list(expected_sources),
                missing=missing,
            ))
        
        # Promedios
        avg_recall = sum(r.recall_at_k for r in results) / len(results) if results else 0.0
        avg_precision = sum(r.precision_at_k for r in results) / len(results) if results else 0.0
        
        logger.info(f"📊 Audit: avg_recall={avg_recall:.2f}, avg_precision={avg_precision:.2f}")
        
        return AuditResponse(
            queries=results,
            avg_recall=round(avg_recall, 3),
            avg_precision=round(avg_precision, 3),
        )
    
    except Exception as e:
        logger.error(f"❌ Audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mongo/health")
async def mongodb_health():
    """
    🔍 **Health check detallado de MongoDB**
    
    Verifica la conexión, acceso a la base de datos, y estado del cluster.
    
    **Response:**
    ```json
    {
      "status": "connected",
      "connection_type": "mongodb",
      "database": "nasakb",
      "collection": "chunks",
      "server_info": {
        "version": "7.0.0",
        "connection": "nasakb-shard-00-00.mongodb.net:27017"
      },
      "stats": {
        "collections": 5,
        "documents": 1234,
        "indexes": 3
      },
      "latency_ms": 45.2
    }
    ```
    """
    try:
        from app.db.mongo_repo import get_mongo_repo
        from time import time
        
        logger.info("🔍 Checking MongoDB health...")
        start = time()
        
        # Obtener repositorio
        repo = get_mongo_repo()
        
        # Test 1: Ping básico
        try:
            ping_result = repo.client.admin.command('ping')
            ping_ok = ping_result.get('ok') == 1
        except Exception as e:
            logger.error(f"❌ MongoDB ping failed: {e}")
            return {
                "status": "error",
                "error": f"Connection failed: {str(e)}",
                "connection_type": settings.VECTOR_BACKEND,
                "database": settings.MONGODB_DB,
                "collection": settings.MONGODB_COLLECTION,
            }
        
        # Test 2: Server info
        try:
            server_info = repo.client.server_info()
            version = server_info.get('version', 'unknown')
        except Exception as e:
            version = f"error: {e}"
        
        # Test 3: Obtener host conectado
        try:
            connection_info = repo.client.admin.command('whatsmyuri')
            connected_host = connection_info.get('you', 'unknown')
        except Exception as e:
            connected_host = f"error: {e}"
        
        # Test 4: Database stats
        try:
            db = repo.client[settings.MONGODB_DB]
            
            # Lista de colecciones
            collections = db.list_collection_names()
            collections_count = len(collections)
            
            # Contar documentos en la colección principal
            if settings.MONGODB_COLLECTION in collections:
                doc_count = repo.collection.count_documents({})
                
                # Contar índices
                indexes = list(repo.collection.list_indexes())
                indexes_count = len(indexes)
                index_names = [idx.get('name') for idx in indexes]
            else:
                doc_count = 0
                indexes_count = 0
                index_names = []
                logger.warning(f"⚠️ Collection '{settings.MONGODB_COLLECTION}' not found")
            
            # Database stats generales
            db_stats = db.command('dbStats')
            db_size = db_stats.get('dataSize', 0)
            
        except Exception as e:
            logger.error(f"❌ Error getting DB stats: {e}")
            collections_count = 0
            doc_count = 0
            indexes_count = 0
            index_names = []
            db_size = 0
        
        # Test 5: Vector index status
        vector_index_exists = False
        try:
            if settings.MONGODB_COLLECTION in collections:
                indexes = list(repo.collection.list_indexes())
                vector_index_exists = any(
                    idx.get('name') == settings.MONGODB_VECTOR_INDEX 
                    for idx in indexes
                )
        except Exception as e:
            logger.warning(f"⚠️ Could not check vector index: {e}")
        
        # Calcular latencia
        latency_ms = round((time() - start) * 1000, 2)
        
        # Respuesta
        response = {
            "status": "connected" if ping_ok else "error",
            "connection_type": settings.VECTOR_BACKEND,
            "database": settings.MONGODB_DB,
            "collection": settings.MONGODB_COLLECTION,
            "server_info": {
                "version": version,
                "connected_to": connected_host,
                "mongodb_uri": settings.MONGODB_URI.replace(
                    f"admin:{settings.MONGO_PASSWORD}@", 
                    "admin:***@"
                ) if hasattr(settings, 'MONGO_PASSWORD') else "***"
            },
            "stats": {
                "collections": collections_count,
                "collections_list": collections[:10] if collections else [],  # Max 10
                "documents_in_collection": doc_count,
                "indexes": indexes_count,
                "index_names": index_names,
                "vector_index_exists": vector_index_exists,
                "vector_index_name": settings.MONGODB_VECTOR_INDEX,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2)
            },
            "latency_ms": latency_ms,
            "healthy": ping_ok and doc_count > 0
        }
        
        logger.info(f"✅ MongoDB health check completed: {latency_ms}ms, {doc_count} docs")
        return response
    
    except Exception as e:
        logger.error(f"❌ MongoDB health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "connection_type": settings.VECTOR_BACKEND,
            "database": settings.MONGODB_DB,
            "collection": settings.MONGODB_COLLECTION,
            "healthy": False
        }
