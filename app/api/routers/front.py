"""
Frontend API Router
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
    DocumentChunk
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
          "source_id": "GLDS-123_chunk_1",
          "title": "Effects of microgravity on immune response",
          "year": 2023,
          "doi": "10.1038/...",
          "organism": "Mus musculus",
          "mission_env": "ISS",
          ...
        }
      ]
    }
    ```
    """
    try:
        logger.info(f"📄 Listing documents: skip={skip}, limit={limit}")
        
        repo = get_mongo_repo()
        documents = repo.get_all_documents(skip=skip, limit=limit)
        total = repo.count_documents()
        
        # Convertir a schema
        doc_list = [
            DocumentMetadata(
                source_id=doc.get("source_id", ""),
                title=doc.get("title", ""),
                year=doc.get("year"),
                doi=doc.get("doi"),
                osdr_id=doc.get("osdr_id"),
                organism=doc.get("organism"),
                mission_env=doc.get("mission_env"),
                exposure=doc.get("exposure"),
                system=doc.get("system"),
                tissue=doc.get("tissue"),
                assay=doc.get("assay")
            )
            for doc in documents
        ]
        
        return DocumentListResponse(total=total, documents=doc_list)
        
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
      "organism": ["Mus musculus", "Homo sapiens"],
      "mission_env": ["ISS"],
      "year_min": 2020,
      "year_max": 2024,
      "search_text": "immune response"
    }
    ```
    
    **Filtros disponibles:**
    - `organism`: Lista de organismos
    - `mission_env`: Lista de entornos de misión
    - `exposure`: Lista de tipos de exposición
    - `system`: Lista de sistemas biológicos
    - `tissue`: Lista de tejidos
    - `assay`: Lista de tipos de ensayo
    - `year_min`, `year_max`: Rango de años
    - `search_text`: Búsqueda de texto en título/contenido
    """
    try:
        logger.info(f"🔍 Searching documents with filters: {filters.dict(exclude_none=True)}")
        
        repo = get_mongo_repo()
        
        # Convertir filtros a dict
        filter_dict = filters.dict(exclude_none=True)
        
        # Buscar documentos
        documents = repo.search_documents_by_filters(filter_dict, skip=skip, limit=limit)
        total = repo.count_documents(filter_dict)
        
        # Convertir a schema
        doc_list = [
            DocumentMetadata(
                source_id=doc.get("source_id", ""),
                title=doc.get("title", ""),
                year=doc.get("year"),
                doi=doc.get("doi"),
                osdr_id=doc.get("osdr_id"),
                organism=doc.get("organism"),
                mission_env=doc.get("mission_env"),
                exposure=doc.get("exposure"),
                system=doc.get("system"),
                tissue=doc.get("tissue"),
                assay=doc.get("assay")
            )
            for doc in documents
        ]
        
        return DocumentListResponse(total=total, documents=doc_list)
        
    except Exception as e:
        logger.error(f"❌ Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{source_id}", response_model=DocumentDetailResponse)
async def get_document_detail(source_id: str):
    """
    📖 **Obtener detalle completo de un documento**
    
    Retorna todos los chunks de un documento específico con sus metadatos.
    Útil para visualizar el contenido completo de un paper.
    
    **Ejemplo:**
    ```
    GET /api/front/documents/GLDS-123
    ```
    
    **Respuesta:**
    ```json
    {
      "metadata": {
        "source_id": "GLDS-123_chunk_1",
        "title": "Effects of microgravity...",
        "year": 2023,
        ...
      },
      "chunks": [
        {
          "source_id": "GLDS-123_chunk_1",
          "section": "Introduction",
          "text": "...",
          ...
        },
        ...
      ],
      "total_chunks": 25
    }
    ```
    """
    try:
        logger.info(f"📖 Getting document detail: {source_id}")
        
        repo = get_mongo_repo()
        doc_data = repo.get_document_by_id(source_id)
        
        if not doc_data:
            raise HTTPException(status_code=404, detail=f"Document {source_id} not found")
        
        # Convertir a schema
        metadata = DocumentMetadata(**doc_data["metadata"])
        
        chunks = [
            DocumentChunk(
                source_id=chunk.get("source_id", ""),
                pk=chunk.get("pk", ""),
                title=chunk.get("title", ""),
                year=chunk.get("year"),
                doi=chunk.get("doi"),
                osdr_id=chunk.get("osdr_id"),
                organism=chunk.get("organism"),
                mission_env=chunk.get("mission_env"),
                exposure=chunk.get("exposure"),
                system=chunk.get("system"),
                tissue=chunk.get("tissue"),
                assay=chunk.get("assay"),
                section=chunk.get("section", ""),
                text=chunk.get("text", ""),
                chunk_index=chunk.get("chunk_index")
            )
            for chunk in doc_data["chunks"]
        ]
        
        return DocumentDetailResponse(
            metadata=metadata,
            chunks=chunks,
            total_chunks=doc_data["total_chunks"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting document detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters", response_model=FilterValuesResponse)
async def get_filter_values():
    """
    🎯 **Obtener valores disponibles para todos los filtros**
    
    Retorna listas de valores únicos para cada campo filtrable.
    Útil para poblar dropdowns/selects en el frontend.
    
    **Respuesta:**
    ```json
    {
      "organisms": ["Mus musculus", "Homo sapiens", "Arabidopsis thaliana"],
      "mission_envs": ["ISS", "LEO", "Ground"],
      "exposures": ["microgravity", "radiation", "spaceflight"],
      "systems": ["immune", "musculoskeletal", "cardiovascular"],
      "tissues": ["muscle", "bone", "liver"],
      "assays": ["RNA-seq", "proteomics", "metabolomics"],
      "years": [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    }
    ```
    """
    try:
        logger.info("🎯 Getting filter values")
        
        repo = get_mongo_repo()
        values = repo.get_filter_values()
        
        return FilterValuesResponse(
            organisms=values.get("organism", []),
            mission_envs=values.get("mission_env", []),
            exposures=values.get("exposure", []),
            systems=values.get("system", []),
            tissues=values.get("tissue", []),
            assays=values.get("assay", []),
            years=sorted(values.get("year", []), reverse=True)
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting filter values: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """
    📊 **Obtener estadísticas generales de la base de datos**
    
    Retorna contadores y métricas útiles.
    
    **Respuesta:**
    ```json
    {
      "total_documents": 150,
      "total_chunks": 3500,
      "organisms_count": 25,
      "years_range": [2015, 2024]
    }
    ```
    """
    try:
        logger.info("📊 Getting database statistics")
        
        repo = get_mongo_repo()
        
        # Contar documentos únicos
        total_docs = repo.count_documents()
        
        # Contar chunks totales
        total_chunks = repo.collection.count_documents({"pk": "nasa"})
        
        # Obtener valores de filtros para contar
        filter_values = repo.get_filter_values()
        
        years = filter_values.get("year", [])
        
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "organisms_count": len(filter_values.get("organism", [])),
            "mission_envs_count": len(filter_values.get("mission_env", [])),
            "years_range": [min(years), max(years)] if years else [None, None]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
