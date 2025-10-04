# 🚨 URGENTE: Crear Índice Vectorial en MongoDB Atlas

## ❌ Problema Principal

El health check muestra:
```json
"vector_index_exists": false
```

**Sin el índice vectorial, la búsqueda NO funciona**. MongoDB necesita un índice especial para buscar por vectores.

---

## ✅ Solución: Crear Atlas Vector Search Index

### PASO 1: Ve a MongoDB Atlas

1. Abre tu navegador y ve a: https://cloud.mongodb.com
2. Inicia sesión con tu cuenta
3. Selecciona tu cluster: **nasakb**

### PASO 2: Navega a Atlas Search

1. En el menú lateral, haz clic en **"Atlas Search"** (o "Search")
2. O ve directamente a la pestaña **"Search"** en tu cluster

### PASO 3: Crear el Índice Vectorial

1. Click en **"Create Search Index"**
2. Selecciona **"JSON Editor"** (no usar el wizard)
3. Configura:
   - **Database**: `nasakb`
   - **Collection**: `chunks`
   - **Index Name**: `vector_index`

### PASO 4: Pegar esta Configuración JSON

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "organism"
    },
    {
      "type": "filter",
      "path": "mission_env"
    },
    {
      "type": "filter",
      "path": "system"
    },
    {
      "type": "filter",
      "path": "exposure"
    },
    {
      "type": "filter",
      "path": "assay"
    },
    {
      "type": "filter",
      "path": "tissue"
    },
    {
      "type": "filter",
      "path": "year"
    }
  ]
}
```

### PASO 5: Crear el Índice

1. Click en **"Create Search Index"**
2. Espera 1-2 minutos mientras se construye el índice
3. Verifica que el estado sea **"Active"** (verde)

---

## 🎯 Configuración Explicada

### Campo Vector Principal
```json
{
  "type": "vector",
  "path": "embedding",           // Campo donde están los vectores
  "numDimensions": 1536,          // OpenAI text-embedding-3-small
  "similarity": "cosine"          // Similitud de coseno
}
```

### Campos de Filtro
Los campos con `"type": "filter"` permiten filtrar por metadata:
- `organism`: Mus musculus, Homo sapiens, etc.
- `mission_env`: ISS, LEO, Shuttle, etc.
- `system`: immune, cardiovascular, etc.
- `exposure`: microgravity, radiation, etc.
- `assay`: RNA-seq, proteomics, etc.
- `tissue`: muscle, bone, blood, etc.
- `year`: Año de publicación

---

## 🔍 Verificar que Funciona

### 1. Espera a que el índice esté "Active"

En MongoDB Atlas, el índice debe mostrar:
```
Status: Active ✓
```

### 2. Prueba el Health Endpoint

```bash
GET http://localhost:8000/diag/mongo/health
```

Deberías ver:
```json
{
  "stats": {
    "vector_index_exists": true,  // ✅ Ahora debe ser true
    "vector_index_name": "vector_index"
  }
}
```

### 3. Prueba una Query

```json
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "query": "What are the effects of microgravity on mice?"
}
```

Ahora debería retornar:
```json
{
  "answer": "...(respuesta generada)...",
  "citations": [
    {
      "source_id": "...",
      "title": "...",
      "snippet": "..."
    }
  ],
  "metrics": {
    "retrieved_k": 8  // ✅ Ahora > 0
  }
}
```

---

## 🆘 Troubleshooting

### Error: "Index build failed"

**Causa**: Dimensiones incorrectas o campo no existe

**Solución**:
1. Verifica que los documentos tengan el campo `embedding`
2. Ejecuta este script para verificar:

```python
from pymongo import MongoClient
from app.core.settings import settings

client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB]
collection = db[settings.MONGODB_COLLECTION]

# Verificar un documento
sample = collection.find_one({"embedding": {"$exists": True}})
if sample:
    print(f"✅ Embedding exists: {len(sample['embedding'])} dimensions")
else:
    print("❌ No embeddings found")
```

### Error: "No results in search"

**Causa**: Índice no está "Active" todavía

**Solución**:
- Espera 1-2 minutos más
- Refresca la página de Atlas Search
- Verifica que diga "Active"

---

## 📚 Documentación Oficial

- [Atlas Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/create-index/)
- [Vector Search Tutorial](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-tutorial/)

---

## ⏱️ Tiempo Estimado

- **Crear índice**: 2 minutos
- **Build del índice**: 1-2 minutos
- **Total**: ~5 minutos

---

## 🎉 Después de Crear el Índice

1. ✅ Reinicia el servidor FastAPI
2. ✅ Prueba el health endpoint
3. ✅ Prueba una query de chat
4. ✅ El endpoint de list documents ahora funciona también

**¡Listo para producción!** 🚀
