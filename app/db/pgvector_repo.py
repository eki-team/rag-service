"""
NASA Biology RAG - pgvector Repository (Opción B - COMENTADA)
Repositorio para PostgreSQL + pgvector (alternativa a Cosmos).
Este módulo está comentado por defecto. Descomentar si se usa pgvector.
"""

# from typing import List, Dict, Any, Optional
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import sessionmaker
# from app.core.settings import settings
# from loguru import logger
# import json


# class PgvectorRepository:
#     """Repositorio para PostgreSQL + pgvector"""
    
#     def __init__(self):
#         # TODO: Descomentar y configurar DATABASE_URL en settings.py
#         # self.engine = create_engine(settings.DATABASE_URL)
#         # self.SessionLocal = sessionmaker(bind=self.engine)
#         # logger.info("✅ pgvector repo initialized")
#         pass
    
#     def search_vectors(
#         self,
#         query_vec: List[float],
#         filters: Optional[Dict[str, Any]] = None,
#         top_k: int = 8,
#         min_similarity: float = 0.70,
#     ) -> List[Dict[str, Any]]:
#         """
#         Buscar por similitud vectorial usando pgvector (<=> operator).
        
#         Ejemplo de query:
#         SELECT 
#             source_id, title, text, section, doi, osdr_id, 
#             organism, mission_env, year,
#             1 - (embedding <=> :query_vec::vector) AS similarity
#         FROM pub_chunks
#         WHERE pk = :pk
#           AND (organism = ANY(:organisms) OR :organisms IS NULL)
#           AND 1 - (embedding <=> :query_vec::vector) >= :min_similarity
#         ORDER BY embedding <=> :query_vec::vector
#         LIMIT :top_k
#         """
#         # session = self.SessionLocal()
#         # try:
#         #     query = text("""
#         #         SELECT 
#         #             source_id, title, text, section, doi, osdr_id,
#         #             organism, system, mission_env, exposure, year,
#         #             1 - (embedding <=> :query_vec::vector) AS similarity
#         #         FROM pub_chunks
#         #         WHERE pk = :pk
#         #           AND 1 - (embedding <=> :query_vec::vector) >= :min_similarity
#         #         ORDER BY embedding <=> :query_vec::vector
#         #         LIMIT :top_k
#         #     """)
            
#         #     params = {
#         #         "query_vec": json.dumps(query_vec),
#         #         "pk": settings.NASA_DEFAULT_ORG,
#         #         "min_similarity": min_similarity,
#         #         "top_k": top_k,
#         #     }
            
#         #     result = session.execute(query, params)
#         #     rows = result.fetchall()
            
#         #     chunks = []
#         #     for row in rows:
#         #         chunks.append(dict(row._mapping))
            
#         #     logger.info(f"📊 pgvector search: {len(chunks)} chunks")
#         #     return chunks
        
#         # finally:
#         #     session.close()
#         pass
    
#     def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
#         """Obtener chunks por IDs"""
#         # session = self.SessionLocal()
#         # try:
#         #     query = text("SELECT * FROM pub_chunks WHERE source_id = ANY(:ids)")
#         #     result = session.execute(query, {"ids": ids})
#         #     return [dict(row._mapping) for row in result.fetchall()]
#         # finally:
#         #     session.close()
#         pass
    
#     def facet_counts(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, int]]:
#         """Conteos por facet"""
#         # TODO: Implementar con GROUP BY
#         pass
    
#     def health_check(self) -> bool:
#         """Health check"""
#         # session = self.SessionLocal()
#         # try:
#         #     session.execute(text("SELECT 1"))
#         #     return True
#         # except:
#         #     return False
#         # finally:
#         #     session.close()
#         pass


# # Singleton
# _pgvector_repo: Optional[PgvectorRepository] = None

# def get_pgvector_repo() -> PgvectorRepository:
#     """Get or create pgvector repository instance"""
#     global _pgvector_repo
#     if _pgvector_repo is None:
#         _pgvector_repo = PgvectorRepository()
#     return _pgvector_repo
