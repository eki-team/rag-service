# 🏗️ Arquitectura de la API - RAG Service

## 📌 Resumen

Este servicio tiene **DOS APIs completamente separadas**:

1. **`/api/chat`** → RAG con IA (búsqueda vectorial + LLM)
2. **`/api/front/*`** → API REST tradicional (solo base de datos)

---

## 1️⃣ `/api/chat` - RAG con Inteligencia Artificial

### 🎯 Propósito
Chatbot inteligente que responde preguntas sobre documentos científicos usando IA.

### 🔧 Tecnología Utilizada
- **OpenAI Embeddings** (text-embedding-3-small, 1536 dimensiones)
- **MongoDB Atlas Vector Search** para búsqueda semántica
- **OpenAI GPT-4o-mini** para generar respuestas
- **RAG Pipeline completo** (Retrieval + Generation)

### 📡 Endpoint

```http
POST /api/chat
Content-Type: application/json

{
  "query": "What are the effects of microgravity on mice?",
  "filters": {
    "organism": ["Mus musculus"],
    "mission_env": ["ISS"]
  },
  "top_k": 8
}
```

### ⚙️ Flujo de Procesamiento

```
1. Usuario envía pregunta
   ↓
2. Se genera embedding OpenAI de la pregunta (1536 dims)
   ↓
3. Búsqueda vectorial en MongoDB Atlas
   ↓
4. Se recuperan los chunks más relevantes
   ↓
5. Se envían al LLM (GPT-4o-mini) junto con la pregunta
   ↓
6. LLM genera respuesta con citas
   ↓
7. Se retorna respuesta + fuentes + metadata
```

### 📦 Respuesta

```json
{
  "answer": "Microgravity has significant effects on mice...",
  "sources": [
    {
      "text": "Study results showed...",
      "metadata": {
        "title": "Mice in Space Mission",
        "doi": "10.1234/example",
        "chunk_index": 3
      }
    }
  ],
  "query": "What are the effects of microgravity on mice?",
  "model": "gpt-4o-mini"
}
```

### 💰 Costos
- **Embeddings**: $0.02 por 1M tokens (~$0.0005 por query)
- **LLM**: Variable según respuesta (~$0.001-0.005 por query)
- **Total estimado**: ~$0.002-0.006 por consulta

---

## 2️⃣ `/api/front/*` - API REST Tradicional

### 🎯 Propósito
API REST para frontend que permite listar, buscar y filtrar documentos **sin usar IA**.

### 🔧 Tecnología Utilizada
- **MongoDB** con queries tradicionales (no vectorial)
- **Agregaciones** para agrupar documentos
- **Text Search** con regex para búsqueda de texto
- **Filtros facetados** (categorías, tags, etc.)

### ⚡ **NO USA:**
- ❌ OpenAI embeddings
- ❌ Búsqueda vectorial
- ❌ LLM para generar respuestas
- ❌ Costos por consulta

### 📡 Endpoints

#### 1. **Listar Documentos**
```http
GET /api/front/documents?skip=0&limit=20
```

**Respuesta:**
```json
{
  "total": 150,
  "documents": [
    {
      "pk": "mice-in-bion-m-1-space-mission",
      "title": "Mice in Bion-M 1 Space Mission",
      "source_type": "article",
      "category": "space",
      "tags": ["mice", "microgravity", "mission"],
      "total_chunks": 55,
      "article_metadata": {
        "title": "Mice in Bion-M 1 Space Mission",
        "authors": ["Author 1", "Author 2"],
        "pmc_id": "PMC1234567",
        "doi": "10.1234/example"
      }
    }
  ]
}
```

#### 2. **Buscar con Filtros**
```http
POST /api/front/documents/search?skip=0&limit=20
Content-Type: application/json

{
  "category": "space",
  "tags": ["mice", "mission"],
  "search_text": "microgravity",
  "pmc_id": "PMC1234567"
}
```

**Búsqueda realizada:**
- ✅ Búsqueda de texto con **regex** (MongoDB $regex)
- ✅ Filtrado por categoría (exact match)
- ✅ Filtrado por tags (array contains)
- ✅ Filtrado por PMC ID (exact match)
- ❌ **NO usa embeddings ni búsqueda semántica**

**Respuesta:** Misma estructura que `GET /documents`

#### 3. **Detalle de Documento**
```http
GET /api/front/documents/{pk}
```

**Respuesta:**
```json
{
  "metadata": {
    "pk": "mice-in-bion-m-1-space-mission",
    "title": "Mice in Bion-M 1 Space Mission",
    "total_chunks": 55,
    "article_metadata": {...}
  },
  "chunks": [
    {
      "text": "This study examines...",
      "chunk_index": 0,
      "total_chunks": 55
    }
  ],
  "total_chunks": 55
}
```

#### 4. **Valores de Filtros**
```http
GET /api/front/filters
```

**Respuesta:**
```json
{
  "categories": ["space", "biology", "medicine"],
  "tags": ["mice", "mission", "microgravity", "immune"],
  "source_types": ["article"]
}
```

#### 5. **Estadísticas**
```http
GET /api/front/stats
```

**Respuesta:**
```json
{
  "total_documents": 150,
  "total_chunks": 8234,
  "categories": {
    "space": 85,
    "biology": 45,
    "medicine": 20
  },
  "tags_count": 234
}
```

### ⚙️ Flujo de Procesamiento (Frontend API)

```
1. Usuario solicita datos
   ↓
2. Se construye query MongoDB tradicional
   ↓
3. Se aplican filtros ($match, $regex, $in)
   ↓
4. Se agrupan resultados por documento ($group)
   ↓
5. Se paginan resultados ($skip, $limit)
   ↓
6. Se retorna JSON con datos
```

### 💰 Costos
- **Costo por consulta**: $0 (solo base de datos)
- **Límite de rate**: Ninguno (depende de MongoDB)

---

## 🔄 Comparación

| Característica | `/api/chat` (RAG) | `/api/front/*` (REST) |
|----------------|-------------------|----------------------|
| **Propósito** | Chatbot inteligente | API de datos |
| **Usa IA** | ✅ Sí (OpenAI) | ❌ No |
| **Búsqueda** | Vectorial semántica | Texto regex + filtros |
| **Embeddings** | ✅ OpenAI (1536D) | ❌ No |
| **LLM** | ✅ GPT-4o-mini | ❌ No |
| **MongoDB** | Vector Search | Queries normales |
| **Costo/query** | ~$0.002-0.006 | $0 |
| **Respuesta** | Texto generado + fuentes | JSON de base de datos |
| **Uso** | Responder preguntas | Listar/filtrar documentos |

---

## 📂 Estructura de Código

```
app/
├── api/
│   └── routers/
│       ├── chat.py         ← RAG con IA (usa embeddings + LLM)
│       └── front.py        ← API REST (solo MongoDB)
│
├── services/
│   ├── embeddings/
│   │   ├── openai_embeddings.py    ← Solo para /api/chat
│   │   └── __init__.py
│   │
│   └── rag/
│       └── pipeline.py             ← Solo para /api/chat
│
└── db/
    └── mongo_repo.py
        ├── search()                     ← Vector search (para chat.py)
        ├── search_documents_by_filters() ← Regex + filtros (para front.py)
        ├── get_all_documents()          ← Listado (para front.py)
        └── get_document_by_id()         ← Detalle (para front.py)
```

---

## 🎯 Casos de Uso

### Para `/api/chat` (RAG):
- ❓ "¿Cuáles son los efectos de la microgravedad en ratones?"
- ❓ "¿Qué estudios hay sobre respuesta inmune en el espacio?"
- ❓ "Explícame los hallazgos del estudio BION-M1"
- ✅ **Responde con lenguaje natural + citas científicas**

### Para `/api/front/*` (REST):
- 📄 Mostrar lista de papers en la UI
- 🔍 Buscar papers por categoría/tags/texto
- 📊 Mostrar estadísticas del dataset
- 🔗 Obtener detalle de un paper específico
- 🏷️ Obtener valores de filtros para dropdowns
- ✅ **Retorna datos estructurados para renderizar en frontend**

---

## 🚀 Arrancar el Servicio

```powershell
# Instalar dependencias (si no está hecho)
pip install -r requirements.txt

# Verificar .env
# OPENAI_API_KEY=sk-proj-...        ← Solo para /api/chat
# MONGODB_URI=mongodb://...         ← Para ambas APIs
# EMBEDDING_MODEL=text-embedding-3-small  ← Solo para /api/chat
# EMBEDDING_DIMENSIONS=1536         ← Solo para /api/chat

# Arrancar servidor
uvicorn app.main:app --reload --port 8000
```

### Verificar funcionamiento:

```powershell
# Health check general
curl http://localhost:8000/health

# Test /api/chat (RAG con IA)
curl -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{"query": "microgravity effects on mice"}'

# Test /api/front (REST sin IA)
curl http://localhost:8000/api/front/documents?limit=5
```

---

## ⚠️ Importante

### MongoDB Atlas Vector Index
Para que `/api/chat` funcione correctamente, debes:

1. **Actualizar el índice vectorial en MongoDB Atlas** a 1536 dimensiones:
   ```javascript
   db.pub_chunks.createSearchIndex("vector_index", "vectorSearch", {
     fields: [{
       type: "vector",
       path: "embedding",
       numDimensions: 1536,
       similarity: "cosine"
     }]
   });
   ```

2. **Re-indexar documentos existentes** (opcional):
   ```powershell
   python re_index_with_openai.py --batch-size 50
   ```

### `/api/front` NO REQUIERE:
- ❌ Actualizar índice vectorial
- ❌ Re-indexar documentos
- ❌ OpenAI API key (puede funcionar sin ella)
- ✅ **Funciona inmediatamente** con MongoDB local o Atlas

---

## 📝 Conclusión

Tu aplicación tiene **dos APIs independientes**:

1. **`/api/chat`** → Chatbot RAG inteligente (búsqueda semántica + IA)
2. **`/api/front/*`** → API REST tradicional (solo base de datos)

Ambas funcionan con la **misma base de datos MongoDB**, pero:
- `/api/chat` usa el campo `embedding` + OpenAI
- `/api/front/*` usa campos normales + queries tradicionales

**Frontend puede usar ambas:**
- Listar/filtrar documentos → `/api/front/*`
- Chatbot de preguntas → `/api/chat`

✅ **Ya está todo configurado correctamente!**
