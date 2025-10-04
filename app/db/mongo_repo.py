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
                        "similarity": "cosine",  # Similitud de coseno
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
    
    # === Frontend API Methods ===
    
    def get_all_documents(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtener lista de documentos únicos (agrupados por source_id principal)
        """
        try:
            pipeline = [
                {"$match": {"pk": settings.NASA_DEFAULT_ORG}},
                {
                    "$group": {
                        "_id": "$doi",  # Agrupar por DOI o paper principal
                        "source_id": {"$first": "$source_id"},
                        "title": {"$first": "$title"},
                        "year": {"$first": "$year"},
                        "doi": {"$first": "$doi"},
                        "osdr_id": {"$first": "$osdr_id"},
                        "organism": {"$first": "$organism"},
                        "mission_env": {"$first": "$mission_env"},
                        "exposure": {"$first": "$exposure"},
                        "system": {"$first": "$system"},
                        "tissue": {"$first": "$tissue"},
                        "assay": {"$first": "$assay"},
                        "chunk_count": {"$sum": 1}
                    }
                },
                {"$sort": {"year": -1}},
                {"$skip": skip},
                {"$limit": limit},
                {
                    "$project": {
                        "_id": 0,
                        "source_id": 1,
                        "title": 1,
                        "year": 1,
                        "doi": 1,
                        "osdr_id": 1,
                        "organism": 1,
                        "mission_env": 1,
                        "exposure": 1,
                        "system": 1,
                        "tissue": 1,
                        "assay": 1,
                        "chunk_count": 1
                    }
                }
            ]
            
            documents = list(self.collection.aggregate(pipeline))
            logger.info(f"📄 Retrieved {len(documents)} unique documents")
            return documents
        except PyMongoError as e:
            logger.error(f"❌ get_all_documents error: {e}")
            return []
    
    def count_documents(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Contar documentos únicos con filtros opcionales"""
        try:
            match_query = {}
            
            if filters:
                if "category" in filters and filters["category"]:
                    match_query["metadata.category"] = filters["category"]
                if "tags" in filters and filters["tags"]:
                    match_query["metadata.tags"] = {"$in": filters["tags"]}
                if "source_type" in filters and filters["source_type"]:
                    match_query["source_type"] = filters["source_type"]
                if "pmc_id" in filters and filters["pmc_id"]:
                    match_query["metadata.article_metadata.pmc_id"] = filters["pmc_id"]
                if "search_text" in filters and filters["search_text"]:
                    match_query["$or"] = [
                        {"text": {"$regex": filters["search_text"], "$options": "i"}},
                        {"metadata.article_metadata.title": {"$regex": filters["search_text"], "$options": "i"}},
                        {"metadata.tags": {"$regex": filters["search_text"], "$options": "i"}}
                    ]
            
            pipeline = [
                {"$match": match_query} if match_query else {"$match": {}},
                {"$group": {"_id": "$pk"}},
                {"$count": "total"}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            count = result[0]["total"] if result else 0
            return count
        except PyMongoError as e:
            logger.error(f"❌ count_documents error: {e}")
            return 0
    
    def search_documents_by_filters(
        self, 
        filters: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Buscar documentos con filtros (sin búsqueda vectorial)"""
        try:
            match_query = {}
            
            if "category" in filters and filters["category"]:
                match_query["metadata.category"] = filters["category"]
            if "tags" in filters and filters["tags"]:
                match_query["metadata.tags"] = {"$in": filters["tags"]}
            if "source_type" in filters and filters["source_type"]:
                match_query["source_type"] = filters["source_type"]
            if "pmc_id" in filters and filters["pmc_id"]:
                match_query["metadata.article_metadata.pmc_id"] = filters["pmc_id"]
            if "search_text" in filters and filters["search_text"]:
                # Búsqueda de texto en título, contenido o tags
                match_query["$or"] = [
                    {"text": {"$regex": filters["search_text"], "$options": "i"}},
                    {"metadata.article_metadata.title": {"$regex": filters["search_text"], "$options": "i"}},
                    {"metadata.tags": {"$regex": filters["search_text"], "$options": "i"}}
                ]
            
            pipeline = [
                {"$match": match_query} if match_query else {"$match": {}},
                {
                    "$group": {
                        "_id": "$pk",
                        "pk": {"$first": "$pk"},
                        "title": {"$first": "$metadata.article_metadata.title"},
                        "source_type": {"$first": "$source_type"},
                        "source_url": {"$first": "$source_url"},
                        "category": {"$first": "$metadata.category"},
                        "tags": {"$first": "$metadata.tags"},
                        "total_chunks": {"$sum": 1},
                        "article_metadata": {"$first": "$metadata.article_metadata"}
                    }
                },
                {"$sort": {"pk": 1}},
                {"$skip": skip},
                {"$limit": limit},
                {
                    "$project": {
                        "_id": 0,
                        "pk": 1,
                        "title": 1,
                        "source_type": 1,
                        "source_url": 1,
                        "category": 1,
                        "tags": 1,
                        "total_chunks": 1,
                        "article_metadata": 1
                    }
                }
            ]
            
            documents = list(self.collection.aggregate(pipeline))
            logger.info(f"🔍 Found {len(documents)} documents matching filters")
            return documents
        except PyMongoError as e:
            logger.error(f"❌ search_documents_by_filters error: {e}")
            return []
    
    def get_document_by_id(self, pk: str) -> Optional[Dict[str, Any]]:
        """Obtener todos los chunks de un documento específico"""
        try:
            # Buscar todos los chunks del documento
            chunks = list(self.collection.find(
                {"pk": pk},
                {"_id": 0, "embedding": 0}  # Excluir _id y embedding
            ).sort("chunk_index", 1))
            
            if not chunks:
                return None
            
            first_chunk = chunks[0]
            metadata = first_chunk.get("metadata", {})
            article_metadata = metadata.get("article_metadata", {})
            
            return {
                "metadata": {
                    "pk": first_chunk.get("pk"),
                    "title": article_metadata.get("title", ""),
                    "source_type": first_chunk.get("source_type"),
                    "source_url": first_chunk.get("source_url"),
                    "category": metadata.get("category"),
                    "tags": metadata.get("tags", []),
                    "total_chunks": len(chunks),
                    "article_metadata": article_metadata
                },
                "chunks": chunks,
                "total_chunks": len(chunks)
            }
        except PyMongoError as e:
            logger.error(f"❌ get_document_by_id error: {e}")
            return None
    
    def get_filter_values(self) -> Dict[str, List[Any]]:
        """Obtener todos los valores únicos para cada filtro"""
        try:
            result = {}
            
            # Obtener categorías únicas
            categories_pipeline = [
                {"$match": {"metadata.category": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$metadata.category"}},
                {"$sort": {"_id": 1}}
            ]
            categories = list(self.collection.aggregate(categories_pipeline))
            result["categories"] = [item["_id"] for item in categories if item["_id"]]
            
            # Obtener source_types únicos
            source_types_pipeline = [
                {"$match": {"source_type": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$source_type"}},
                {"$sort": {"_id": 1}}
            ]
            source_types = list(self.collection.aggregate(source_types_pipeline))
            result["source_types"] = [item["_id"] for item in source_types if item["_id"]]
            
            # Obtener top 50 tags más comunes
            tags_pipeline = [
                {"$match": {"metadata.tags": {"$exists": True, "$ne": []}}},
                {"$unwind": "$metadata.tags"},
                {"$group": {"_id": "$metadata.tags", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 50},
                {"$project": {"_id": 1}}
            ]
            tags = list(self.collection.aggregate(tags_pipeline))
            result["tags"] = [item["_id"] for item in tags if item["_id"]]
            
            # Contar documentos y chunks totales
            total_docs_pipeline = [
                {"$group": {"_id": "$pk"}},
                {"$count": "total"}
            ]
            total_docs_result = list(self.collection.aggregate(total_docs_pipeline))
            result["total_documents"] = total_docs_result[0]["total"] if total_docs_result else 0
            
            result["total_chunks"] = self.collection.count_documents({})
            
            logger.info(f"🎯 Retrieved filter values: {len(result['categories'])} categories, {len(result['tags'])} tags")
            return result
        except PyMongoError as e:
            logger.error(f"❌ get_filter_values error: {e}")
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
