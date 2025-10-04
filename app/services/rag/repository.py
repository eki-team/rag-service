"""
NASA Biology RAG - Repository (orquestador)
Orquesta consultas al repo de datos (Cosmos o pgvector).
"""
from typing import List, Dict, Any, Optional
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)


class RepositoryService:
    """Orquestador de repositorios"""
    
    def __init__(self):
        self.backend = settings.VECTOR_BACKEND
        self._repo = None
    
    @property
    def repo(self):
        """Lazy-load del repo según backend configurado"""
        if self._repo is None:
            if self.backend == "mongodb":
                from app.db.mongo_repo import get_mongo_repo
                self._repo = get_mongo_repo()
                logger.info("✅ Using MongoDB backend")
            elif self.backend == "pgvector":
                # Descomentado cuando se active pgvector
                # from app.db.pgvector_repo import get_pgvector_repo
                # self._repo = get_pgvector_repo()
                logger.warning("⚠️ pgvector backend not implemented (commented)")
                raise NotImplementedError("pgvector backend is commented out")
            else:
                raise ValueError(f"Unknown vector backend: {self.backend}")
        return self._repo
    
    def search_vectors(self, query_vec: List[float], filters: Optional[Dict] = None, top_k: int = 8) -> List[Dict[str, Any]]:
        """Buscar chunks por vector"""
        return self.repo.search_vectors(query_vec, filters, top_k)
    
    def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Obtener chunks por IDs"""
        return self.repo.get_by_ids(ids)
    
    def facet_counts(self, filters: Optional[Dict] = None) -> Dict[str, Dict[str, int]]:
        """Conteos de facets"""
        return self.repo.facet_counts(filters)
    
    def health_check(self) -> bool:
        """Check de salud"""
        return self.repo.health_check()


# Singleton
_repo_service: Optional[RepositoryService] = None

def get_repository_service() -> RepositoryService:
    """Get or create repository service"""
    global _repo_service
    if _repo_service is None:
        _repo_service = RepositoryService()
    return _repo_service
