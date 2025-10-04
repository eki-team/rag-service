"""
NASA Biology RAG - Diagnostic Schema
Modelos para endpoints de diagnóstico.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class HealthResponse(BaseModel):
    """Response de GET /diag/health"""
    status: str = "ok"
    service: str = "nasa-rag"
    vector_backend: str
    models: Dict[str, str]
    nasa_mode: bool
    guided_enabled: bool


class EmbeddingRequest(BaseModel):
    """Request para POST /diag/emb"""
    text: str = Field(..., min_length=1)


class EmbeddingResponse(BaseModel):
    """Response de POST /diag/emb"""
    text: str
    embedding: List[float]
    model: str
    dimensions: int


class RetrievalRequest(BaseModel):
    """Request para POST /diag/retrieval"""
    query: str
    top_k: int = 8
    filters: Optional[Dict[str, Any]] = None


class RetrievalChunk(BaseModel):
    """Chunk retornado en diag/retrieval"""
    source_id: str
    title: str
    section: Optional[str]
    doi: Optional[str]
    osdr_id: Optional[str]
    similarity: float
    text: str
    metadata: Dict[str, Any]


class RetrievalResponse(BaseModel):
    """Response de POST /diag/retrieval"""
    query: str
    chunks: List[RetrievalChunk]
    latency_ms: float
    total_found: int


class AuditQuery(BaseModel):
    """Query dorada para audit"""
    id: str
    query: str
    expected_sources: List[str]
    filters: Optional[Dict[str, Any]] = None


class AuditResult(BaseModel):
    """Resultado de audit para una query"""
    query_id: str
    recall_at_k: float
    precision_at_k: float
    retrieved: List[str]
    expected: List[str]
    missing: List[str]


class AuditResponse(BaseModel):
    """Response de POST /diag/retrieval_audit"""
    queries: List[AuditResult]
    avg_recall: float
    avg_precision: float
