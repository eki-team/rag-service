"""
Frontend API Router - Adaptado a estructura real de MongoDB
Endpoints para operaciones del frontend (listado, búsqueda, filtrado)
independientes del chatbot RAG.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging

from app.schemas.front import (
    DocumentListResponse,
    ChunksListResponse,
    SearchFilters,
    FilterValuesResponse,
    DocumentDetailResponse,
    DocumentMetadata,
    DocumentChunk,
    ArticleMetadata,
    StatisticsResponse
)
from app.db.mongo_repo import get_mongo_repo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/front", tags=["frontend"])


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0, description="Número de documentos a saltar"),
    limit: int = Query(20, ge=1, le=100, description="Número de documentos por página")
):
    """
    📄 **Listar todos los documentos únicos**
    
    Retorna lista paginada de documentos (papers) sin duplicados.
    Cada documento incluye metadata principal.
    
    **Ejemplo:**
    ```
    GET /api/front/documents?skip=0&limit=20
    ```
    
    **Respuesta:**
    ```json
    {
      "total": 150,
      "documents": [
        {
          "pk": "mice-in-bion-m-1-space-mission",
          "title": "Mice in Bion-M 1 Space Mission",
          "source_type": "article",
          "source_url": "https://...",
          "category": "space",
          "tags": ["mice", "space", "mission"],
          "total_chunks": 55
        }
      ]
    }
    ```
    """
    try:
        logger.info(f"📄 Listing papers: skip={skip}, limit={limit}")
        
        repo = get_mongo_repo()
        papers = repo.get_unique_papers(skip=skip, limit=limit)
        total = repo.count_unique_papers()
        
        # Convertir a schema
        paper_list = []
        for paper in papers:
            # Extraer metadata
            article_meta = paper.get("article_metadata", {})
            
            article_metadata_obj = None
            if article_meta:
                article_metadata_obj = ArticleMetadata(
                    url=article_meta.get("url"),
                    title=article_meta.get("title"),
                    authors=article_meta.get("authors", []),
                    scraped_at=article_meta.get("scraped_at"),
                    pmc_id=article_meta.get("pmc_id"),
                    doi=article_meta.get("doi"),
                    statistics=article_meta.get("statistics")
                )
            
            paper_list.append(DocumentMetadata(
                pk=paper.get("pk", "unknown"),
                title=article_meta.get("title") if article_meta else None,
                source_type=paper.get("source_type"),
                source_url=paper.get("source_url"),
                category=paper.get("category"),
                tags=paper.get("tags", []),
                total_chunks=paper.get("total_chunks", 0),
                article_metadata=article_metadata_obj
            ))
        
        return DocumentListResponse(total=total, documents=paper_list)
        
    except Exception as e:
        logger.error(f"❌ Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/search", response_model=DocumentListResponse)
async def search_documents(
    filters: SearchFilters,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    🔍 **Buscar documentos con filtros**
    
    Buscar documentos aplicando filtros facetados y/o búsqueda de texto.
    No utiliza búsqueda vectorial (es búsqueda tradicional).
    
    **Body ejemplo:**
    ```json
    {
      "category": "space",
      "tags": ["mice", "mission"],
      "search_text": "microgravity"
    }
    ```
    
    **Filtros disponibles:**
    - `category`: Categoría del documento (space, biology, etc)
    - `tags`: Lista de tags para filtrar
    - `search_text`: Búsqueda de texto en título/contenido/tags
    - `pmc_id`: ID de PubMed Central
    - `source_type`: Tipo de fuente (article, etc)
    """
    try:
        logger.info(f"🔍 Searching papers with filters: {filters.model_dump(exclude_none=True)}")
        
        repo = get_mongo_repo()
        
        # Convertir filtros a MongoDB query format
        filter_dict = filters.model_dump(exclude_none=True)
        mongo_filters = {}
        
        if "category" in filter_dict:
            mongo_filters["metadata.category"] = filter_dict["category"]
        if "tags" in filter_dict:
            mongo_filters["metadata.tags"] = {"$in": filter_dict["tags"]}
        if "source_type" in filter_dict:
            mongo_filters["source_type"] = filter_dict["source_type"]
        if "pmc_id" in filter_dict:
            mongo_filters["metadata.article_metadata.pmc_id"] = filter_dict["pmc_id"]
        
        # Buscar papers únicos
        papers = repo.get_unique_papers(skip=skip, limit=limit, filters=mongo_filters)
        total = repo.count_unique_papers(filters=mongo_filters)
        
        # Convertir a schema
        paper_list = []
        for paper in papers:
            # Extraer metadata
            article_meta = paper.get("article_metadata", {})
            
            article_metadata_obj = None
            if article_meta:
                article_metadata_obj = ArticleMetadata(
                    url=article_meta.get("url"),
                    title=article_meta.get("title"),
                    authors=article_meta.get("authors", []),
                    scraped_at=article_meta.get("scraped_at"),
                    pmc_id=article_meta.get("pmc_id"),
                    doi=article_meta.get("doi"),
                    statistics=article_meta.get("statistics")
                )
            
            paper_list.append(DocumentMetadata(
                pk=paper.get("pk", "unknown"),
                title=article_meta.get("title") if article_meta else None,
                source_type=paper.get("source_type"),
                source_url=paper.get("source_url"),
                category=paper.get("category"),
                tags=paper.get("tags", []),
                total_chunks=paper.get("total_chunks", 0),
                article_metadata=article_metadata_obj
            ))
        
        return DocumentListResponse(total=total, documents=paper_list)
        
    except Exception as e:
        logger.error(f"❌ Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NUEVOS ENDPOINTS - Las rutas específicas DEBEN ir ANTES de /{pk}
# ============================================================================

@router.get("/documents/paginated", response_model=DocumentListResponse) 
async def get_documents_paginated(
    page: int = Query(1, ge=1, description="Número de página (empezando en 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Documentos por página"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    source_type: Optional[str] = Query(None, description="Filtrar por tipo de fuente")
):
    """Paginación mejorada de documentos con filtros opcionales"""
    try:
        skip = (page - 1) * page_size
        logger.info(f"📄 Getting paginated papers: page={page}, size={page_size}")
        
        repo = get_mongo_repo()
        filters = {}
        if category:
            filters["metadata.category"] = category
        if source_type:
            filters["source_type"] = source_type
        
        papers = repo.get_unique_papers(skip=skip, limit=page_size, filters=filters)
        total = repo.count_unique_papers(filters=filters)
        total_pages = (total + page_size - 1) // page_size
        
        paper_list = []
        for paper in papers:
            # Extraer metadata
            article_meta = paper.get("article_metadata", {})
            
            article_metadata_obj = None
            if article_meta:
                article_metadata_obj = ArticleMetadata(
                    url=article_meta.get("url"),
                    title=article_meta.get("title"),
                    authors=article_meta.get("authors", []),
                    scraped_at=article_meta.get("scraped_at"),
                    pmc_id=article_meta.get("pmc_id"),
                    doi=article_meta.get("doi"),
                    statistics=article_meta.get("statistics")
                )
            
            paper_list.append(DocumentMetadata(
                pk=paper.get("pk", "unknown"),
                title=article_meta.get("title") if article_meta else None,
                source_type=paper.get("source_type"),
                source_url=paper.get("source_url"),
                category=paper.get("category"),
                tags=paper.get("tags", []),
                total_chunks=paper.get("total_chunks", 0),
                article_metadata=article_metadata_obj
            ))
        
        return DocumentListResponse(
            total=total, 
            documents=paper_list,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting paginated documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/by-category", response_model=DocumentListResponse)
async def get_documents_by_category(
    category: str = Query(..., description="Categoría a filtrar"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Búsqueda de documentos por categoría específica"""
    try:
        logger.info(f"🏷️ Getting papers by category: {category}")
        repo = get_mongo_repo()
        
        filters = {"metadata.category": category}
        papers = repo.get_unique_papers(skip=skip, limit=limit, filters=filters)
        total = repo.count_unique_papers(filters=filters)
        
        paper_list = []
        for paper in papers:
            # Extraer metadata
            article_meta = paper.get("article_metadata", {})
            
            article_metadata_obj = None
            if article_meta:
                article_metadata_obj = ArticleMetadata(
                    url=article_meta.get("url"),
                    title=article_meta.get("title"),
                    authors=article_meta.get("authors", []),
                    scraped_at=article_meta.get("scraped_at"),
                    pmc_id=article_meta.get("pmc_id"),
                    doi=article_meta.get("doi"),
                    statistics=article_meta.get("statistics")
                )
            
            paper_list.append(DocumentMetadata(
                pk=paper.get("pk", "unknown"),
                title=article_meta.get("title") if article_meta else None,
                source_type=paper.get("source_type"),
                source_url=paper.get("source_url"),
                category=paper.get("category"),
                tags=paper.get("tags", []),
                total_chunks=paper.get("total_chunks", 0),
                article_metadata=article_metadata_obj
            ))
        
        return DocumentListResponse(total=total, documents=paper_list)
        
    except Exception as e:
        logger.error(f"❌ Error getting documents by category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/by-tags", response_model=DocumentListResponse)
async def get_documents_by_tags(
    tags: List[str] = Query(..., description="Tags a filtrar"),
    match_all: bool = Query(False, description="Si true, debe coincidir con todos los tags"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Búsqueda de documentos por tags"""
    try:
        logger.info(f"🏷️ Getting papers by tags: {tags}, match_all={match_all}")
        repo = get_mongo_repo()
        
        if match_all:
            filters = {"metadata.tags": {"$all": tags}}
        else:
            filters = {"metadata.tags": {"$in": tags}}
        
        papers = repo.get_unique_papers(skip=skip, limit=limit, filters=filters)
        total = repo.count_unique_papers(filters=filters)
        
        paper_list = []
        for paper in papers:
            # Extraer metadata
            article_meta = paper.get("article_metadata", {})
            
            article_metadata_obj = None
            if article_meta:
                article_metadata_obj = ArticleMetadata(
                    url=article_meta.get("url"),
                    title=article_meta.get("title"),
                    authors=article_meta.get("authors", []),
                    scraped_at=article_meta.get("scraped_at"),
                    pmc_id=article_meta.get("pmc_id"),
                    doi=article_meta.get("doi"),
                    statistics=article_meta.get("statistics")
                )
            
            paper_list.append(DocumentMetadata(
                pk=paper.get("pk", "unknown"),
                title=article_meta.get("title") if article_meta else None,
                source_type=paper.get("source_type"),
                source_url=paper.get("source_url"),
                category=paper.get("category"),
                tags=paper.get("tags", []),
                total_chunks=paper.get("total_chunks", 0),
                article_metadata=article_metadata_obj
            ))
        
        return DocumentListResponse(total=total, documents=paper_list)
        
    except Exception as e:
        logger.error(f"❌ Error getting documents by tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filter-values", response_model=FilterValuesResponse)
async def get_available_filter_values():
    """Obtener valores disponibles para filtros dinámicos"""
    try:
        logger.info("📊 Getting available filter values")
        repo = get_mongo_repo()
        filter_values = repo.get_filter_values()
        
        return FilterValuesResponse(
            categories=filter_values.get("categories", [
                "general", "mission", "nasa", "physics", "planets", 
                "science", "space", "technology"
            ]),
            tags=filter_values.get("tags", []),
            source_types=filter_values.get("source_types", ["article"]),
            total_documents=filter_values.get("total_documents", 536),
            total_chunks=filter_values.get("total_chunks", 22674)
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting filter values: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{pk}", response_model=DocumentDetailResponse)
async def get_document_detail(pk: str):
    """
    📖 **Obtener detalle completo de un documento**
    
    Retorna todos los chunks de un documento específico con metadata completa.
    
    **Ejemplo:**
    ```
    GET /api/front/documents/mice-in-bion-m-1-space-mission
    ```
    
    **Respuesta:**
    ```json
    {
      "metadata": {
        "pk": "mice-in-bion-m-1-space-mission",
        "title": "Mice in Bion-M 1 Space Mission",
        "total_chunks": 55,
        ...
      },
      "chunks": [
        {
          "pk": "mice-in-bion-m-1-space-mission",
          "text": "Title: Mice in Bion-M 1 Space Mission...",
          "chunk_index": 0,
          "total_chunks": 55,
          ...
        }
      ],
      "total_chunks": 55
    }
    ```
    """
    try:
        logger.info(f"📖 Getting document detail: pk={pk}")
        
        repo = get_mongo_repo()
        document = repo.get_document_by_id(pk)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {pk} not found")
        
        # Convertir metadata
        meta = document["metadata"]
        article_meta = meta.get("article_metadata")
        article_metadata_obj = None
        if article_meta:
            article_metadata_obj = ArticleMetadata(
                url=article_meta.get("url"),
                title=article_meta.get("title", ""),
                authors=article_meta.get("authors", []),
                scraped_at=article_meta.get("scraped_at"),
                pmc_id=article_meta.get("pmc_id"),
                doi=article_meta.get("doi"),
                statistics=article_meta.get("statistics")
            )
        
        metadata_obj = DocumentMetadata(
            pk=meta.get("pk", ""),
            title=meta.get("title", ""),
            source_type=meta.get("source_type"),
            source_url=meta.get("source_url"),
            category=meta.get("category"),
            tags=meta.get("tags", []),
            total_chunks=meta.get("total_chunks", 0),
            article_metadata=article_metadata_obj
        )
        
        # Convertir chunks
        chunks_list = []
        for chunk in document["chunks"]:
            chunk_meta = chunk.get("metadata", {})
            chunk_article_meta = chunk_meta.get("article_metadata")
            chunk_article_metadata_obj = None
            if chunk_article_meta:
                chunk_article_metadata_obj = ArticleMetadata(
                    url=chunk_article_meta.get("url"),
                    title=chunk_article_meta.get("title", ""),
                    authors=chunk_article_meta.get("authors", []),
                    scraped_at=chunk_article_meta.get("scraped_at"),
                    pmc_id=chunk_article_meta.get("pmc_id"),
                    doi=chunk_article_meta.get("doi"),
                    statistics=chunk_article_meta.get("statistics")
                )
            
            chunks_list.append(DocumentChunk(
                pk=chunk.get("pk", ""),
                text=chunk.get("text", ""),
                source_type=chunk.get("source_type"),
                source_url=chunk.get("source_url"),
                category=chunk_meta.get("category"),
                tags=chunk_meta.get("tags", []),
                chunk_index=chunk.get("chunk_index", 0),
                total_chunks=chunk.get("total_chunks", 0),
                char_count=chunk_meta.get("char_count"),
                word_count=chunk_meta.get("word_count"),
                sentences_count=chunk_meta.get("sentences_count"),
                article_metadata=chunk_article_metadata_obj
            ))
        
        return DocumentDetailResponse(
            metadata=metadata_obj,
            chunks=chunks_list,
            total_chunks=document["total_chunks"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting document detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters", response_model=FilterValuesResponse)
async def get_filter_values():
    """
    🎯 **Obtener valores disponibles para filtros**
    
    Retorna todos los valores únicos para cada filtro disponible.
    Útil para poblar dropdowns y selectores en el frontend.
    
    **Ejemplo:**
    ```
    GET /api/front/filters
    ```
    
    **Respuesta:**
    ```json
    {
      "categories": ["space", "biology", "physics"],
      "tags": ["mice", "mission", "microgravity", ...],
      "source_types": ["article"],
      "total_documents": 150,
      "total_chunks": 3500
    }
    ```
    """
    try:
        logger.info("🎯 Getting filter values")
        
        repo = get_mongo_repo()
        filter_values = repo.get_filter_values()
        
        return FilterValuesResponse(
            categories=filter_values.get("categories", []),
            tags=filter_values.get("tags", []),
            source_types=filter_values.get("source_types", []),
            total_documents=filter_values.get("total_documents", 0),
            total_chunks=filter_values.get("total_chunks", 0)
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting filter values: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """
    📊 **Obtener estadísticas de la base de datos**
    
    Retorna estadísticas generales de la colección.
    
    **Ejemplo:**
    ```
    GET /api/front/stats
    ```
    
    **Respuesta:**
    ```json
    {
      "total_documents": 150,
      "total_chunks": 3500,
      "categories_count": 3,
      "tags_count": 250,
      "source_types": ["article"]
    }
    ```
    """
    try:
        logger.info("📊 Getting database statistics")
        
        repo = get_mongo_repo()
        filter_values = repo.get_filter_values()
        
        return {
            "total_documents": filter_values.get("total_documents", 0),
            "total_chunks": filter_values.get("total_chunks", 0),
            "categories_count": len(filter_values.get("categories", [])),
            "tags_count": len(filter_values.get("tags", [])),
            "source_types": filter_values.get("source_types", []),
            "categories": filter_values.get("categories", [])
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
