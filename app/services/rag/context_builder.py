"""
NASA Biology RAG - Context Builder
Agrupa chunks, limita tokens, extrae evidence quotes.
"""
from typing import List, Dict, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Construye contexto para el LLM a partir de chunks"""
    
    def __init__(self, max_tokens: int = 3000):
        self.max_tokens = max_tokens
    
    def build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Construir contexto estructurado a partir de chunks.
        
        Format:
        [1] Title: ...
        DOI: ... | OSDR: ... | Section: Results
        Text: ...
        
        [2] Title: ...
        ...
        """
        if not chunks:
            return ""
        
        # Agrupar por paper (DOI)
        papers = self._group_by_paper(chunks)
        
        # Construir contexto con límite de tokens
        context_parts = []
        token_count = 0
        
        for idx, (doi, paper_chunks) in enumerate(papers.items(), start=1):
            # Tomar primer chunk para metadata
            first = paper_chunks[0]
            title = first.get("title", "Unknown")
            year = first.get("year", "")
            osdr = first.get("osdr_id", "")
            
            # Header
            header = f"[{idx}] {title} ({year})\n"
            header += f"DOI: {doi or 'N/A'} | OSDR: {osdr or 'N/A'}\n"
            
            # Chunks de este paper (priorizados por sección)
            for chunk in paper_chunks[:2]:  # Max 2 chunks por paper
                section = chunk.get("section", "")
                text = chunk.get("text", "")
                chunk_text = f"Section: {section}\n{text}\n\n"
                
                # Estimar tokens (rough: ~4 chars = 1 token)
                estimated_tokens = len(header + chunk_text) // 4
                if token_count + estimated_tokens > self.max_tokens:
                    logger.warning(f"⚠️ Token limit reached, stopping at paper {idx}")
                    break
                
                context_parts.append(header + chunk_text)
                token_count += estimated_tokens
                header = ""  # Solo agregar header una vez por paper
        
        context = "\n---\n".join(context_parts)
        logger.info(f"📝 Built context: ~{token_count} tokens from {len(papers)} papers")
        return context
    
    def _group_by_paper(self, chunks: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Agrupar chunks por DOI (o source_id si no hay DOI)"""
        papers = defaultdict(list)
        for chunk in chunks:
            key = chunk.get("doi") or chunk.get("source_id", "unknown")
            papers[key].append(chunk)
        return dict(papers)
    
    def extract_evidence_quotes(self, chunks: List[Dict[str, Any]], max_quotes: int = 3) -> List[str]:
        """
        Extraer las oraciones más relevantes de cada chunk (evidence quotes).
        Útil para mostrar en UI o para grounding.
        """
        quotes = []
        for chunk in chunks[:max_quotes]:
            text = chunk.get("text", "")
            # Tomar primera oración relevante (simplificado)
            sentences = text.split(". ")
            if sentences:
                quote = sentences[0] + "."
                quotes.append(quote[:200])  # Limitar a 200 chars
        return quotes
