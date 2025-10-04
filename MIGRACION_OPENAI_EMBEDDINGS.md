# 🔄 Migración a OpenAI Embeddings

## ✅ Cambios Realizados

### 1. **Nuevo Servicio de Embeddings**
- **Archivo:** `app/services/embeddings/openai_embeddings.py`
- **Modelo:** `text-embedding-3-small` (OpenAI)
- **Dimensiones:** 1536 (antes: 384)
- **Costo:** $0.02 / 1M tokens

### 2. **Configuración Actualizada**
`.env`:
```properties
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
EMBEDDING_BATCH_SIZE=100
```

### 3. **Ventajas de OpenAI Embeddings**
✅ Mejor calidad de búsqueda semántica
✅ Soporte multilingüe superior
✅ Más dimensiones (1536 vs 384)
✅ No requiere descargar modelos locales
✅ Sin dependencia de PyTorch/transformers
❌ Costo por uso (pero muy económico: $0.02/1M tokens)

---

## ⚠️ IMPORTANTE: Actualizar Índice Vectorial en MongoDB

Como cambiaste de **384 dimensiones** a **1536 dimensiones**, **DEBES recrear el índice vectorial** en MongoDB Atlas.

### Opción 1: Recrear Índice en MongoDB Atlas UI

1. Ve a MongoDB Atlas → Database → Collections
2. Selecciona `mydb.pub_chunks`
3. Ve a "Search Indexes"
4. **ELIMINA** el índice `vector_index` actual (384 dims)
5. Crea nuevo índice con esta configuración:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    }
  ]
}
```

### Opción 2: Crear Índice con MongoDB Shell

```javascript
use mydb;

// Eliminar índice viejo
db.pub_chunks.dropIndex("vector_index");

// Crear índice nuevo (1536 dims)
db.pub_chunks.createSearchIndex(
  "vector_index",
  "vectorSearch",
  {
    fields: [
      {
        type: "vector",
        path: "embedding",
        numDimensions: 1536,
        similarity: "cosine"
      }
    ]
  }
);
```

---

## 🔄 Re-indexar Documentos

**IMPORTANTE:** Todos los embeddings existentes en MongoDB son de 384 dimensiones. Necesitas regenerarlos con OpenAI.

### Script de Re-indexación:

```python
# re_index_with_openai.py
from pymongo import MongoClient
from app.services.embeddings import get_embeddings_service
from app.core.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def re_index_documents():
    """Re-indexa todos los documentos con OpenAI embeddings"""
    
    # Conectar a MongoDB
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    collection = db[settings.MONGODB_COLLECTION]
    
    # Inicializar servicio de embeddings
    embeddings_service = get_embeddings_service()
    
    # Obtener todos los documentos
    total = collection.count_documents({})
    logger.info(f"📊 Total documents to re-index: {total}")
    
    # Procesar en batches
    batch_size = 100
    processed = 0
    
    for skip in range(0, total, batch_size):
        # Obtener batch
        docs = list(collection.find({}, {"_id": 1, "text": 1}).skip(skip).limit(batch_size))
        
        if not docs:
            break
        
        # Extraer textos
        texts = [doc["text"] for doc in docs]
        doc_ids = [doc["_id"] for doc in docs]
        
        # Generar embeddings con OpenAI
        logger.info(f"🔄 Generating embeddings for batch {skip}-{skip+len(docs)}...")
        embeddings = embeddings_service.encode_documents(texts, batch_size=100)
        
        # Actualizar en MongoDB
        for doc_id, embedding in zip(doc_ids, embeddings):
            collection.update_one(
                {"_id": doc_id},
                {"$set": {"embedding": embedding}}
            )
        
        processed += len(docs)
        logger.info(f"✅ Processed {processed}/{total} documents ({processed/total*100:.1f}%)")
    
    logger.info(f"🎉 Re-indexing complete! {processed} documents updated")

if __name__ == "__main__":
    re_index_documents()
```

**Ejecutar:**
```bash
python re_index_with_openai.py
```

---

## 🧪 Testing

### 1. Probar servicio de embeddings:

```bash
curl -X POST "http://localhost:8000/diag/emb" \
  -H "Content-Type: application/json" \
  -d '{"text": "microgravity effects on immune system"}'
```

**Esperas ver:**
```json
{
  "text": "microgravity effects on immune system",
  "embedding_length": 1536,
  "embedding_sample": [0.123, -0.456, ...],
  "model": "text-embedding-3-small"
}
```

### 2. Probar retrieval (sin LLM):

```bash
curl -X POST "http://localhost:8000/diag/retrieval" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the effects of microgravity?",
    "top_k": 5
  }'
```

### 3. Probar RAG chatbot:

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does spaceflight affect the immune system?",
    "top_k": 8
  }'
```

---

## 💰 Costos de OpenAI Embeddings

### text-embedding-3-small
- **Precio:** $0.02 / 1M tokens
- **Ejemplo:** 1000 documentos de 500 palabras cada uno = ~375K tokens = **$0.0075** (menos de 1 centavo)

### Comparación:
- **Sentence-transformers:** Gratis, pero local (requiere CPU/RAM)
- **OpenAI:** Muy barato, mejor calidad, sin overhead local

---

## 📊 Comparación: Sentence-Transformers vs OpenAI

| Aspecto | Sentence-Transformers | OpenAI Embeddings |
|---------|----------------------|-------------------|
| **Modelo** | all-MiniLM-L6-v2 | text-embedding-3-small |
| **Dimensiones** | 384 | 1536 |
| **Calidad** | Buena | Excelente |
| **Velocidad** | Rápido (local) | Depende de API |
| **Costo** | Gratis | $0.02/1M tokens |
| **Dependencias** | PyTorch, transformers | openai (ligero) |
| **Tamaño modelo** | ~90MB | N/A (API) |
| **Uso RAM** | ~500MB | Mínimo |
| **Multilingüe** | Bueno | Excelente |

---

## 🚀 Próximos Pasos

1. ✅ **Servicio creado** - OpenAI embeddings listo
2. ⚠️ **Actualizar índice MongoDB** - Cambiar de 384 a 1536 dims
3. ⚠️ **Re-indexar documentos** - Regenerar embeddings con OpenAI
4. ✅ **Testing** - Probar endpoints `/diag/emb`, `/diag/retrieval`, `/api/chat`

---

## 📝 Notas

- Los embeddings de OpenAI son **mejores** para búsqueda semántica
- El modelo es **multilingüe** (soporta español, inglés, etc.)
- **Costo muy bajo** para proyectos pequeños/medianos
- Si tienes **muchos documentos** (millones), considera sentence-transformers para ahorrar costos
- Para **producción**, OpenAI embeddings es la mejor opción por calidad/costo

---

¿Necesitas ayuda con la re-indexación? ¡Avísame! 🚀
