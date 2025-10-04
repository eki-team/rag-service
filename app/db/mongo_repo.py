"""
NASA Biology RAG - MongoDB Repository (Opción A - PROD)
Repositorio para MongoDB con vector search (Atlas Vector Search).
"""
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)


class MongoRepository:
    """Repositorio para MongoDB con Atlas Vector Search"""
    
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.database = self.client[settings.MONGODB_DB]
        self.collection = self.database[settings.MONGODB_COLLECTION]
        logger.info(f"✅ MongoDB repo initialized: {settings.MONGODB_DB}/{settings.MONGODB_COLLECTION}")
    
    def search_vectors(
        self,
        query_vec: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 8,
        min_similarity: float = 0.70,
    ) -> List[Dict[str, Any]]:
        """
        Buscar por similitud vectorial con filtros opcionales usando MongoDB Atlas Vector Search.
        
        Args:
            query_vec: Vector de embedding de la query
            filters: Filtros facetados (organism, mission_env, etc.)
            top_k: Número de resultados
            min_similarity: Similitud mínima
        
        Returns:
            Lista de chunks con metadata y score
        """
        try:
            # Construir pipeline de agregación con $vectorSearch
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": settings.MONGODB_VECTOR_INDEX,
                        "path": "embedding",
                        "queryVector": query_vec,
                        "numCandidates": top_k * 10,  # Candidatos para mejorar recall
                        "limit": top_k,
                    }
                },
                {
                    "$addFields": {
                        "similarity": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            # Agregar filtros con $match
            match_conditions = {"pk": settings.NASA_DEFAULT_ORG}
            
            if filters:
                if "organism" in filters and filters["organism"]:
                    match_conditions["organism"] = {"$in": filters["organism"]}
                
                if "mission_env" in filters and filters["mission_env"]:
                    match_conditions["mission_env"] = {"$in": filters["mission_env"]}
                
                if "system" in filters and filters["system"]:
                    match_conditions["system"] = {"$in": filters["system"]}
                
                if "exposure" in filters and filters["exposure"]:
                    match_conditions["exposure"] = {"$in": filters["exposure"]}
                
                if "assay" in filters and filters["assay"]:
                    match_conditions["assay"] = {"$in": filters["assay"]}
                
                if "tissue" in filters and filters["tissue"]:
                    match_conditions["tissue"] = {"$in": filters["tissue"]}
                
                if "year_range" in filters and filters["year_range"]:
                    year_min, year_max = filters["year_range"]
                    match_conditions["year"] = {"$gte": year_min, "$lte": year_max}
            
            # Agregar $match después del $vectorSearch
            pipeline.insert(1, {"$match": match_conditions})
            
            # Agregar proyección para incluir solo campos necesarios
            pipeline.append({
                "$project": {
                    "_id": 0,
                    "source_id": 1,
                    "title": 1,
                    "text": 1,
                    "section": 1,
                    "doi": 1,
                    "osdr_id": 1,
                    "organism": 1,
                    "system": 1,
                    "mission_env": 1,
                    "exposure": 1,
                    "assay": 1,
                    "tissue": 1,
                    "year": 1,
                    "venue": 1,
                    "url": 1,
                    "source_type": 1,
                    "similarity": 1,
                }
            })
            
            # Ejecutar pipeline
            results = list(self.collection.aggregate(pipeline))
            
            # Filtrar por min_similarity
            filtered_results = [doc for doc in results if doc.get("similarity", 0) >= min_similarity]
            
            logger.info(f"📊 MongoDB search: {len(filtered_results)}/{len(results)} chunks above threshold {min_similarity}")
            return filtered_results
        
        except PyMongoError as e:
            logger.error(f"❌ MongoDB search error: {e}")
            return []
    
    def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Obtener chunks por IDs"""
        try:
            results = list(self.collection.find(
                {"source_id": {"$in": ids}},
                {"_id": 0}  # Excluir _id de MongoDB
            ))
            return results
        except PyMongoError as e:
            logger.error(f"❌ MongoDB get_by_ids error: {e}")
            return []
    
    def facet_counts(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, int]]:
        """
        Obtener conteos de facets (para UI de filtros).
        
        Returns:
            Dict con conteos por facet: {"organism": {"Mus musculus": 123, ...}, ...}
        """
        try:
            facet_fields = ["organism", "system", "mission_env", "exposure", "assay", "tissue"]
            result = {}
            
            for field in facet_fields:
                pipeline = [
                    {"$match": {"pk": settings.NASA_DEFAULT_ORG}},
                    {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                
                counts = list(self.collection.aggregate(pipeline))
                result[field] = {item["_id"]: item["count"] for item in counts if item["_id"]}
            
            logger.info(f"📊 Facet counts computed for {len(facet_fields)} fields")
            return result
        except PyMongoError as e:
            logger.error(f"❌ facet_counts error: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check de salud de la conexión"""
        try:
            # Ping a la base de datos
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB health check failed: {e}")
            return False


# Singleton
_mongo_repo: Optional[MongoRepository] = None

def get_mongo_repo() -> MongoRepository:
    """Get or create MongoDB repository instance"""
    global _mongo_repo
    if _mongo_repo is None:
        _mongo_repo = MongoRepository()
    return _mongo_repo
