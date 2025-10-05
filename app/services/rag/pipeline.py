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
        2. Enhance filters with auto-extracted tags from query
        3. Retrieval con filtros
        4. Build context
        5. LLM synthesis
        6. Extract citations
        7. Return response con métricas
        """
        start_time = time()
        
        # 1. Embedding (síncrono, muy rápido en CPU)
        logger.info(f"🔍 Query: {query[:100]}...")
        query_vec = self._get_embedding(query)
        
        # 1.5. Auto-extract tags from query and merge with existing filters
        enhanced_filters = self._enhance_filters_with_query_tags(query, filters)
        
        # 2. Retrieval
        chunks = self.retriever.retrieve(query_vec, enhanced_filters, top_k)
        if not chunks:
            return self._empty_response(query, enhanced_filters, session_id)
        
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
            used_filters=enhanced_filters,
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
    
    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """Extract title from text content - usually the first line or after 'Title:'"""
        if not text:
            return None
        
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with "Title:"
            if line.lower().startswith('title:'):
                title = line[6:].strip()
                if title:
                    return title
            
            # If first substantial line (> 10 chars), consider it the title
            if len(line) > 10 and not line.startswith(('Abstract', 'Keywords', 'Authors')):
                return line
        
        return None
    
    def _extract_citations(self, chunks: list[Dict[str, Any]]) -> list[Citation]:
        """Extraer citations de chunks con información completa de metadata"""
        citations = []
        for idx, chunk in enumerate(chunks, start=1):
            # Snippet: primeras 200 chars
            snippet = chunk.get("text", "")[:200] + "..."
            
            # Extract title from text if not available in metadata
            title = chunk.get("title")
            if not title:
                title = self._extract_title_from_text(chunk.get("text", ""))
            
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
            
            # Get metadata object
            metadata = chunk.get("metadata", {})
            
            # Extract URLs - prioritize source_url from metadata or document
            source_url = chunk.get("source_url") or metadata.get("source_url")
            url = chunk.get("url") or metadata.get("url") or source_url
            
            citations.append(Citation(
                # Document identifiers
                document_id=str(chunk.get("_id")) if chunk.get("_id") else None,
                source_id=chunk.get("source_id", f"chunk_{idx}"),
                doi=chunk.get("doi"),
                osdr_id=chunk.get("osdr_id"),
                
                # Content fields
                section=section,
                snippet=snippet,
                title=title,
                
                # URLs and links
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
                created_at=chunk.get("created_at"),
                
                # Full metadata object
                metadata=metadata,
                
                # Scoring and relevance information
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
    
    def _enhance_filters_with_query_tags(self, query: str, filters: Optional[FilterFacets]) -> FilterFacets:
        """
        Extract relevant tags from user query and merge with existing filters.
        Uses keyword matching and domain-specific tag extraction.
        """
        # Domain-specific keywords mapping to tags
        keyword_to_tags = {
            # Biological systems
            "bone": ["bone", "skeleton", "musculoskeletal"],
            "muscle": ["muscle", "musculoskeletal", "skeletal"],
            "brain": ["brain", "neurological", "central-nervous"],
            "heart": ["cardiovascular", "cardiac", "heart"],
            "immune": ["immune", "immunology", "defense"],
            "kidney": ["renal", "kidney", "urinary"],
            "liver": ["hepatic", "liver", "metabolism"],
            "lung": ["pulmonary", "respiratory", "lung"],
            "eye": ["ocular", "vision", "sensory"],
            
            # Space conditions
            "microgravity": ["microgravity", "weightlessness", "gravity"],
            "radiation": ["radiation", "cosmic", "ionizing"],
            "space": ["space", "spaceflight", "mission"],
            "iss": ["iss", "station", "orbital"],
            "mars": ["mars", "planetary", "deep-space"],
            
            # Biological processes
            "gene": ["genomics", "gene-expression", "molecular"],
            "protein": ["proteomics", "protein", "molecular"],
            "cell": ["cellular", "cytology", "cell-biology"],
            "metabolism": ["metabolism", "biochemistry", "energy"],
            "development": ["development", "growth", "morphology"],
            
            # Research areas
            "biomedical": ["biomedical", "medical", "clinical"],
            "tissue": ["tissue", "histology", "pathology"],
            "behavior": ["behavioral", "psychology", "neurobehavior"],
        }
        
        # Extract tags from query (case insensitive)
        query_lower = query.lower()
        extracted_tags = []
        
        for keyword, tags in keyword_to_tags.items():
            if keyword in query_lower:
                extracted_tags.extend(tags)
        
        # Remove duplicates while preserving order
        extracted_tags = list(dict.fromkeys(extracted_tags))
        
        # Create enhanced filters
        if filters is None:
            filters = FilterFacets()
        
        # Merge with existing tags
        existing_tags = filters.tags or []
        all_tags = existing_tags + extracted_tags
        
        # Remove duplicates and limit to top 10 for performance
        unique_tags = list(dict.fromkeys(all_tags))[:10]
        
        # Create new FilterFacets with enhanced tags
        enhanced_filters = FilterFacets(
            organism=filters.organism,
            system=filters.system,
            mission_env=filters.mission_env,
            year_range=filters.year_range,
            exposure=filters.exposure,
            assay=filters.assay,
            tissue=filters.tissue,
            tags=unique_tags if unique_tags else None
        )
        
        if extracted_tags:
            logger.info(f"🏷️ Auto-extracted tags from query: {extracted_tags}")
        
        return enhanced_filters


# Singleton
_pipeline: Optional[RAGPipeline] = None

def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
