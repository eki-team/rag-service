
# 🚀 NASA Biology RAG Service

**RAG (Retrieval-Augmented Generation) service** para investigación en biología espacial de NASA. Indexa y consulta papers científicos de OSDR (Open Science Data Repository), LSL, y TASKBOOK.

---

## 📋 Features

- ✅ **Vector search** con MongoDB Atlas (384 dims, cosine similarity)
- ✅ **Local embeddings** con all-MiniLM-L6-v2 (~14K oraciones/seg en CPU)
- ✅ **Filtros facetados**: organism, mission environment, exposure type, tissue, year
- ✅ **Grounding con citas explícitas**: todas las afirmaciones incluyen `[N]` citations
- ✅ **Priorización por sección**: Results > Conclusion > Methods > Introduction
- ✅ **GPT-4o-mini** para síntesis (OpenAI)
- ✅ **Endpoints de diagnóstico**: health, embeddings, retrieval, audit

---

## 🏗️ Architecture

```
app/
  api/routers/
    chat.py           # POST /api/chat
    diag.py           # GET/POST /diag/*
  core/
    settings.py       # Config desde .env
    security.py       # CORS, rate limit
    constants.py      # FACETS, SECTION_PRIORITY
  db/
    mongo_repo.py     # MongoDB (opción A)
    pgvector_repo.py  # pgvector (opción B, comentada)
  schemas/
    chat.py           # ChatRequest, ChatResponse
    diag.py           # Health, Embedding, Retrieval
    chunk.py          # Chunk (paper científico)
  services/rag/
    retriever.py      # Búsqueda + re-ranking
    repository.py     # Orquestador
    context_builder.py# Construcción de contexto
    pipeline.py       # Pipeline completo
    prompts/
      free_nasa.py    # Prompts FREE mode
      guided_nasa.py  # (deshabilitado)
  utils/
    text.py           # Text processing
    audit.py          # Logging
  main.py             # FastAPI app
```

---

## � Quick Start

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar `.env`

```bash
cp .env.example .env
# Editar .env con tus credenciales (OpenAI API key para LLM, MongoDB URI)
```

**Nota**: Los embeddings son **locales** (no requieren API key). El modelo `all-MiniLM-L6-v2` se descarga automáticamente (~80 MB) en la primera ejecución.

### 3. Test embeddings (opcional)

```bash
python test_embeddings.py
```

Esto verifica que sentence-transformers funcione correctamente y muestra el rendimiento.

### 4. Correr el servicio

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Test rápido (sin Postman)

```bash
python quick_test_chat.py
```

Esto verifica que el endpoint `/api/chat` funcione correctamente.

### 6. Testing con Postman

📦 **Importa la colección**: `NASA_RAG.postman_collection.json`

Ver guía completa en: **[POSTMAN_GUIDE.md](POSTMAN_GUIDE.md)**

**Documentación interactiva:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📡 Endpoints

### POST /api/chat

RAG completo: pregunta → retrieval → síntesis → respuesta con citas.

**Request:**
```json
{
  "query": "What are the effects of microgravity on immune response in mice?",
  "filters": {
    "organism": ["Mus musculus"],
    "mission_env": ["ISS"],
    "exposure": ["microgravity"]
  },
  "top_k": 8
}
```

**Response:**
```json
{
  "answer": "Studies show that microgravity exposure leads to immune dysregulation [1][2]...",
  "citations": [
    {
      "source_id": "GLDS-123_chunk_5",
      "doi": "10.1038/...",
      "section": "Results",
      "snippet": "RNA-seq analysis revealed..."
    }
  ],
  "metrics": {
    "latency_ms": 1234.5,
    "retrieved_k": 8,
    "grounded_ratio": 0.92
  }
}
```

### GET /diag/health

Health check del servicio.

### POST /diag/emb

Generar embedding de un texto (debug).

### POST /diag/retrieval

Test de retrieval sin síntesis (debug).

### POST /diag/retrieval_audit

Audit de retrieval usando queries doradas (`CONTEXT/golden_queries.json`).

---

## 🎯 Filtros Facetados

| Facet | Ejemplo |
|-------|---------|
| `organism` | `["Mus musculus"]` |
| `system` | `["human", "plant"]` |
| `mission_env` | `["ISS", "LEO", "Lunar"]` |
| `exposure` | `["microgravity", "radiation"]` |
| `assay` | `["RNA-seq", "proteomics"]` |
| `tissue` | `["muscle", "bone"]` |
| `year_range` | `[2020, 2024]` |

---

## 🗂️ Modelo de Datos (Chunk)

Cada chunk indexado en el vector store:

```python
{
  "source_id": "GLDS-123_chunk_5",
  "pk": "nasa",
  "title": "Paper title",
  "year": 2023,
  "doi": "10.1038/...",
  "osdr_id": "GLDS-123",
  "organism": "Mus musculus",
  "mission_env": "ISS",
  "exposure": "microgravity",
  "section": "Results",
  "text": "Chunk text...",
  "embedding": [0.1, 0.2, ...]  # 384 dims (all-MiniLM-L6-v2)
}
```

Este modelo debe ser generado por el **ETL** (fuera de este repo).

---

## 🔧 Configuración (`.env`)

```bash
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small

VECTOR_BACKEND=mongodb  # mongodb | pgvector
MONGODB_URI=mongodb://localhost:27017
# Para Atlas: mongodb+srv://user:password@cluster.mongodb.net/
MONGODB_DB=nasa_bio
MONGODB_COLLECTION=pub_chunks
MONGODB_VECTOR_INDEX=vector_index

NASA_MODE=true
NASA_GUIDED_ENABLED=false
DEFAULT_TOP_K=8
MIN_SIMILARITY=0.70
```

---

## � Testing

### Query manual (cURL)

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Effects of microgravity on bone density",
    "filters": {"organism": ["Homo sapiens"], "tissue": ["bone"]},
    "top_k": 5
  }'
```

### Health check

```bash
curl http://localhost:8000/diag/health
```

---

## �️ MongoDB Atlas Vector Search

Este servicio usa **MongoDB Atlas Vector Search** para búsquedas vectoriales. Necesitas:

1. **Crear un índice vectorial** en tu colección:

```javascript
// En MongoDB Atlas, crear índice vectorial:
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
      "path": "year"
    }
  ]
}
```

2. **Configurar URI** en `.env`:
   - Local: `mongodb://localhost:27017`
   - Atlas: `mongodb+srv://user:password@cluster.mongodb.net/`

---

## �🛠️ pgvector (Opción B)

Si prefieres PostgreSQL + pgvector:

1. Descomentar `app/db/pgvector_repo.py`
2. Configurar en `.env`:
   ```bash
   VECTOR_BACKEND=pgvector
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your-password
   POSTGRES_DB=nasa_rag
   ```

---

## 📦 Dependencias

- **fastapi**, **uvicorn**: API
- **httpx**: Cliente HTTP (OpenAI)
- **pymongo**: MongoDB driver
- **tiktoken**: Token counting
- **loguru**: Logging
- **rapidfuzz**: Dedup/snippets

---

## 📝 TODOs

- [ ] BM25 híbrido (keyword + vector)
- [ ] Re-ranking con LLM
- [ ] Facet counts en Cosmos
- [ ] Cache de embeddings
- [ ] Streaming de respuestas
- [ ] Modo Guided completo