"""
Embeddings services
"""
from app.services.embeddings.sentence_transformer import (
    get_embeddings_service,
    SentenceTransformerEmbeddings,
)

__all__ = [
    "get_embeddings_service",
    "SentenceTransformerEmbeddings",
]
