"""
NASA Biology RAG - OpenAI Embeddings
Generador de embeddings usando OpenAI text-embedding-3-small (1536 dimensiones).
"""
from openai import OpenAI
from typing import List, Union
import numpy as np
import logging
from app.core.settings import settings

logger = logging.getLogger(__name__)


class OpenAIEmbeddings:
    """
    Servicio de embeddings con OpenAI API.
    Modelo: text-embedding-3-small
    - Dimensiones: 1536
    - Similitud: Coseno
    - Costo: $0.02 / 1M tokens
    - Mejor calidad que sentence-transformers
    """
    
    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Args:
            model_name: Modelo de OpenAI (text-embedding-3-small o text-embedding-3-large)
        """
        logger.info(f"🔄 Initializing OpenAI embeddings: {model_name}...")
        
        if not settings.OPENAI_API_KEY:
            raise ValueError("❌ OPENAI_API_KEY no está configurado en .env")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_name = model_name
        
        # Dimensiones según modelo
        if model_name == "text-embedding-3-small":
            self.dimensions = 1536
        elif model_name == "text-embedding-3-large":
            self.dimensions = 3072
        else:
            self.dimensions = 1536  # default
        
        logger.info(f"✅ OpenAI embeddings initialized: {model_name} ({self.dimensions} dims)")
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 100,  # OpenAI soporta hasta 2048 inputs
    ) -> Union[List[float], List[List[float]]]:
        """
        Genera embeddings para uno o más textos.
        
        Args:
            texts: Texto o lista de textos
            batch_size: Batch size para procesar múltiples textos
        
        Returns:
            Vector o lista de vectores (1536 dims cada uno)
        """
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        embeddings_list = []
        
        # Procesar en batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                logger.debug(f"🔄 Generating embeddings for {len(batch)} texts...")
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model_name
                )
                
                # Extraer embeddings de la respuesta
                batch_embeddings = [item.embedding for item in response.data]
                embeddings_list.extend(batch_embeddings)
                
                logger.debug(f"✅ Generated {len(batch_embeddings)} embeddings")
                
            except Exception as e:
                logger.error(f"❌ Error generating embeddings: {e}")
                raise
        
        return embeddings_list[0] if is_single else embeddings_list
    
    def encode_query(self, query: str) -> List[float]:
        """
        Genera embedding para una query de búsqueda.
        
        Args:
            query: Query del usuario
        
        Returns:
            Vector de 1536 dimensiones
        """
        logger.info(f"🔍 Encoding query: {query[:100]}...")
        embedding = self.encode(query)
        logger.info(f"✅ Query encoded: {len(embedding)} dims")
        return embedding
    
    def encode_documents(self, documents: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Genera embeddings para múltiples documentos (útil para indexación).
        
        Args:
            documents: Lista de textos a indexar
            batch_size: Batch size para procesar
        
        Returns:
            Lista de vectores (1536 dims cada uno)
        """
        logger.info(f"📄 Encoding {len(documents)} documents...")
        embeddings = self.encode(documents, batch_size=batch_size)
        logger.info(f"✅ Encoded {len(embeddings)} documents")
        return embeddings
    
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
_embeddings_service: OpenAIEmbeddings = None


def get_embeddings_service() -> OpenAIEmbeddings:
    """
    Obtiene instancia singleton del servicio de embeddings.
    El cliente se inicializa una vez al inicio.
    """
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = OpenAIEmbeddings()
    return _embeddings_service
