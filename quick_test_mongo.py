"""
Script de Prueba Rápida - Verificar Datos en MongoDB
"""
from pymongo import MongoClient
from app.core.settings import settings
import json

def quick_test():
    print("=" * 70)
    print("🧪 PRUEBA RÁPIDA DE MONGODB")
    print("=" * 70)
    
    # Conectar
    client_options = {
        'serverSelectionTimeoutMS': 10000,
        'connectTimeoutMS': 10000,
        'socketTimeoutMS': 45000,
        'maxPoolSize': 50,
        'minPoolSize': 10,
        'retryWrites': True,
        'retryReads': True,
        'w': 'majority',
    }
    
    if settings.MONGODB_URI.startswith('mongodb+srv://'):
        client_options.update({
            'tls': True,
            'tlsAllowInvalidCertificates': True,
        })
    
    client = MongoClient(settings.MONGODB_URI, **client_options)
    
    try:
        db = client[settings.MONGODB_DB]
        collection = db[settings.MONGODB_COLLECTION]
        
        # 1. Conteo total
        total = collection.count_documents({})
        print(f"\n✅ Total de chunks: {total}")
        
        # 2. Conteo por DOI (documentos únicos)
        pipeline = [
            {"$group": {"_id": "$doi"}},
            {"$count": "total"}
        ]
        result = list(collection.aggregate(pipeline))
        unique_docs = result[0]["total"] if result else 0
        print(f"✅ Documentos únicos (por DOI): {unique_docs}")
        
        # 3. Verificar embeddings
        with_embeddings = collection.count_documents({"embedding": {"$exists": True}})
        print(f"✅ Chunks con embeddings: {with_embeddings}/{total}")
        
        if with_embeddings > 0:
            sample = collection.find_one({"embedding": {"$exists": True}})
            dims = len(sample["embedding"])
            print(f"✅ Dimensiones del embedding: {dims}")
        
        # 4. Muestra de documentos
        print(f"\n📄 MUESTRA DE DOCUMENTOS (primeros 3):\n")
        
        pipeline = [
            {"$group": {
                "_id": "$doi",
                "title": {"$first": "$title"},
                "year": {"$first": "$year"},
                "organism": {"$first": "$organism"},
                "chunk_count": {"$sum": 1}
            }},
            {"$sort": {"year": -1}},
            {"$limit": 3}
        ]
        
        docs = list(collection.aggregate(pipeline))
        
        for i, doc in enumerate(docs, 1):
            print(f"{i}. {doc.get('title', 'N/A')[:60]}...")
            print(f"   Year: {doc.get('year', 'N/A')}")
            print(f"   Organism: {doc.get('organism', 'N/A')}")
            print(f"   Chunks: {doc.get('chunk_count', 0)}")
            print()
        
        # 5. Verificar índices
        print(f"📊 ÍNDICES DISPONIBLES:\n")
        indexes = list(collection.list_indexes())
        for idx in indexes:
            name = idx.get('name', 'N/A')
            print(f"   - {name}")
        
        vector_index = any('vector' in idx.get('name', '').lower() for idx in indexes)
        if vector_index:
            print(f"\n✅ Índice vectorial encontrado")
        else:
            print(f"\n❌ NO hay índice vectorial")
            print(f"💡 Debes crearlo en MongoDB Atlas (ver CREAR_INDICE_VECTORIAL.md)")
        
        print(f"\n" + "=" * 70)
        print(f"✅ PRUEBA COMPLETADA")
        print(f"=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    quick_test()
