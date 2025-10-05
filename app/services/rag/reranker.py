"""
Advanced Reranker - Multi-signal scoring for RAG
=================================================

Implementa reranking sofisticado con múltiples señales:
- Similitud semántica (vector sim)
- BM25 léxico (si disponible)
- Section boost (Abstract > Results > Discussion > ...)
- Keyword overlap (query + expanded terms)
- Recency (preferir papers recientes)
- Authority (fuentes .nasa.gov, venues reconocidos)
- Diversity (penalizar duplicados semánticos)
- Length fit (penalizar chunks muy cortos/largos)

Fórmula final:
final_score = 0.36*sim + 0.18*bm25 + 0.14*keyword_overlap + 0.12*sec_boost 
              + 0.08*recency + 0.07*authority + 0.05*length_fit - 0.10*duplicate_penalty
"""

import re
from typing import List, Dict, Any, Set
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Section priority mapping (highest to lowest)
SECTION_PRIORITY = {
    "abstract": 0.10,
    "results": 0.10,
    "discussion": 0.07,
    "conclusion": 0.07,
    "methods": 0.03,
    "introduction": 0.03,
    "materials and methods": 0.03,
    "background": 0.02,
    "appendix": 0.00,
    "references": 0.00,
    "supplementary": 0.00,
}

# Authority domains and keywords
AUTHORITY_DOMAINS = {
    "nasa.gov": 0.07,
    "nih.gov": 0.05,
    "nature.com": 0.06,
    "science.org": 0.06,
    "cell.com": 0.05,
    "plos.org": 0.04,
    "doi.org": 0.02,
}

# Pesos del reranker
WEIGHTS = {
    "sim": 0.36,
    "bm25": 0.18,
    "keyword_overlap": 0.14,
    "sec_boost": 0.12,
    "recency": 0.08,
    "authority": 0.07,
    "length_fit": 0.05,
    "duplicate_penalty": -0.10,
}


class AdvancedReranker:
    """Reranker con múltiples señales de calidad"""
    
    def __init__(
        self,
        query: str,
        expanded_terms: Set[str],
        top_rerank: int = 12,
        top_synthesis: int = 6,
    ):
        self.query = query.lower()
        self.expanded_terms = expanded_terms
        self.top_rerank = top_rerank
        self.top_synthesis = top_synthesis
        self.query_tokens = set(self._tokenize(query))
        self.expanded_tokens = set(self._tokenize(" ".join(expanded_terms)))
        
    def rerank(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rerank chunks con múltiples señales y selecciona TOP_SYNTHESIS.
        
        Args:
            chunks: Lista de chunks con metadata (score, text, section, etc.)
        
        Returns:
            Lista de chunks reranked y filtrados (TOP_SYNTHESIS)
        """
        if not chunks:
            return []
        
        # 1. Calcular scores para cada chunk
        scored_chunks = []
        for chunk in chunks:
            final_score = self._calculate_final_score(chunk, chunks)
            chunk["rerank_score"] = final_score
            chunk["rerank_signals"] = chunk.get("_debug_signals", {})  # Para debugging
            scored_chunks.append(chunk)
        
        # 2. Ordenar por final_score
        scored_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # 3. Tomar TOP_RERANK
        top_reranked = scored_chunks[:self.top_rerank]
        
        # 4. Enforce diversidad de fuentes (máx 2 por documento)
        diverse_chunks = self._enforce_diversity(top_reranked)
        
        # 5. Seleccionar TOP_SYNTHESIS
        final_chunks = diverse_chunks[:self.top_synthesis]
        
        logger.info(f"🔄 Reranked {len(chunks)} → {len(top_reranked)} → {len(final_chunks)} chunks")
        
        return final_chunks
    
    def _calculate_final_score(
        self,
        chunk: Dict[str, Any],
        all_chunks: List[Dict[str, Any]],
    ) -> float:
        """Calcula el score final con todas las señales"""
        
        # Similitud semántica (normalizada a [0,1])
        sim = chunk.get("score", 0.0)
        if sim > 1.0:  # Si es cosine similarity sin normalizar
            sim = (sim + 1.0) / 2.0
        
        # BM25 (si está disponible, normalizado a [0,1])
        bm25 = chunk.get("bm25_score", 0.0)
        bm25 = min(1.0, bm25 / 10.0)  # Normalizar asumiendo max ~10
        
        # Section boost
        sec_boost = self._section_boost(chunk)
        
        # Keyword overlap
        keyword_overlap = self._keyword_overlap(chunk)
        
        # Recency
        recency = self._recency_score(chunk)
        
        # Authority
        authority = self._authority_score(chunk)
        
        # Length fit
        length_fit = self._length_fit(chunk)
        
        # Duplicate penalty
        duplicate_penalty = self._duplicate_penalty(chunk, all_chunks)
        
        # Fórmula ponderada
        final_score = (
            WEIGHTS["sim"] * sim
            + WEIGHTS["bm25"] * bm25
            + WEIGHTS["keyword_overlap"] * keyword_overlap
            + WEIGHTS["sec_boost"] * sec_boost
            + WEIGHTS["recency"] * recency
            + WEIGHTS["authority"] * authority
            + WEIGHTS["length_fit"] * length_fit
            + WEIGHTS["duplicate_penalty"] * duplicate_penalty
        )
        
        # Guardar señales para debugging
        chunk["_debug_signals"] = {
            "sim": round(sim, 3),
            "bm25": round(bm25, 3),
            "sec_boost": round(sec_boost, 3),
            "keyword_overlap": round(keyword_overlap, 3),
            "recency": round(recency, 3),
            "authority": round(authority, 3),
            "length_fit": round(length_fit, 3),
            "duplicate_penalty": round(duplicate_penalty, 3),
            "final": round(final_score, 3),
        }
        
        return final_score
    
    def _section_boost(self, chunk: Dict[str, Any]) -> float:
        """Boost por sección según SECTION_PRIORITY"""
        section = chunk.get("section", "").lower()
        for key, boost in SECTION_PRIORITY.items():
            if key in section:
                return boost
        return 0.0
    
    def _keyword_overlap(self, chunk: Dict[str, Any]) -> float:
        """Solapamiento de tokens de query + expanded_terms con el chunk"""
        text = chunk.get("text", "").lower()
        chunk_tokens = set(self._tokenize(text))
        
        # Combinar tokens de query y expanded
        all_query_tokens = self.query_tokens | self.expanded_tokens
        
        if not all_query_tokens:
            return 0.0
        
        # Jaccard similarity
        overlap = len(all_query_tokens & chunk_tokens)
        return min(1.0, overlap / len(all_query_tokens))
    
    def _recency_score(self, chunk: Dict[str, Any]) -> float:
        """Score de recencia (preferir papers recientes, saturar a +0.05)"""
        date_str = chunk.get("date") or chunk.get("year")
        if not date_str:
            return 0.0
        
        try:
            # Intentar parsear fecha
            if isinstance(date_str, int):
                year = date_str
            elif "-" in str(date_str):
                year = int(str(date_str).split("-")[0])
            else:
                year = int(date_str)
            
            current_year = datetime.now().year
            age = current_year - year
            
            # Papers recientes (≤2 años): +0.05
            # Papers viejos (>10 años): 0.0
            if age <= 2:
                return 0.05
            elif age <= 5:
                return 0.03
            elif age <= 10:
                return 0.01
            else:
                return 0.0
        except:
            return 0.0
    
    def _authority_score(self, chunk: Dict[str, Any]) -> float:
        """Score de autoridad (fuentes confiables)"""
        url = chunk.get("url", "").lower()
        doi = chunk.get("doi", "").lower()
        source = chunk.get("source", "").lower()
        
        # Chequear dominios de autoridad
        for domain, boost in AUTHORITY_DOMAINS.items():
            if domain in url or domain in doi or domain in source:
                return boost
        
        return 0.0
    
    def _length_fit(self, chunk: Dict[str, Any]) -> float:
        """Penalizar chunks muy cortos o muy largos"""
        text = chunk.get("text", "")
        length = len(text)
        
        # Ideal: 300-800 caracteres
        if 300 <= length <= 800:
            return 0.02
        elif 150 <= length < 300 or 800 < length <= 1200:
            return 0.00
        else:
            return -0.02
    
    def _duplicate_penalty(
        self,
        chunk: Dict[str, Any],
        all_chunks: List[Dict[str, Any]],
    ) -> float:
        """Penalizar duplicados semánticos (similitud >0.95 con otro chunk mejor rankeado)"""
        chunk_text = chunk.get("text", "").lower()
        chunk_tokens = set(self._tokenize(chunk_text))
        
        if not chunk_tokens:
            return 0.0
        
        # Comparar con chunks anteriores (mejor rankeados)
        for other in all_chunks:
            if other is chunk:
                continue
            
            other_text = other.get("text", "").lower()
            other_tokens = set(self._tokenize(other_text))
            
            if not other_tokens:
                continue
            
            # Jaccard similarity
            intersection = len(chunk_tokens & other_tokens)
            union = len(chunk_tokens | other_tokens)
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.95:
                    return -0.05
        
        return 0.0
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenizar texto (split por espacios y puntuación)"""
        return re.findall(r'\b\w+\b', text.lower())
    
    def _enforce_diversity(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enforce diversidad de fuentes: máximo 2 chunks por documento.
        Intenta cubrir ≥3 fuentes distintas si es posible.
        """
        doc_counts = defaultdict(int)
        diverse = []
        
        for chunk in chunks:
            # Identificador de documento (DOI, URL o source_id)
            doc_id = (
                chunk.get("doi")
                or chunk.get("url")
                or chunk.get("source_id", "").split("_chunk_")[0]
            )
            
            if doc_counts[doc_id] < 2:
                diverse.append(chunk)
                doc_counts[doc_id] += 1
        
        # Log diversidad
        num_sources = len(doc_counts)
        logger.info(f"📚 Diversity: {num_sources} unique sources")
        
        return diverse
