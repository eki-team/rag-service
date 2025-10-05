"""
Scientific Document Ingestion & Normalization Service
"""

from .document_processor import DocumentProcessor
from .chunk_processor import ChunkProcessor
from .verifier import DocumentVerifier
from .synthesizer import ChunkSynthesizer, SimpleSynthesizer
from .ingestion_pipeline import IngestionPipeline, ingest_from_dict, ingest_from_file
from .mongo_config import get_mongo_config, get_documents_collection, get_chunks_collection
from .models import (
    ScientificDocument,
    DocumentChunk,
    IngestionResult,
    ChunkSynthesis,
    ChunkVerification,
)

__all__ = [
    "DocumentProcessor",
    "ChunkProcessor",
    "DocumentVerifier",
    "ChunkSynthesizer",
    "SimpleSynthesizer",
    "IngestionPipeline",
    "ingest_from_dict",
    "ingest_from_file",
    "get_mongo_config",
    "get_documents_collection",
    "get_chunks_collection",
    "ScientificDocument",
    "DocumentChunk",
    "IngestionResult",
    "ChunkSynthesis",
    "ChunkVerification",
]
