"""
NASA RAG Service - Summary
===========================

✅ COMPLETADO: Refactor de rag-service → NASA Biology RAG

## 📦 Estructura Final:

app/
  ├── api/routers/
  │   ├── chat.py              # POST /api/chat
  │   ├── diag.py              # GET/POST /diag/*
  ├── core/
  │   ├── settings.py          # Config desde .env (OpenAI, Cosmos, NASA)
  │   ├── security.py          # CORS, rate limit
  │   ├── constants.py         # SECTION_PRIORITY, FACETS
  ├── db/
  │   ├── cosmos_repo.py       # Cosmos DB (opción A - PROD)
  │   ├── pgvector_repo.py     # pgvector (opción B - comentada)
  ├── schemas/
  │   ├── chat.py              # ChatRequest, ChatResponse, FilterFacets
  │   ├── diag.py              # Health, Embedding, Retrieval
  │   ├── chunk.py             # Chunk (paper científico)
  ├── services/rag/
  │   ├── retriever.py         # Búsqueda + re-ranking por sección
  │   ├── repository.py        # Orquestador de repos
  │   ├── context_builder.py   # Construcción de contexto
  │   ├── pipeline.py          # Pipeline completo (retrieval → LLM)
  │   ├── prompts/
  │   │   ├── free_nasa.py     # Prompts para modo FREE
  │   │   ├── guided_nasa.py   # (deshabilitado por flag)
  ├── utils/
  │   ├── text.py              # Text processing
  │   ├── audit.py             # Logging de retrieval/grounding
  ├── main.py                  # FastAPI app

CONTEXT/
  ├── rag.txt                  # Contexto original (preservado)
  ├── golden_queries.json      # Queries doradas para audit

.env.example                   # Configuración con variables NASA
requirements.txt               # Dependencias actualizadas
README.md                      # Documentación completa

---

## 🎯 Features Implementadas:

1. ✅ Settings centralizados (settings.py) con NASA config
2. ✅ MongoDB como vector store principal (pgvector comentado)
3. ✅ Filtros facetados (organism, mission_env, exposure, etc.)
4. ✅ Re-ranking por sección (Results > Conclusion > Methods > Intro)
5. ✅ Dedup por DOI
6. ✅ Pipeline RAG completo (embedding → retrieval → synthesis)
7. ✅ Prompts con grounding y citas [N]
8. ✅ Endpoints /api/chat y /diag/*
9. ✅ Golden queries para audit
10. ✅ Logging de retrieval y grounding

---

## 🚀 Para Correr:

1. Configurar .env:
   cp .env.example .env
   # Editar con claves reales

2. Instalar deps:
   pip install -r requirements.txt

3. Correr:
   uvicorn app.main:app --reload --port 8000

4. Abrir docs:
   http://localhost:8000/docs

---

## 🧪 Testing:

# Health check
curl http://localhost:8000/diag/health

# Chat query
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "microgravity immune response", "top_k": 5}'

# Retrieval audit
curl -X POST http://localhost:8000/diag/retrieval_audit

---

## ⚠️ Notas:

- MongoDB usa Atlas Vector Search (requiere índice vectorial configurado)
- pgvector está comentado (descomentar si se usa)
- Modo Guided deshabilitado (NASA_GUIDED_ENABLED=false)
- ETL debe generar chunks con el schema definido en schemas/chunk.py
- Logs se guardan en logs/ (crear directorio si no existe)

---

## 🔧 Próximos Pasos:

1. Configurar MongoDB Atlas con índice vectorial (ver guía en README)
2. Ejecutar ETL para indexar papers de OSDR/LSL/TASKBOOK
3. Validar retrieval con golden queries
4. Ajustar prompts según feedback de usuarios
5. Habilitar rate limiting si se expone públicamente

---

## 📝 Limpieza Realizada:

❌ Eliminados: referencias a TMS, Relator, cursos, empresa (SaveWater)
✅ Mantenidos: estructura base, patrones de rag.txt
✅ Nuevos: esquemas NASA, filtros facetados, prompts especializados

---

## 📧 Contacto:

EKI-TEAM - NASA Biology RAG Project
"""
