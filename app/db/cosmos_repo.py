"""
NASA Biology RAG - Cosmos DB Repository (Opción A - PROD)
Repositorio para Cosmos DB NoSQL con vector search.
"""
from typing import List, Dict, Any, Optional
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from app.core.settings import settings
from app.schemas.chunk import Chunk
from loguru import logger


class CosmosRepository:
    """Repositorio para Cosmos DB NoSQL"""
    
    def __init__(self):
        self.client = CosmosClient(settings.COSMOS_URL, credential=settings.COSMOS_KEY)
        self.database = self.client.get_database_client(settings.COSMOS_DB)
        self.container = self.database.get_container_client(settings.COSMOS_CONTAINER)
        logger.info(f"✅ Cosmos repo initialized: {settings.COSMOS_DB}/{settings.COSMOS_CONTAINER}")
    
    def search_vectors(
        self,
        query_vec: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 8,
        min_similarity: float = 0.70,
    ) -> List[Dict[str, Any]]:
        """
        Buscar por similitud vectorial con filtros opcionales.
        
        Args:
            query_vec: Vector de embedding de la query
            filters: Filtros facetados (organism, mission_env, etc.)
            top_k: Número de resultados
            min_similarity: Similitud mínima
        
        Returns:
            Lista de chunks con metadata y score
        """
        try:
            # Construir query SQL con vector similarity
            # TODO: Adaptar según la implementación de vector search en tu Cosmos DB
            # Ejemplo genérico:
            query = """
                SELECT TOP @top_k 
                    c.source_id, c.title, c.text, c.section, c.doi, c.osdr_id,
                    c.organism, c.system, c.mission_env, c.exposure, c.assay, c.tissue,
                    c.year, c.venue, c.url, c.source_type,
                    VectorDistance(c.embedding, @query_vec) AS similarity
                FROM c
                WHERE c.pk = @pk
            """
            
            params = [
                {"name": "@top_k", "value": top_k},
                {"name": "@query_vec", "value": query_vec},
                {"name": "@pk", "value": settings.NASA_DEFAULT_ORG},
            ]
            
            # Agregar filtros
            if filters:
                if "organism" in filters and filters["organism"]:
                    query += " AND ARRAY_CONTAINS(@organisms, c.organism)"
                    params.append({"name": "@organisms", "value": filters["organism"]})
                
                if "mission_env" in filters and filters["mission_env"]:
                    query += " AND ARRAY_CONTAINS(@mission_envs, c.mission_env)"
                    params.append({"name": "@mission_envs", "value": filters["mission_env"]})
                
                if "system" in filters and filters["system"]:
                    query += " AND ARRAY_CONTAINS(@systems, c.system)"
                    params.append({"name": "@systems", "value": filters["system"]})
                
                if "exposure" in filters and filters["exposure"]:
                    query += " AND ARRAY_CONTAINS(@exposures, c.exposure)"
                    params.append({"name": "@exposures", "value": filters["exposure"]})
                
                if "year_range" in filters and filters["year_range"]:
                    year_min, year_max = filters["year_range"]
                    query += " AND c.year >= @year_min AND c.year <= @year_max"
                    params.append({"name": "@year_min", "value": year_min})
                    params.append({"name": "@year_max", "value": year_max})
            
            query += " ORDER BY VectorDistance(c.embedding, @query_vec)"
            
            # Ejecutar query
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                partition_key=settings.NASA_DEFAULT_ORG,
                enable_cross_partition_query=False,
            ))
            
            # Filtrar por min_similarity
            results = [item for item in items if item.get("similarity", 0) >= min_similarity]
            
            logger.info(f"📊 Cosmos search: {len(results)}/{len(items)} chunks above threshold {min_similarity}")
            return results
        
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Cosmos search error: {e}")
            return []
    
    def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Obtener chunks por IDs"""
        try:
            query = "SELECT * FROM c WHERE ARRAY_CONTAINS(@ids, c.source_id)"
            params = [{"name": "@ids", "value": ids}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                partition_key=settings.NASA_DEFAULT_ORG,
            ))
            
            return items
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Cosmos get_by_ids error: {e}")
            return []
    
    def facet_counts(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, int]]:
        """
        Obtener conteos de facets (para UI de filtros).
        
        Returns:
            Dict con conteos por facet: {"organism": {"Mus musculus": 123, ...}, ...}
        """
        try:
            # TODO: Implementar agregaciones por facet
            # Por ahora devuelve stub
            logger.warning("⚠️ facet_counts not implemented yet (stub)")
            return {
                "organism": {},
                "system": {},
                "mission_env": {},
                "exposure": {},
            }
        except Exception as e:
            logger.error(f"❌ facet_counts error: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check de salud de la conexión"""
        try:
            # Intentar leer un item dummy
            query = "SELECT TOP 1 c.source_id FROM c WHERE c.pk = @pk"
            list(self.container.query_items(
                query=query,
                parameters=[{"name": "@pk", "value": settings.NASA_DEFAULT_ORG}],
                partition_key=settings.NASA_DEFAULT_ORG,
            ))
            return True
        except Exception as e:
            logger.error(f"❌ Cosmos health check failed: {e}")
            return False


# Singleton
_cosmos_repo: Optional[CosmosRepository] = None

def get_cosmos_repo() -> CosmosRepository:
    """Get or create Cosmos repository instance"""
    global _cosmos_repo
    if _cosmos_repo is None:
        _cosmos_repo = CosmosRepository()
    return _cosmos_repo
