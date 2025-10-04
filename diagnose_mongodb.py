"""
Diagnóstico de Datos en MongoDB
Verifica la estructura y contenido de la colección chunks
"""
from pymongo import MongoClient
from app.core.settings import settings
import json

def diagnose_mongodb():
    """Diagnóstico completo de MongoDB"""
    print("=" * 70)
    print("🔍 DIAGNÓSTICO DE MONGODB - Colección 'chunks'")
    print("=" * 70)
    
    # Conectar
    print(f"\n📌 Conectando a: {settings.MONGODB_DB}/{settings.MONGODB_COLLECTION}")
    
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
        # Test conexión
        client.admin.command('ping')
        print("✅ Conexión exitosa\n")
        
        db = client[settings.MONGODB_DB]
        collection = db[settings.MONGODB_COLLECTION]
        
        # 1. Conteo total
        print("=" * 70)
        print("📊 ESTADÍSTICAS GENERALES")
        print("=" * 70)
        
        total_count = collection.count_documents({})
        print(f"📦 Total de documentos: {total_count}")
        
        if total_count == 0:
            print("\n❌ ¡LA COLECCIÓN ESTÁ VACÍA!")
            print("\n💡 Necesitas importar datos primero:")
            print("   1. Ejecutar el script ETL que tengas")
            print("   2. O importar desde un backup")
            print("   3. O verificar que la colección se llame 'chunks'")
            return
        
        # 2. Verificar campo 'pk'
        print(f"\n🔎 Verificando campo 'pk' (esperado: '{settings.NASA_DEFAULT_ORG}')...")
        
        pk_counts = list(collection.aggregate([
            {"$group": {"_id": "$pk", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        print(f"\n   Valores de 'pk' encontrados:")
        for item in pk_counts:
            pk_value = item['_id']
            count = item['count']
            emoji = "✅" if pk_value == settings.NASA_DEFAULT_ORG else "⚠️"
            print(f"   {emoji} '{pk_value}': {count} docs")
        
        # 3. Verificar campo 'embedding'
        print(f"\n🔎 Verificando campo 'embedding' (vector)...")
        
        docs_with_embedding = collection.count_documents({"embedding": {"$exists": True}})
        print(f"   📊 Documentos con 'embedding': {docs_with_embedding}/{total_count}")
        
        if docs_with_embedding == 0:
            print(f"   ❌ ¡Ningún documento tiene embeddings!")
            print(f"   💡 Necesitas generar embeddings primero")
        else:
            # Verificar dimensiones
            sample = collection.find_one({"embedding": {"$exists": True}})
            if sample and "embedding" in sample:
                embedding_dims = len(sample["embedding"])
                expected_dims = settings.EMBEDDING_DIMENSIONS
                emoji = "✅" if embedding_dims == expected_dims else "⚠️"
                print(f"   {emoji} Dimensiones del vector: {embedding_dims} (esperado: {expected_dims})")
        
        # 4. Verificar índice vectorial
        print(f"\n🔎 Verificando índice vectorial...")
        
        indexes = list(collection.list_indexes())
        vector_index_found = False
        
        print(f"   📋 Índices encontrados:")
        for idx in indexes:
            idx_name = idx.get('name', 'N/A')
            print(f"      - {idx_name}")
            
            if idx_name == settings.MONGODB_VECTOR_INDEX or 'vector' in idx_name.lower():
                vector_index_found = True
        
        if not vector_index_found:
            print(f"\n   ⚠️  No se encontró el índice vectorial '{settings.MONGODB_VECTOR_INDEX}'")
            print(f"   💡 Debes crear un Atlas Vector Search Index en MongoDB Atlas:")
            print(f"      1. Ve a tu cluster en MongoDB Atlas")
            print(f"      2. Pestaña 'Atlas Search'")
            print(f"      3. Crear índice con nombre: '{settings.MONGODB_VECTOR_INDEX}'")
            print(f"      4. Campo: 'embedding', Dimensiones: {settings.EMBEDDING_DIMENSIONS}, Similitud: cosine")
        else:
            print(f"   ✅ Índice vectorial encontrado")
        
        # 5. Muestra de documento
        print(f"\n=" * 70)
        print("📄 MUESTRA DE DOCUMENTO (primero)")
        print("=" * 70)
        
        sample_doc = collection.find_one({})
        if sample_doc:
            # Ocultar embedding para no saturar output
            if "embedding" in sample_doc:
                embedding_info = f"[Vector de {len(sample_doc['embedding'])} dimensiones]"
                sample_doc["embedding"] = embedding_info
            
            # Ocultar _id de Mongo
            if "_id" in sample_doc:
                del sample_doc["_id"]
            
            print(json.dumps(sample_doc, indent=2, ensure_ascii=False))
        
        # 6. Campos disponibles
        print(f"\n=" * 70)
        print("🗂️  CAMPOS DISPONIBLES EN DOCUMENTOS")
        print("=" * 70)
        
        # Obtener todos los campos únicos
        pipeline = [
            {"$limit": 100},  # Muestra de 100 docs
            {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
            {"$unwind": "$arrayofkeyvalue"},
            {"$group": {"_id": "$arrayofkeyvalue.k"}},
            {"$sort": {"_id": 1}}
        ]
        
        fields = list(collection.aggregate(pipeline))
        print(f"\n   Campos encontrados ({len(fields)}):")
        for field in fields:
            field_name = field['_id']
            print(f"      - {field_name}")
        
        # 7. Valores de campos facetados
        print(f"\n=" * 70)
        print("🏷️  VALORES DE CAMPOS FACETADOS (top 5 cada uno)")
        print("=" * 70)
        
        facet_fields = ["organism", "system", "mission_env", "exposure", "assay", "tissue"]
        
        for field in facet_fields:
            # Verificar si el campo existe
            count_with_field = collection.count_documents({field: {"$exists": True, "$ne": None}})
            
            if count_with_field == 0:
                print(f"\n   ⚠️  Campo '{field}': No existe o está vacío")
                continue
            
            pipeline = [
                {"$match": {field: {"$exists": True, "$ne": None}}},
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            top_values = list(collection.aggregate(pipeline))
            
            print(f"\n   ✅ Campo '{field}' ({count_with_field} docs):")
            for item in top_values:
                value = item['_id']
                count = item['count']
                print(f"      - {value}: {count}")
        
        # 8. Resumen final
        print(f"\n=" * 70)
        print("📋 RESUMEN DEL DIAGNÓSTICO")
        print("=" * 70)
        
        issues = []
        
        if total_count == 0:
            issues.append("❌ Colección vacía - necesitas importar datos")
        
        if docs_with_embedding == 0:
            issues.append("❌ No hay embeddings - necesitas generarlos")
        
        if not vector_index_found:
            issues.append("❌ Falta índice vectorial en MongoDB Atlas")
        
        # Verificar si el pk correcto existe
        correct_pk_count = collection.count_documents({"pk": settings.NASA_DEFAULT_ORG})
        if correct_pk_count == 0:
            issues.append(f"⚠️  No hay documentos con pk='{settings.NASA_DEFAULT_ORG}'")
        
        if issues:
            print("\n⚠️  PROBLEMAS DETECTADOS:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("\n✅ ¡Todo parece estar correcto!")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    diagnose_mongodb()
