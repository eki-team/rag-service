"""
NASA Biology RAG - Chat Router
Endpoint POST /api/chat
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag.pipeline_advanced import get_rag_pipeline
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse, summary="NASA Biology RAG Chat")
async def chat(request: ChatRequest):
    """
    🚀 **NASA Biology RAG - Chat Endpoint**
    
    Realiza búsqueda semántica en papers de biología espacial y genera respuesta con citas.
    
    ---
    
    ## 📝 Request Body
    
    ### Mínimo (solo query):
    ```json
    {
      "query": "What are the effects of microgravity on mice?"
    }
    ```
    
    ### Con filtros opcionales:
    ```json
    {
      "query": "How does spaceflight affect immune response?",
      "filters": {
        "organism": ["Mus musculus"],
        "mission_env": ["ISS"],
        "exposure": ["microgravity"]
      },
      "top_k": 8
    }
    ```
    
    ---
    
    ## 📊 Response
    
    ```json
    {
      "answer": "Studies show that microgravity exposure leads to...[1][2]",
      "citations": [
        {
          "source_id": "GLDS-123_chunk_5",
          "doi": "10.1038/...",
          "section": "Results",
          "snippet": "RNA-seq analysis revealed..."
        }
      ],
      "metrics": {
        "latency_ms": 1234.5,
        "retrieved_k": 8,
        "grounded_ratio": 0.92
      }
    }
    ```
    
    ---
    
    ## 🔍 Filtros disponibles
    
    - **organism**: ["Mus musculus", "Homo sapiens", "Arabidopsis", etc.]
    - **mission_env**: ["ISS", "LEO", "Shuttle", "Ground", etc.]
    - **exposure**: ["microgravity", "radiation", "spaceflight", etc.]
    - **system**: ["immune", "cardiovascular", "musculoskeletal", etc.]
    - **year_range**: [2020, 2024]
    - **tissue**: ["muscle", "bone", "blood", etc.]
    - **assay**: ["RNA-seq", "proteomics", "microscopy", etc.]
    
    ---
    
    ## ⚙️ Parámetros
    
    - **query** (requerido): Pregunta en lenguaje natural
    - **filters** (opcional): Filtros facetados para retrieval
    - **top_k** (opcional, default=8): Número de chunks a recuperar (1-20)
    - **session_id** (opcional): ID para tracking de sesión
    
    ---
    
    ## 💡 Tips para Postman
    
    1. **URL**: `POST http://localhost:8000/api/chat`
    2. **Headers**: `Content-Type: application/json`
    3. **Body**: Seleccionar "raw" + "JSON"
    4. **Query simple**: Solo envía `{"query": "tu pregunta"}`
    
    """
    try:
        logger.info(f"📨 Chat request: {request.query[:100]}...")
        pipeline = get_rag_pipeline()
        response = await pipeline.answer(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k,
            session_id=request.session_id,
        )
        logger.info(f"✅ Response generated: {len(response.citations)} citations")
        return response
    
    except Exception as e:
        logger.error(f"❌ Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )
