"""
Schemas para endpoints del frontend
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadatos de un documento/paper"""
    source_id: str
    title: str
    year: Optional[int] = None
    doi: Optional[str] = None
    osdr_id: Optional[str] = None
    organism: Optional[str] = None
    mission_env: Optional[str] = None
    exposure: Optional[str] = None
    system: Optional[str] = None
    tissue: Optional[str] = None
    assay: Optional[str] = None


class DocumentChunk(BaseModel):
    """Chunk completo con metadatos"""
    source_id: str
    pk: str
    title: str
    year: Optional[int] = None
    doi: Optional[str] = None
    osdr_id: Optional[str] = None
    organism: Optional[str] = None
    mission_env: Optional[str] = None
    exposure: Optional[str] = None
    system: Optional[str] = None
    tissue: Optional[str] = None
    assay: Optional[str] = None
    section: str
    text: str
    chunk_index: Optional[int] = None


class DocumentListResponse(BaseModel):
    """Respuesta con lista de documentos únicos"""
    total: int
    documents: List[DocumentMetadata]


class ChunksListResponse(BaseModel):
    """Respuesta con lista de chunks"""
    total: int
    chunks: List[DocumentChunk]


class SearchFilters(BaseModel):
    """Filtros para búsqueda de documentos"""
    organism: Optional[List[str]] = None
    mission_env: Optional[List[str]] = None
    exposure: Optional[List[str]] = None
    system: Optional[List[str]] = None
    tissue: Optional[List[str]] = None
    assay: Optional[List[str]] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    search_text: Optional[str] = None


class FilterValuesResponse(BaseModel):
    """Valores disponibles para cada filtro"""
    organisms: List[str]
    mission_envs: List[str]
    exposures: List[str]
    systems: List[str]
    tissues: List[str]
    assays: List[str]
    years: List[int]


class DocumentDetailResponse(BaseModel):
    """Detalle completo de un documento con todos sus chunks"""
    metadata: DocumentMetadata
    chunks: List[DocumentChunk]
    total_chunks: int
