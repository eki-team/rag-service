"""
NASA Biology RAG - Retriever
Búsqueda híbrida con ponderación por sección y dedup.
"""
from typing import List, Dict, Any, Optional
from app.schemas.chat import FilterFacets
from app.core.constants import SECTION_PRIORITY
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)


class Retriever:
    """Retriever con ponderación por sección y filtros"""
    
    def __init__(self, repo):
        self.repo = repo
    
    def retrieve(
        self,
        query_vec: List[float],
        filters: Optional[FilterFacets] = None,
        top_k: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Recuperar chunks con filtros y re-ranking por sección.
        
        Steps:
        1. Vector search con filtros
        2. Re-ranking por prioridad de sección (Results > Conclusion > Methods > Intro)
        3. Dedup por DOI/source_id
        4. Return top_k
        """
        # 1. Vector search
        filter_dict = self._filters_to_dict(filters) if filters else None
        chunks = self.repo.search_vectors(
            query_vec=query_vec,
            filters=filter_dict,
            top_k=top_k * 2,  # Obtener más para tener margen después de dedup
            min_similarity=settings.MIN_SIMILARITY,
        )
        
        if not chunks:
            logger.warning("⚠️ No chunks retrieved from vector search")
            return []
        
        logger.info(f"📦 Retrieved {len(chunks)} chunks before re-ranking")
        
        # 2. Re-ranking por sección
        for chunk in chunks:
            section = chunk.get("section", "")
            section_score = SECTION_PRIORITY.get(section, 0)
            base_similarity = chunk.get("similarity", 0.0)
            
            # Boost por sección: Results +0.1, Conclusion +0.05, etc.
            boost = section_score * 0.025
            chunk["final_score"] = base_similarity + boost
        
        chunks.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 3. Dedup por DOI (mantener el chunk con mejor score)
        seen_dois = set()
        deduped = []
        for chunk in chunks:
            doi = chunk.get("doi")
            if doi and doi in seen_dois:
                continue
            if doi:
                seen_dois.add(doi)
            deduped.append(chunk)
        
        logger.info(f"🧹 After dedup: {len(deduped)} chunks")
        
        # 4. Return top_k
        result = deduped[:top_k]
        logger.info(f"✅ Final retrieval: {len(result)} chunks")
        return result
    
    def _filters_to_dict(self, filters: FilterFacets) -> Dict[str, Any]:
        """Convertir FilterFacets a dict para el repo"""
        filter_dict = {}
        if filters.organism:
            filter_dict["organism"] = filters.organism
        if filters.system:
            filter_dict["system"] = filters.system
        if filters.mission_env:
            filter_dict["mission_env"] = filters.mission_env
        if filters.exposure:
            filter_dict["exposure"] = filters.exposure
        if filters.assay:
            filter_dict["assay"] = filters.assay
        if filters.tissue:
            filter_dict["tissue"] = filters.tissue
        if filters.year_range:
            filter_dict["year_range"] = filters.year_range
        return filter_dict
