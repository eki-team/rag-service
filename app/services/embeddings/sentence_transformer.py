"""
NASA Biology RAG - Sentence Transformer Embeddings
Generador de embeddings usando all-MiniLM-L6-v2 (384 dimensiones).
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddings:
    """
    Servicio de embeddings con sentence-transformers.
    Modelo: all-MiniLM-L6-v2
    - Dimensiones: 384
    - Similitud: Coseno
    - Velocidad: ~14,000 oraciones/seg en CPU
    - Multilingüe: Sí
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Args:
            model_name: Nombre del modelo de Hugging Face
        """
        logger.info(f"🔄 Loading model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.dimensions = 384
        logger.info(f"✅ Model loaded: {model_name} ({self.dimensions} dims)")
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = 32,
    ) -> Union[List[float], List[List[float]]]:
        """
        Genera embeddings para uno o más textos.
        
        Args:
            texts: Texto o lista de textos
            normalize: Normalizar vectores (recomendado para coseno)
            batch_size: Batch size para procesar múltiples textos
        
        Returns:
            Vector o lista de vectores (384 dims cada uno)
        """
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        # Generar embeddings
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        
        # Convertir a lista de floats
        embeddings_list = embeddings.tolist()
        
        return embeddings_list[0] if is_single else embeddings_list
    
    def encode_query(self, query: str) -> List[float]:
        """
        Genera embedding para una query de búsqueda.
        
        Args:
            query: Query del usuario
        
        Returns:
            Vector de 384 dimensiones
        """
        return self.encode(query, normalize=True)
    
    def encode_documents(self, documents: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Genera embeddings para múltiples documentos (útil para indexación).
        
        Args:
            documents: Lista de textos a indexar
            batch_size: Batch size para procesar
        
        Returns:
            Lista de vectores (384 dims cada uno)
        """
        return self.encode(documents, normalize=True, batch_size=batch_size)
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calcula similitud de coseno entre dos vectores.
        
        Args:
            vec1: Primer vector
            vec2: Segundo vector
        
        Returns:
            Similitud de coseno (0-1)
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# Singleton global
_embeddings_service: SentenceTransformerEmbeddings = None


def get_embeddings_service() -> SentenceTransformerEmbeddings:
    """
    Obtiene instancia singleton del servicio de embeddings.
    El modelo se carga una vez al inicio.
    """
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = SentenceTransformerEmbeddings()
    return _embeddings_service
