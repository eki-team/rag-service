"""
NASA Biology RAG - Advanced Pipeline
====================================

Orquesta retrieval avanzado + reranking multi-señal + síntesis estricta con citas.

Características:
- Query expansion con TAG_DICT
- Reranking con múltiples señales (section, authority, recency, diversity, etc.)
- Síntesis estricta (solo información del contexto + citas obligatorias)
- Métricas de calidad (faithfulness, relevancy, grounding)
"""

from typing import Optional, Dict, Any, List
from time import time
import httpx
import re
from collections import Counter

from app.schemas.chat import FilterFacets, ChatResponse, Citation, RetrievalMetrics
from app.services.rag.repository import get_repository_service
from app.services.rag.retriever import Retriever
from app.services.rag.context_builder import ContextBuilder
from app.services.rag.prompts.free_nasa import SYNTHESIS_PROMPT
from app.services.rag.tag_dict import get_expanded_terms, get_matched_keys, expand_query_text
from app.services.rag.reranker import AdvancedReranker
from app.services.embeddings import get_embeddings_service
from app.core.settings import settings

import logging

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Pipeline completo de RAG con expansión de query y reranking avanzado"""
    
    def __init__(self):
        self.repo_service = get_repository_service()
        self.retriever = Retriever(self.repo_service.repo)
        self.context_builder = ContextBuilder(max_tokens=4000)  # Aumentado para mejor contexto
        self.embeddings = get_embeddings_service()
        
        # Parámetros configurables (pueden sobreescribirse)
        self.TOP_K = 40          # Candidate set inicial
        self.TOP_RERANK = 12     # Pasajes para reranking
        self.TOP_SYNTHESIS = 6   # Pasajes finales para síntesis
    
    async def answer(
        self,
        query: str,
        filters: Optional[FilterFacets] = None,
        top_k: int = 8,
        session_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Proceso completo de RAG avanzado:
        
        1. Query Expansion con TAG_DICT
        2. Embedding de query expandida
        3. Retrieval híbrido (TOP_K candidatos)
        4. Advanced Reranking con múltiples señales (TOP_RERANK → TOP_SYNTHESIS)
        5. Context Building
        6. LLM Synthesis con citas estrictas
        7. Citation Extraction
        8. Metrics & Response
        """
        start_time = time()
        
        # ===========================================================================
        # FASE 1: QUERY EXPANSION
        # ===========================================================================
        logger.info(f"🔍 Original query: {query[:100]}...")
        
        # Detectar términos del TAG_DICT en la query
        matched_keys = get_matched_keys(query)
        expanded_terms = get_expanded_terms(query)
        
        if matched_keys:
            logger.info(f"🏷️  TAG_DICT matches: {matched_keys}")
            logger.info(f"📝 Expanded terms: {list(expanded_terms)[:10]}...")  # Primeros 10
        
        # Construir query expandida (para embedding)
        query_expanded = expand_query_text(query)
        
        # ===========================================================================
        # FASE 2: EMBEDDING
        # ===========================================================================
        query_vec = self._get_embedding(query_expanded)
        
        # ===========================================================================
        # FASE 3: RETRIEVAL (TOP_K candidatos)
        # ===========================================================================
        # Usar TOP_K para recuperación inicial (más candidatos = mejor reranking)
        retrieval_k = self.TOP_K if self.TOP_K > top_k else top_k * 3
        
        chunks = self.retriever.retrieve(query_vec, filters, retrieval_k)
        
        if not chunks:
            return self._empty_response(query, filters, session_id)
        
        logger.info(f"📚 Retrieved {len(chunks)} initial candidates")
        
        # ===========================================================================
        # FASE 4: ADVANCED RERANKING
        # ===========================================================================
        reranker = AdvancedReranker(
            query=query,
            expanded_terms=expanded_terms,
            top_rerank=self.TOP_RERANK,
            top_synthesis=self.TOP_SYNTHESIS,
        )
        
        reranked_chunks = reranker.rerank(chunks)
        logger.info(f"🔄 Reranked to {len(reranked_chunks)} chunks for synthesis")
        
        # ===========================================================================
        # FASE 5: CONTEXT BUILDING
        # ===========================================================================
        context = self.context_builder.build_context(reranked_chunks)
        
        # ===========================================================================
        # FASE 6: LLM SYNTHESIS (con citas estrictas)
        # ===========================================================================
        logger.info("🤖 Generating answer with strict citations...")
        answer = await self._synthesize(query, context)
        
        # ===========================================================================
        # FASE 7: CITATIONS
        # ===========================================================================
        citations = self._extract_citations(reranked_chunks)
        
        # ===========================================================================
        # FASE 8: METRICS
        # ===========================================================================
        # Calculate grounding ratio (% de claims con citas)
        grounded_ratio = self._estimate_grounding(answer, citations)
        
        latency_ms = (time() - start_time) * 1000
        section_dist = Counter(c.get("section") for c in reranked_chunks if c.get("section"))
        
        metrics = RetrievalMetrics(
            latency_ms=round(latency_ms, 2),
            retrieved_k=len(reranked_chunks),
            grounded_ratio=grounded_ratio,
            dedup_count=len(chunks) - len(reranked_chunks),
            section_distribution=dict(section_dist),
        )
        
        logger.info(f"✅ Pipeline completed in {latency_ms:.0f}ms (grounding: {grounded_ratio:.1%})")
        
        # ===========================================================================
        # RESPONSE
        # ===========================================================================
        return ChatResponse(
            answer=answer,
            citations=citations,
            metrics=metrics,
            session_id=session_id,
        )
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generar embedding con OpenAI text-embedding-3-small (1536 dims)"""
        return self.embeddings.encode_query(text)
    
    async def _synthesize(self, query: str, context: str) -> str:
        """
        Síntesis con OpenAI usando el SYNTHESIS_PROMPT estricto.
        El prompt enforcea citas obligatorias y faithfulness.
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        prompt = SYNTHESIS_PROMPT.format(context=context, query=query)
        
        payload = {
            "model": settings.OPENAI_CHAT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a NASA space biology research assistant. "
                        "You MUST cite sources using [N] format for EVERY factual claim. "
                        "You MUST NOT use external knowledge. "
                        "Only write what the context explicitly states."
                    )
                },
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
    
    def _extract_citations(self, chunks: List[Dict[str, Any]]) -> List[Citation]:
        """
        Extraer citations de chunks con información completa de metadata.
        Incluye scoring signals del reranker para transparencia.
        """
        citations = []
        
        for idx, chunk in enumerate(chunks, start=1):
            # Snippet: primeras 200 caracteres
            snippet = chunk.get("text", "")[:200] + "..."
            
            # Título
            title = chunk.get("title") or self._extract_title_from_text(chunk.get("text", ""))
            
            # Scoring information (del reranker)
            rerank_score = chunk.get("rerank_score")
            debug_signals = chunk.get("_debug_signals", {})
            
            # Section
            section = chunk.get("section", "Unknown")
            
            # Build relevance reason con todas las señales
            if debug_signals:
                reason = (
                    f"Sim: {debug_signals.get('sim', 0):.3f} | "
                    f"Sec: {debug_signals.get('sec_boost', 0):.3f} | "
                    f"Keyword: {debug_signals.get('keyword_overlap', 0):.3f} | "
                    f"Authority: {debug_signals.get('authority', 0):.3f} | "
                    f"Final: {debug_signals.get('final', 0):.3f}"
                )
            else:
                reason = f"Vector similarity: {chunk.get('score', 0):.3f}"
            
            # Metadata
            metadata = chunk.get("metadata", {})
            
            # URLs
            source_url = chunk.get("source_url") or metadata.get("source_url")
            url = chunk.get("url") or metadata.get("url") or source_url
            
            citations.append(Citation(
                # Identifiers
                document_id=str(chunk.get("_id")) if chunk.get("_id") else None,
                source_id=chunk.get("source_id", f"chunk_{idx}"),
                doi=chunk.get("doi"),
                osdr_id=chunk.get("osdr_id"),
                
                # Content
                section=section,
                snippet=snippet,
                text=title,
                
                # URLs
                url=url,
                source_url=source_url,
                
                # Publication metadata
                year=chunk.get("year"),
                venue=chunk.get("venue"),
                source_type=chunk.get("source_type"),
                
                # Biological metadata
                organism=chunk.get("organism"),
                system=chunk.get("system"),
                mission_env=chunk.get("mission_env"),
                exposure=chunk.get("exposure"),
                assay=chunk.get("assay"),
                tissue=chunk.get("tissue"),
                
                # Chunk metadata
                chunk_index=chunk.get("chunk_index"),
                total_chunks=chunk.get("total_chunks"),
                created_at=str(chunk.get("created_at")) if chunk.get("created_at") else None,
                
                # Full metadata
                metadata=metadata,
                
                # Scoring (reranked)
                similarity_score=round(chunk.get("score", 0), 4),
                section_boost=round(debug_signals.get("sec_boost", 0), 4) if debug_signals else None,
                final_score=round(rerank_score, 4) if rerank_score else None,
                relevance_reason=reason,
            ))
        
        return citations
    
    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """Extract title from text content"""
        if not text:
            return None
        
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
            
            if line.lower().startswith('title:'):
                title = line[6:].strip()
                if title:
                    return title
            
            if len(line) > 10 and not line.startswith(('Abstract', 'Keywords', 'Authors')):
                return line
        
        return None
    
    def _estimate_grounding(self, answer: str, citations: List[Citation]) -> float:
        """
        Estimar grounding ratio (% de sentences con citas).
        
        Heurística:
        - Contar [N] en la respuesta
        - Dividir por número de sentences
        - Cap a 1.0
        """
        citation_refs = re.findall(r'\[\d+\]', answer)
        
        if not citation_refs:
            return 0.0
        
        # Split por puntos (sentences)
        sentences = [s.strip() for s in answer.split(".") if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Ratio de sentences con al menos una cita
        sentences_with_citations = sum(
            1 for sent in sentences if re.search(r'\[\d+\]', sent)
        )
        
        ratio = sentences_with_citations / len(sentences)
        
        return min(ratio, 1.0)
    
    def _empty_response(
        self,
        query: str,
        filters: Optional[FilterFacets],
        session_id: Optional[str],
    ) -> ChatResponse:
        """Response cuando no hay chunks"""
        return ChatResponse(
            answer=(
                "No relevant results found in the NASA biology corpus for your query. "
                "Try adjusting filters, rephrasing the question, or broadening the search terms."
            ),
            citations=[],
            metrics=RetrievalMetrics(
                latency_ms=0.0,
                retrieved_k=0,
                grounded_ratio=0.0,
            ),
            session_id=session_id,
        )


# ===============================================================================
# SINGLETON
# ===============================================================================
_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
