"""
Schemas para endpoints del frontend - Adaptados a la estructura real de MongoDB
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ArticleMetadata(BaseModel):
    """Metadatos del artículo desde metadata.article_metadata"""
    url: Optional[str] = None
    title: Optional[str] = None  # Puede ser None
    authors: List[str] = []
    scraped_at: Optional[str] = None
    pmc_id: Optional[str] = None
    doi: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None


class DocumentMetadata(BaseModel):
    """Metadatos de un documento/paper"""
    pk: str  # ID del documento (ej: mice-in-bion-m-1-space-mission)
    title: Optional[str] = None  # Título del documento (puede venir de article_metadata.title)
    source_type: Optional[str] = None  # article, etc
    source_url: Optional[str] = None
    category: Optional[str] = None  # space, etc
    tags: List[str] = []
    total_chunks: int
    article_metadata: Optional[ArticleMetadata] = None


class DocumentChunk(BaseModel):
    """Chunk individual de MongoDB (sin agrupar)"""
    id: str  # _id de MongoDB convertido a string
    pk: str
    text: str
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None
    char_count: Optional[int] = None
    word_count: Optional[int] = None
    sentences_count: Optional[int] = None
    article_metadata: Optional[ArticleMetadata] = None


class DocumentListResponse(BaseModel):
    """Respuesta con lista de papers únicos"""
    total: int
    documents: List[DocumentMetadata]  # Papers únicos (1 por pk)
    page: Optional[int] = None
    page_size: Optional[int] = None
    total_pages: Optional[int] = None


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
