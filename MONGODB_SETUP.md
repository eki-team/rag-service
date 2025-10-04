# 🗄️ Guía de Setup MongoDB para NASA RAG

Esta guía explica cómo configurar **MongoDB Atlas Vector Search** para el servicio RAG.

---

## 📋 Requisitos

- Cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (tier gratuito disponible)
- Python 3.11+
- Embeddings all-MiniLM-L6-v2 (384 dimensiones, local)

---

## 🚀 Setup Paso a Paso

### 1. Crear Cluster en MongoDB Atlas

1. Ve a [cloud.mongodb.com](https://cloud.mongodb.com)
2. Crea un nuevo cluster (M0 gratis está bien para desarrollo)
3. Configura acceso de red (IP Whitelist: agrega tu IP o `0.0.0.0/0` para desarrollo)
4. Crea usuario de base de datos con permisos de lectura/escritura

### 2. Crear Base de Datos y Colección

```javascript
// En MongoDB Compass o Atlas UI:
use nasa_bio
db.createCollection("pub_chunks")
```

### 3. Crear Índice Vectorial (IMPORTANTE)

**Opción A: Via Atlas UI**

1. Ve a tu cluster → "Search" → "Create Search Index"
2. Selecciona "JSON Editor"
3. Usa esta configuración:

```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 384,
        "similarity": "cosine"
      },
      "organism": {
        "type": "string"
      },
      "mission_env": {
        "type": "string"
      },
      "system": {
        "type": "string"
      },
      "exposure": {
        "type": "string"
      },
      "year": {
        "type": "number"
      },
      "pk": {
        "type": "string"
      }
    }
  }
}
```

4. Nombra el índice: `vector_index`
5. Selecciona colección: `pub_chunks`

**Opción B: Via MongoDB Shell**

```javascript
db.pub_chunks.createSearchIndex(
  "vector_index",
  {
    "mappings": {
      "dynamic": false,
      "fields": {
        "embedding": {
          "type": "knnVector",
          "dimensions": 384,
          "similarity": "cosine"
        },
        "organism": { "type": "string" },
        "mission_env": { "type": "string" },
        "system": { "type": "string" },
        "exposure": { "type": "string" },
        "year": { "type": "number" },
        "pk": { "type": "string" }
      }
    }
  }
)
```

### 4. Configurar `.env`

```bash
# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=nasa_bio
MONGODB_COLLECTION=pub_chunks
MONGODB_VECTOR_INDEX=vector_index

# MongoDB Local
# MONGODB_URI=mongodb://localhost:27017
```

### 5. Insertar Datos de Prueba

```python
from pymongo import MongoClient

client = MongoClient("mongodb+srv://...")
db = client["nasa_bio"]
collection = db["pub_chunks"]

# Documento de prueba
doc = {
    "source_id": "test_chunk_1",
    "pk": "nasa",
    "title": "Test Paper on Microgravity",
    "year": 2024,
    "organism": "Mus musculus",
    "mission_env": "ISS",
    "exposure": "microgravity",
    "section": "Results",
    "text": "This is a test chunk about microgravity effects on mice.",
    "embedding": [0.1] * 384,  # Vector de 384 dimensiones (all-MiniLM-L6-v2)
}

collection.insert_one(doc)
print("✅ Test document inserted")
```

---

## 🧪 Verificar Setup

### Test de Conexión

```python
from pymongo import MongoClient

client = MongoClient("mongodb+srv://...")
db = client["nasa_bio"]
collection = db["pub_chunks"]

# Ping
client.admin.command('ping')
print("✅ MongoDB connected")

# Contar documentos
count = collection.count_documents({})
print(f"📊 Documents in collection: {count}")
```

### Test de Vector Search

```python
pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": [0.1] * 384,  # Vector de prueba (384 dims)
            "numCandidates": 50,
            "limit": 5,
            "similarity": "cosine"
        }
    },
    {
        "$addFields": {
            "similarity": {"$meta": "vectorSearchScore"}
        }
    }
]

results = list(collection.aggregate(pipeline))
print(f"✅ Vector search returned {len(results)} results")
for r in results:
    print(f"  - {r['source_id']}: similarity={r['similarity']:.3f}")
```

---

## 📊 Índices Adicionales (Recomendados)

Para mejorar performance de filtros:

```javascript
// Índices compuestos
db.pub_chunks.createIndex({ "pk": 1, "organism": 1 })
db.pub_chunks.createIndex({ "pk": 1, "mission_env": 1 })
db.pub_chunks.createIndex({ "pk": 1, "year": 1 })
db.pub_chunks.createIndex({ "source_id": 1 }, { unique: true })
```

---

## 🔍 Troubleshooting

### Error: "Index not found"
- El índice vectorial tarda ~5-10 min en estar listo después de crearlo
- Verifica el nombre del índice en Atlas UI

### Error: "numDimensions mismatch"
- `all-MiniLM-L6-v2` = 384 dimensiones
- OpenAI `text-embedding-3-small` = 1536 dimensiones
- OpenAI `text-embedding-3-large` = 3072 dimensiones
- Asegúrate que el índice coincida con tu modelo (384 para este proyecto)

### Performance lento
- Aumenta `numCandidates` en el pipeline (default: top_k * 10)
- Verifica que tienes índices en campos de filtro
- Considera upgrade de tier (M10+) para más RAM

### Connection timeout
- Verifica IP Whitelist en Atlas
- Check firewall local
- Prueba connection string en MongoDB Compass

---

## 📚 Recursos

- [MongoDB Atlas Vector Search Docs](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/)
- [Python Driver (pymongo)](https://pymongo.readthedocs.io/)
- [Vector Search Tutorial](https://www.mongodb.com/docs/atlas/atlas-vector-search/tutorials/)

---

## 💡 Tips

1. **Desarrollo local**: Usa MongoDB Community Server + `mongosh`
2. **Embeddings**: Cachea embeddings para evitar recalcular
3. **Batch inserts**: Usa `insert_many()` para cargas masivas
4. **Monitoring**: Activa Performance Advisor en Atlas
5. **Backup**: Configura snapshots automáticos en producción
