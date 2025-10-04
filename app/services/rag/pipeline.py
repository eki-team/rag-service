"""
NASA Biology RAG - Pipeline
Orquesta retrieval + context building + LLM synthesis.
"""
from typing import Optional, Dict, Any
from time import time
import httpx
from app.schemas.chat import FilterFacets, ChatResponse, Citation, RetrievalMetrics
from app.services.rag.repository import get_repository_service
from app.services.rag.retriever import Retriever
from app.services.rag.context_builder import ContextBuilder
from app.services.rag.prompts.free_nasa import SYNTHESIS_PROMPT
from app.services.embeddings import get_embeddings_service  # Usa OpenAI embeddings (1536 dims)
from app.core.settings import settings
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Pipeline completo de RAG"""
    
    def __init__(self):
        self.repo_service = get_repository_service()
        self.retriever = Retriever(self.repo_service.repo)
        self.context_builder = ContextBuilder(max_tokens=3000)
        self.embeddings = get_embeddings_service()
    
    async def answer(
        self,
        query: str,
        filters: Optional[FilterFacets] = None,
        top_k: int = 8,
        session_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Proceso completo de RAG:
        1. Generar embedding de query
        2. Retrieval con filtros
        3. Build context
        4. LLM synthesis
        5. Extract citations
        6. Return response con métricas
        """
        start_time = time()
        
        # 1. Embedding (síncrono, muy rápido en CPU)
        logger.info(f"🔍 Query: {query[:100]}...")
        query_vec = self._get_embedding(query)
        
        # 2. Retrieval
        chunks = self.retriever.retrieve(query_vec, filters, top_k)
        if not chunks:
            return self._empty_response(query, filters, session_id)
        
        # 3. Build context
        context = self.context_builder.build_context(chunks)
        
        # 4. LLM synthesis
        answer = await self._synthesize(query, context)
        
        # 5. Citations
        citations = self._extract_citations(chunks)
        
        # 6. Metrics
        latency_ms = (time() - start_time) * 1000
        section_dist = Counter(c.get("section") for c in chunks if c.get("section"))
        
        metrics = RetrievalMetrics(
            latency_ms=round(latency_ms, 2),
            retrieved_k=len(chunks),
            grounded_ratio=self._estimate_grounding(answer, citations),
            dedup_count=top_k - len(chunks),  # approx
            section_distribution=dict(section_dist),
        )
        
        logger.info(f"✅ Pipeline completed in {latency_ms:.0f}ms")
        
        return ChatResponse(
            answer=answer,
            citations=citations,
            used_filters=filters,
            metrics=metrics,
            session_id=session_id,
        )
    
    def _get_embedding(self, text: str) -> list[float]:
        """
        Generar embedding usando sentence-transformers (all-MiniLM-L6-v2).
        Retorna vector de 384 dimensiones con similitud de coseno.
        Muy rápido: ~14,000 oraciones/seg en CPU.
        """
        return self.embeddings.encode_query(text)
    
    async def _synthesize(self, query: str, context: str) -> str:
        """Síntesis con OpenAI chat"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        prompt = SYNTHESIS_PROMPT.format(context=context, query=query)
        
        payload = {
            "model": settings.OPENAI_CHAT_MODEL,
            "messages": [
                {"role": "system", "content": "You are a NASA space biology research assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": settings.OPENAI_TEMPERATURE,
            "max_tokens": settings.OPENAI_MAX_TOKENS,
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def _extract_citations(self, chunks: list[Dict[str, Any]]) -> list[Citation]:
        """Extraer citations de chunks con información de scoring"""
        citations = []
        for idx, chunk in enumerate(chunks, start=1):
            # Snippet: primeras 200 chars
            snippet = chunk.get("text", "")[:200] + "..."
            
            # Extract scoring information
            similarity = chunk.get("similarity", chunk.get("base_similarity"))
            section_boost = chunk.get("section_boost", 0.0)
            final_score = chunk.get("final_score", similarity)
            section = chunk.get("section", "Unknown")
            
            # Build relevance reason
            reason_parts = []
            if similarity:
                reason_parts.append(f"Vector similarity: {similarity:.3f}")
            if section_boost > 0:
                reason_parts.append(f"Section '{section}' boost: +{section_boost:.3f}")
            if final_score:
                reason_parts.append(f"Final score: {final_score:.3f}")
            
            relevance_reason = " | ".join(reason_parts) if reason_parts else "Selected by retrieval system"
            
            citations.append(Citation(
                source_id=chunk.get("source_id", f"chunk_{idx}"),
                doi=chunk.get("doi"),
                osdr_id=chunk.get("osdr_id"),
                section=section,
                snippet=snippet,
                url=chunk.get("url"),
                title=chunk.get("title"),
                year=chunk.get("year"),
                similarity_score=round(similarity, 4) if similarity else None,
                section_boost=round(section_boost, 4) if section_boost else None,
                final_score=round(final_score, 4) if final_score else None,
                relevance_reason=relevance_reason,
            ))
        return citations
    
    def _estimate_grounding(self, answer: str, citations: list[Citation]) -> float:
        """Estimar ratio de grounding (heurística: contar [N] en respuesta)"""
        import re
        citation_refs = re.findall(r'\[\d+\]', answer)
        if not citation_refs:
            return 0.0
        # Rough estimate: claims con cita / total de sentences
        sentences = answer.split(". ")
        grounded = len(citation_refs)
        total = max(len(sentences), 1)
        return min(grounded / total, 1.0)
    
    def _empty_response(self, query: str, filters: Optional[FilterFacets], session_id: Optional[str]) -> ChatResponse:
        """Response cuando no hay chunks"""
        return ChatResponse(
            answer="No relevant results found for your query. Try adjusting filters or rephrasing the question.",
            citations=[],
            used_filters=filters,
            metrics=RetrievalMetrics(
                latency_ms=0.0,
                retrieved_k=0,
                grounded_ratio=0.0,
            ),
            session_id=session_id,
        )


# Singleton
_pipeline: Optional[RAGPipeline] = None

def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
