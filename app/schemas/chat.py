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
    
    class Config:
        json_schema_extra = {
            "example": {
                "organism": ["Mus musculus"],
                "mission_env": ["ISS", "LEO"],
                "year_range": [2020, 2024],
                "exposure": ["microgravity"],
            }
        }


class Citation(BaseModel):
    """Cita de un paper usado en la respuesta"""
    source_id: str
    doi: Optional[str] = None
    osdr_id: Optional[str] = None
    section: Optional[str] = None
    snippet: str = Field(..., description="Fragmento relevante del chunk")
    url: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None


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
    latency_ms: float
    retrieved_k: int
    grounded_ratio: float = Field(..., description="Ratio de claims con cita")
    dedup_count: int = 0
    section_distribution: Optional[dict] = None


class ChatResponse(BaseModel):
    """Response de POST /api/chat"""
    answer: str = Field(..., description="Respuesta sintetizada con citas")
    citations: List[Citation] = []
    used_filters: Optional[FilterFacets] = None
    metrics: RetrievalMetrics
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Studies show that microgravity exposure leads to immune dysregulation in mice [1][2]...",
                "citations": [
                    {
                        "source_id": "GLDS-123_chunk_5",
                        "doi": "10.1038/s41526-023-00123-4",
                        "osdr_id": "GLDS-123",
                        "section": "Results",
                        "snippet": "RNA-seq analysis revealed significant upregulation...",
                        "url": "https://osdr.nasa.gov/bio/repo/data/studies/GLDS-123",
                        "title": "Microgravity effects on immune response",
                        "year": 2023,
                    }
                ],
                "used_filters": {
                    "organism": ["Mus musculus"],
                    "mission_env": ["ISS"],
                },
                "metrics": {
                    "latency_ms": 1234.5,
                    "retrieved_k": 8,
                    "grounded_ratio": 0.92,
                    "dedup_count": 2,
                    "section_distribution": {"Results": 4, "Conclusion": 2, "Methods": 2},
                },
            }
        }
