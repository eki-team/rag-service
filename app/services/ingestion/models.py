"""
Pydantic Models for Scientific Document Ingestion
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class ArticleMetadata(BaseModel):
    """Metadata for scientific articles"""
    url: str
    title: str
    authors: List[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    pmc_id: Optional[str] = None
    doi: Optional[str] = None
    statistics: Dict[str, Any] = Field(default_factory=dict)


class Reference(BaseModel):
    """Reference metadata"""
    title: str
    year: Optional[int] = None
    doi: Optional[str] = None
    source_url: Optional[str] = None


class DocumentMetadata(BaseModel):
    """Complete document metadata"""
    article_metadata: ArticleMetadata
    references: List[Reference] = Field(default_factory=list)
    char_count: int = 0
    word_count: int = 0
    sentences_count: int = 0
    tags: List[str] = Field(default_factory=list)
    category: str = "other"


class ScientificDocument(BaseModel):
    """Document-level schema for MongoDB"""
    pk: str
    text: str
    abstract: str = ""
    publication_year: Optional[int] = None
    source_type: Literal["article", "preprint", "book", "thesis", "report", "other"] = "article"
    source_url: str
    metadata: DocumentMetadata
    total_chunks: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class Claim(BaseModel):
    """Verifiable claim with evidence"""
    claim: str
    evidence_span: str


class ChunkSynthesis(BaseModel):
    """Synthesis for a single chunk"""
    bullets: List[str] = Field(default_factory=list, min_length=3, max_length=5)
    key_terms: List[str] = Field(default_factory=list, min_length=5, max_length=10)
    claims: List[Claim] = Field(default_factory=list, min_length=1, max_length=3)


class VerificationCheck(BaseModel):
    """Individual verification check"""
    name: str
    result: bool


class ChunkVerification(BaseModel):
    """Verification status for a chunk"""
    status: Literal["passed", "flagged"] = "passed"
    checks: List[VerificationCheck] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: str = ""


class DocumentChunk(BaseModel):
    """Chunk-level schema for MongoDB"""
    pk: str  # <doc-pk>-<chunk-index>
    chunk_index: int
    total_chunks: int
    text: str
    synthesis: ChunkSynthesis
    verification: ChunkVerification
    embedding: Optional[List[float]] = None
    section: str = "unknown"  # Default section as per requirements
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class IngestionResult(BaseModel):
    """Result of ingestion process"""
    success: bool
    document_pk: Optional[str] = None
    chunks_created: int = 0
    verification_status: Literal["passed", "flagged"] = "passed"
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
