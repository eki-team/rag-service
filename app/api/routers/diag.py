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
                "embed": settings.OPENAI_EMBED_MODEL,
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
    """Generar embedding de un texto (debug)"""
    try:
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "input": request.text,
            "model": settings.OPENAI_EMBED_MODEL,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            embedding = data["data"][0]["embedding"]
        
        return EmbeddingResponse(
            text=request.text,
            embedding=embedding,
            model=settings.OPENAI_EMBED_MODEL,
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
        
        # Generar embedding
        query_vec = await pipeline._get_embedding(request.query)
        
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
