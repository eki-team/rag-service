"""
NASA Biology RAG - Chat Schema
Request/Response para endpoint de chat.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class FilterFacets(BaseModel):
    """Filtros facetados para retrieval"""
    organism: Optional[List[str]] = None
    system: Optional[List[str]] = None
    mission_env: Optional[List[str]] = None
    year_range: Optional[tuple[int, int]] = None
    exposure: Optional[List[str]] = None
    assay: Optional[List[str]] = None
    tissue: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "organism": ["Mus musculus"],
                "mission_env": ["ISS", "LEO"],
                "year_range": [2020, 2024],
                "exposure": ["microgravity"],
                "tags": ["biomedical", "bone", "mice", "space"]
            }
        }


class Citation(BaseModel):
    """Cita de un paper usado en la respuesta"""
    # Document identifiers
    document_id: Optional[str] = Field(None, description="MongoDB document _id")
    source_id: str
    doi: Optional[str] = None
    osdr_id: Optional[str] = None
    
    # Content fields
    section: Optional[str] = None
    snippet: str = Field(..., description="Fragmento relevante del chunk")
    text: Optional[str] = None
    
    # URLs and links
    url: Optional[str] = Field(None, description="Source URL from metadata or document")
    source_url: Optional[str] = Field(None, description="Original source URL")
    
    # Publication metadata
    year: Optional[int] = None
    venue: Optional[str] = None
    source_type: Optional[str] = None
    
    # Biological metadata
    organism: Optional[str] = None
    system: Optional[str] = None
    mission_env: Optional[str] = None
    exposure: Optional[str] = None
    assay: Optional[str] = None
    tissue: Optional[str] = None
    
    # Chunk metadata
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None
    created_at: Optional[str] = None
    
    # Full metadata object
    metadata: Optional[dict] = Field(None, description="Complete metadata object from document")
    
    # Scoring and relevance information
    similarity_score: Optional[float] = Field(None, description="Vector similarity score (0-1)")
    section_boost: Optional[float] = Field(None, description="Section priority boost applied")
    final_score: Optional[float] = Field(None, description="Final ranking score (similarity + boost)")
    relevance_reason: Optional[str] = Field(None, description="Why this chunk was selected")


class ChatRequest(BaseModel):
    """Request para POST /api/chat"""
    query: str = Field(..., min_length=3, description="Pregunta del usuario")
    filters: Optional[FilterFacets] = None
    top_k: int = Field(default=8, ge=1, le=20, description="Número de chunks a recuperar")
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the effects of microgravity on immune response in mice?",
                "filters": {
                    "organism": ["Mus musculus"],
                    "mission_env": ["ISS"],
                    "exposure": ["microgravity"],
                },
                "top_k": 8,
                "session_id": "user-123-session-456",
            }
        }


class RetrievalMetrics(BaseModel):
    """Métricas del proceso de retrieval"""
    latency_ms: float = Field(..., description="Latencia total en milisegundos")
    retrieved_k: int = Field(..., description="Número de chunks recuperados")
    grounded_ratio: float = Field(..., description="Porcentaje de claims que tienen cita")
    dedup_count: int = Field(0, description="Número de chunks duplicados removidos")
    section_distribution: Optional[dict] = Field(None, description="Distribución por sección")


class ChatResponse(BaseModel):
    """Response del endpoint /api/chat"""
    answer: str = Field(..., description="Respuesta sintetizada con citas")
    citations: List[Citation] = []
    metrics: RetrievalMetrics
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Studies show that microgravity exposure leads to immune dysregulation in mice...",
                "citations": [
                    {
                        "source_id": "GLDS-123_chunk_5",
                        "doi": "10.1038/s41526-023-00123-4",
                        "osdr_id": "GLDS-123",
                        "section": "Results",
                        "snippet": "RNA-seq analysis revealed significant upregulation...",
                        "url": "https://osdr.nasa.gov/bio/repo/data/studies/GLDS-123",
                        "text": "Microgravity effects on immune response",
                        "year": 2023,
                        "similarity_score": 0.87,
                        "section_boost": 0.10,
                        "final_score": 0.97,
                        "relevance_reason": "High similarity (0.87) + Results section boost (+0.10)",
                    }
                ],
                "metrics": {
                    "latency_ms": 1234.5,
                    "retrieved_k": 8,
                    "grounded_ratio": 0.92,
                    "dedup_count": 2,
                    "section_distribution": {"Results": 4, "Conclusion": 2, "Methods": 2},
                },
            }
        }