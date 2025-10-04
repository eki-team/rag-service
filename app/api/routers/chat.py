"""
NASA Biology RAG - Chat Router
Endpoint POST /api/chat
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag.pipeline import get_rag_pipeline
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG endpoint para preguntas sobre biología espacial de NASA.
    
    - **query**: Pregunta del usuario
    - **filters**: Filtros opcionales (organism, mission_env, etc.)
    - **top_k**: Número de chunks a recuperar (default 8)
    - **session_id**: ID de sesión (opcional, para tracking)
    
    Returns:
    - **answer**: Respuesta sintetizada con citas [N]
    - **citations**: Lista de papers citados
    - **metrics**: Métricas de retrieval y grounding
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
        return response
    
    except Exception as e:
        logger.error(f"❌ Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )
