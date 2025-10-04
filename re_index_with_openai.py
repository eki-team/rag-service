"""
Script para re-indexar documentos con OpenAI embeddings
Convierte embeddings de 384 dims (sentence-transformers) a 1536 dims (OpenAI)
"""
from pymongo import MongoClient
from app.services.embeddings import get_embeddings_service
from app.core.settings import settings
import logging
from tqdm import tqdm
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def re_index_documents(batch_size: int = 50, skip_existing: bool = False):
    """
    Re-indexa todos los documentos con OpenAI embeddings.
    
    Args:
        batch_size: Número de documentos a procesar por batch
        skip_existing: Si True, salta documentos que ya tienen embedding de 1536 dims
    """
    try:
        # Conectar a MongoDB
        logger.info(f"🔌 Connecting to MongoDB: {settings.MONGODB_URI}")
        client = MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=60000,
            connectTimeoutMS=60000,
            socketTimeoutMS=60000
        )
        db = client[settings.MONGODB_DB]
        collection = db[settings.MONGODB_COLLECTION]
        
        # Verificar conexión
        client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {settings.MONGODB_DB}/{settings.MONGODB_COLLECTION}")
        
        # Inicializar servicio de embeddings
        logger.info("🔄 Initializing OpenAI embeddings service...")
        embeddings_service = get_embeddings_service()
        logger.info(f"✅ Embeddings service ready: {embeddings_service.model_name} ({embeddings_service.dimensions} dims)")
        
        # Filtro para documentos a procesar
        query_filter = {}
        if skip_existing:
            # Saltar documentos que ya tienen embedding de 1536 dims
            query_filter = {
                "$or": [
                    {"embedding": {"$exists": False}},
                    {"embedding": {"$size": {"$ne": 1536}}}
                ]
            }
        
        # Obtener total de documentos
        total = collection.count_documents(query_filter)
        logger.info(f"📊 Total documents to re-index: {total}")
        
        if total == 0:
            logger.info("✅ No documents to re-index!")
            return
        
        # Confirmar con usuario
        response = input(f"\n⚠️  ¿Deseas re-indexar {total} documentos con OpenAI embeddings? (y/n): ")
        if response.lower() != 'y':
            logger.info("❌ Re-indexación cancelada")
            return
        
        # Procesar en batches con barra de progreso
        processed = 0
        errors = 0
        
        with tqdm(total=total, desc="Re-indexing", unit="docs") as pbar:
            for skip in range(0, total, batch_size):
                try:
                    # Obtener batch de documentos
                    docs = list(collection.find(
                        query_filter,
                        {"_id": 1, "text": 1, "pk": 1}
                    ).skip(skip).limit(batch_size))
                    
                    if not docs:
                        break
                    
                    # Extraer textos y IDs
                    texts = [doc.get("text", "") for doc in docs]
                    doc_ids = [doc["_id"] for doc in docs]
                    
                    # Filtrar textos vacíos
                    valid_indices = [i for i, text in enumerate(texts) if text.strip()]
                    if not valid_indices:
                        logger.warning(f"⚠️  Batch {skip}-{skip+len(docs)}: No valid texts")
                        pbar.update(len(docs))
                        continue
                    
                    valid_texts = [texts[i] for i in valid_indices]
                    valid_ids = [doc_ids[i] for i in valid_indices]
                    
                    # Generar embeddings con OpenAI
                    logger.debug(f"🔄 Generating embeddings for batch {skip}-{skip+len(valid_texts)}...")
                    embeddings = embeddings_service.encode_documents(valid_texts, batch_size=batch_size)
                    
                    # Validar dimensiones
                    if embeddings and len(embeddings[0]) != 1536:
                        logger.error(f"❌ Invalid embedding dimensions: {len(embeddings[0])}")
                        errors += len(docs)
                        pbar.update(len(docs))
                        continue
                    
                    # Actualizar en MongoDB
                    for doc_id, embedding in zip(valid_ids, embeddings):
                        collection.update_one(
                            {"_id": doc_id},
                            {"$set": {"embedding": embedding}}
                        )
                    
                    processed += len(valid_indices)
                    pbar.update(len(docs))
                    
                except Exception as e:
                    logger.error(f"❌ Error processing batch {skip}-{skip+batch_size}: {e}")
                    errors += len(docs) if docs else batch_size
                    pbar.update(len(docs) if docs else batch_size)
                    continue
        
        # Resumen final
        logger.info("\n" + "="*60)
        logger.info(f"🎉 Re-indexing complete!")
        logger.info(f"✅ Processed: {processed} documents")
        logger.info(f"❌ Errors: {errors} documents")
        logger.info(f"📊 Total: {total} documents")
        logger.info(f"Success rate: {processed/total*100:.1f}%")
        logger.info("="*60)
        
        # Verificar algunos documentos
        logger.info("\n🔍 Verifying sample documents...")
        sample_docs = list(collection.find({"embedding": {"$exists": True}}).limit(3))
        for doc in sample_docs:
            embedding = doc.get("embedding", [])
            logger.info(f"  - {doc.get('pk', 'N/A')}: {len(embedding)} dims")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()
            logger.info("🔌 MongoDB connection closed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Re-index documents with OpenAI embeddings")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for processing (default: 50)"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip documents that already have 1536-dim embeddings"
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting re-indexing process...")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Skip existing: {args.skip_existing}")
    
    re_index_documents(
        batch_size=args.batch_size,
        skip_existing=args.skip_existing
    )
