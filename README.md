
# 🚀 NASA Biology RAG Service

**RAG (Retrieval-Augmented Generation) service** para investigación en biología espacial de NASA. Indexa y consulta papers científicos de OSDR (Open Science Data Repository), LSL, y TASKBOOK.

---

## 📋 Features

- ✅ **Vector search** con Cosmos DB NoSQL (o pgvector como alternativa)
- ✅ **Filtros facetados**: organism, mission environment, exposure type, tissue, year
- ✅ **Grounding con citas explícitas**: todas las afirmaciones incluyen `[N]` citations
- ✅ **Priorización por sección**: Results > Conclusion > Methods > Introduction
- ✅ **OpenAI embeddings + GPT-4o-mini** para síntesis
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
    cosmos_repo.py    # Cosmos DB (opción A)
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
# Editar .env con tus credenciales (OpenAI, Cosmos DB)
```

### 3. Correr el servicio

```bash
uvicorn app.main:app --reload --port 8000
```

Abre http://localhost:8000/docs para ver la documentación Swagger.

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
  "embedding": [0.1, 0.2, ...]
}
```

Este modelo debe ser generado por el **ETL** (fuera de este repo).

---

## 🔧 Configuración (`.env`)

```bash
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small

VECTOR_BACKEND=cosmos  # cosmos | pgvector
COSMOS_URL=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-key
COSMOS_DB=nasa_bio
COSMOS_CONTAINER=pub_chunks

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

## 🛠️ pgvector (Opción B)

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
- **azure-cosmos**: Cosmos DB
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