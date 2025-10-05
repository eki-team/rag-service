
# 🚀 NASA Biology RAG Service

**RAG (Retrieval-Augmented Generation) service** para investigación en biología espacial de NASA. Indexa y consulta papers científicos de OSDR (Open Science Data Repository), LSL, y TASKBOOK.

---

## 📋 Features

### 🎯 Advanced RAG System (v2.0)
- ✅ **Query Expansion** con TAG_DICT (80+ conceptos → 300+ términos)
- ✅ **Reranking avanzado** con 8 señales (similarity, section, authority, recency, diversity, etc.)
- ✅ **Section-aware** con prioridades: Abstract/Results (+0.10) > Discussion (+0.07) > Methods (+0.03)
- ✅ **Authority boost** para fuentes confiables (nasa.gov, nature.com, science.org)
- ✅ **Diversity enforcement**: Máx 2 chunks/documento, cobertura ≥3 fuentes
- ✅ **Citas estrictas**: TODAS las afirmaciones incluyen `[N]` citations (mandatory)
- ✅ **Faithfulness**: Solo información del contexto, NO external knowledge
- ✅ **Grounding metrics**: % de sentences con citas (target: ≥80%)

### 🔧 Infrastructure
- ✅ **Vector search** con MongoDB Atlas (1536 dims OpenAI embeddings, cosine similarity)
- ✅ **Filtros facetados**: organism, mission environment, exposure type, tissue, year
- ✅ **GPT-4o-mini** para síntesis (OpenAI)
- ✅ **Endpoints de diagnóstico**: health, embeddings, retrieval, audit

📖 **Ver documentación completa**: [ADVANCED_RAG.md](./ADVANCED_RAG.md)

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
    pipeline.py       # Pipeline completo RAG
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

**Response (con Advanced RAG):**
```json
{
  "answer": "Microgravity exposure leads to significant immune dysregulation in mice [1][3]. RNA-seq analysis revealed upregulation of pro-inflammatory cytokines including IL-6 and TNF-α [2]. Studies on the ISS showed decreased T-cell proliferation and altered cytokine profiles [1]. While baseline immune function recovered after 7 days post-landing [3], chronic spaceflight may pose increased infection risk [4].",
  "citations": [
    {
      "source_id": "GLDS-123_chunk_5",
      "doi": "10.1038/s41586-2023-12345",
      "section": "Results",
      "snippet": "RNA-seq analysis revealed significant upregulation of pro-inflammatory cytokines...",
      "year": 2023,
      "url": "https://www.nature.com/articles/...",
      "rerank_score": 0.9145,
      "relevance_reason": "Sim: 0.823 | Sec: 0.100 | Keyword: 0.654 | Authority: 0.070 | Final: 0.915"
    }
  ],
  "metrics": {
    "latency_ms": 2345.67,
    "retrieved_k": 6,
    "grounded_ratio": 0.92,
    "section_distribution": {
      "Results": 3,
      "Discussion": 2,
      "Abstract": 1
    }
  }
}
```

---

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

## 🧪 Evaluación del RAG

Este proyecto incluye un **evaluador automático completo** usando RAGAS + LangChain LLM-as-Judge.

### Métricas evaluadas:
- **RAGAS**: answer_relevancy, faithfulness, context_precision, context_recall
- **LLM-as-Judge**: bias, toxicity
- **Custom**: grounded_ratio (% oraciones con [N] citations)

### Quick Start:

```bash
# Instalar dependencias de evaluación
pip install -r requirements_eval.txt

# Test rápido (1 query)
python test_eval_quick.py

# Evaluación completa (15 queries)
python eval_rag_nasa.py
```

**Documentación completa**: Ver [EVAL_GUIDE.md](EVAL_GUIDE.md)

---

## 📝 TODOs

- [x] Sistema de evaluación automática (RAGAS + LLM-as-Judge)
- [ ] BM25 híbrido (keyword + vector)
- [ ] Re-ranking con LLM
- [ ] Facet counts en Cosmos
- [ ] Cache de embeddings
- [ ] Streaming de respuestas
- [ ] Modo Guided completo