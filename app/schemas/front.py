"""
Schemas para endpoints del frontend - Adaptados a la estructura real de MongoDB
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ArticleMetadata(BaseModel):
    """Metadatos del artículo desde metadata.article_metadata"""
    url: Optional[str] = None
    title: str
    authors: List[str] = []
    scraped_at: Optional[str] = None
    pmc_id: Optional[str] = None
    doi: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None


class DocumentMetadata(BaseModel):
    """Metadatos de un documento/paper"""
    pk: str  # ID del documento (ej: mice-in-bion-m-1-space-mission)
    title: str
    source_type: Optional[str] = None  # article, etc
    source_url: Optional[str] = None
    category: Optional[str] = None  # space, etc
    tags: List[str] = []
    total_chunks: int
    article_metadata: Optional[ArticleMetadata] = None


class DocumentChunk(BaseModel):
    """Chunk completo con metadatos"""
    pk: str
    text: str
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    chunk_index: int
    total_chunks: int
    char_count: Optional[int] = None
    word_count: Optional[int] = None
    sentences_count: Optional[int] = None
    article_metadata: Optional[ArticleMetadata] = None


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
    category: Optional[str] = None  # space, biology, etc
    tags: Optional[List[str]] = None  # Lista de tags para filtrar
    search_text: Optional[str] = None  # Búsqueda en title, text, tags
    pmc_id: Optional[str] = None  # ID de PubMed Central
    source_type: Optional[str] = None  # article, etc


class FilterValuesResponse(BaseModel):
    """Valores disponibles para cada filtro"""
    categories: List[str]
    tags: List[str]  # Top 50 tags más comunes
    source_types: List[str]
    total_documents: int
    total_chunks: int


class DocumentDetailResponse(BaseModel):
    """Detalle completo de un documento con todos sus chunks"""
    metadata: DocumentMetadata
    chunks: List[DocumentChunk]
    total_chunks: int


class StatisticsResponse(BaseModel):
    """📊 Respuesta con estadísticas generales de la base de datos"""
    total_documents: int
    total_chunks: int
    unique_categories: List[str]
    unique_tags: List[str]
    source_types: List[str]
