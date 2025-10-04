# ✅ Frontend API - Adaptada a Estructura Real

## 🎯 Cambios Realizados

He adaptado **completamente** el Frontend API para que funcione con tu estructura real de MongoDB.

---

## 📝 Archivos Actualizados

### 1. **`app/schemas/front.py`** ✅
- ✅ Eliminados campos inexistentes (`source_id`, `organism`, `mission_env`, `year`, etc.)
- ✅ Añadidos campos reales: `pk`, `category`, `tags`, `source_type`, `source_url`
- ✅ Añadido schema `ArticleMetadata` para `metadata.article_metadata`
- ✅ Schemas ahora coinciden 100% con tu estructura MongoDB

### 2. **`app/db/mongo_repo.py`** ✅
- ✅ `get_all_documents()`: Agrupa por `pk`, extrae `metadata.article_metadata.title`
- ✅ `count_documents()`: Filtra por `category`, `tags`, `search_text`, `pmc_id`
- ✅ `search_documents_by_filters()`: Búsqueda por campos reales
- ✅ `get_document_by_id()`: Busca por `pk` (no `source_id`)
- ✅ `get_filter_values()`: Retorna `categories`, `tags`, `source_types` únicos

### 3. **`app/api/routers/front.py`** ✅
- ✅ Endpoints actualizados para usar schemas correctos
- ✅ Conversión de datos MongoDB → Pydantic schemas
- ✅ Manejo correcto de `metadata.article_metadata` anidado
- ✅ Path parameter `{pk}` en lugar de `{source_id}`

### 4. **`FRONTEND_API_REAL_STRUCTURE.md`** 📚
- Guía completa con ejemplos usando tu estructura real
- Casos de uso en JavaScript
- Schemas TypeScript
- Troubleshooting

---

## 🔑 Diferencias Clave: Antes vs Ahora

| Campo Anterior (Inventado) | Campo Real (Tu BD) |
|----------------------------|-------------------|
| `source_id` | `pk` |
| `organism`, `mission_env`, `exposure` | No existen |
| `year`, `doi` (campo raíz) | `metadata.article_metadata.doi` |
| `title` (campo raíz) | `metadata.article_metadata.title` |
| - | `metadata.tags` (array) |
| - | `metadata.category` (string) |
| - | `metadata.char_count`, `word_count` |

---

## 🚀 Endpoints Actualizados

### ✅ GET /api/front/documents
```bash
curl "http://localhost:8000/api/front/documents?skip=0&limit=20"
```
**Retorna:** Lista de documentos agrupados por `pk`

### ✅ POST /api/front/documents/search
```bash
curl -X POST "http://localhost:8000/api/front/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "space",
    "tags": ["mice", "mission"],
    "search_text": "microgravity"
  }'
```
**Filtros reales:**
- `category`: "space", "biology", etc
- `tags`: ["mice", "bion", "mission"]
- `search_text`: Busca en título, texto y tags
- `pmc_id`: ID de PubMed Central
- `source_type`: "article", etc

### ✅ GET /api/front/documents/{pk}
```bash
curl "http://localhost:8000/api/front/documents/mice-in-bion-m-1-space-mission-training-and-selection"
```
**Retorna:** Documento completo con todos sus chunks

### ✅ GET /api/front/filters
```bash
curl "http://localhost:8000/api/front/filters"
```
**Retorna:**
```json
{
  "categories": ["space"],
  "tags": ["biomedical", "bion", "mice", "mission", "space"],
  "source_types": ["article"],
  "total_documents": 1,
  "total_chunks": 55
}
```

### ✅ GET /api/front/stats
```bash
curl "http://localhost:8000/api/front/stats"
```
**Retorna estadísticas de la base de datos**

---

## 🧪 Testing Rápido

### 1. **Verificar que el servidor está corriendo:**
```bash
curl http://localhost:8000/diag/health
```

### 2. **Ver estadísticas:**
```bash
curl http://localhost:8000/api/front/stats
```
**Esperas ver:**
```json
{
  "total_documents": 1,
  "total_chunks": 55,
  "categories_count": 1,
  "tags_count": 12,
  "source_types": ["article"],
  "categories": ["space"]
}
```

### 3. **Ver filtros disponibles:**
```bash
curl http://localhost:8000/api/front/filters
```

### 4. **Listar documentos:**
```bash
curl "http://localhost:8000/api/front/documents?skip=0&limit=10"
```

### 5. **Ver detalle de documento:**
```bash
# Usa el 'pk' del documento de tu ejemplo:
curl "http://localhost:8000/api/front/documents/mice-in-bion-m-1-space-mission-training-and-selection"
```

---

## ⚠️ Notas Importantes

### ✅ Lo que SÍ funciona ahora:
- Frontend API con tu estructura real
- Filtros por `category`, `tags`, `search_text`
- Búsqueda de texto en título, contenido y tags
- Obtener detalle de documento por `pk`
- Estadísticas y valores de filtros
- **Funciona en MongoDB local** (no requiere Atlas)

### ⚠️ Lo que AÚN requiere trabajo:
- **RAG Chatbot (`/api/chat`)**: Requiere MongoDB Atlas con Vector Search
  - Los campos `organism`, `mission_env`, etc. del RAG no existen en tu BD
  - Necesitarías adaptar también el RAG si quieres usarlo

---

## 📚 Documentación

- **`FRONTEND_API_REAL_STRUCTURE.md`**: Guía completa con ejemplos
- **`POSTMAN_TESTING_GUIDE.md`**: Guía de testing con Postman
- **Swagger UI**: http://localhost:8000/docs (documentación interactiva)

---

## 🎯 Próximos Pasos

### Opción 1: Probar Frontend API (lo creado ahora)
```bash
# Ver swagger:
# http://localhost:8000/docs

# Probar endpoints:
curl http://localhost:8000/api/front/stats
curl http://localhost:8000/api/front/filters
curl http://localhost:8000/api/front/documents
```

### Opción 2: Actualizar Postman Collection
Necesitaríamos actualizar `NASA_RAG.postman_collection.json` para reflejar los nuevos schemas (cambiar `source_id` → `pk`, etc.)

### Opción 3: Adaptar RAG Chatbot
Si quieres usar el RAG Chatbot (`/api/chat`), necesitamos:
1. Adaptar `chat.py` para usar `pk`, `tags`, `category`
2. Configurar MongoDB Atlas (local no soporta Vector Search)
3. Actualizar filtros del RAG

---

## 📊 Estado del Proyecto

| Componente | Estado | Funciona Local | Requiere Atlas |
|------------|--------|----------------|----------------|
| Frontend API | ✅ Actualizado | ✅ Sí | ❌ No |
| Diagnóstico (`/diag/*`) | ✅ OK | ✅ Sí | ❌ No |
| RAG Chatbot (`/api/chat`) | ⚠️ Requiere adaptación | ❌ No | ✅ Sí |
| Schemas | ✅ Actualizados | - | - |
| Repositorio | ✅ Actualizado | ✅ Sí | ❌ No |

---

¿Qué quieres hacer ahora?

1. **Probar el Frontend API** con curl o Postman
2. **Actualizar la Postman collection** con los nuevos schemas
3. **Adaptar el RAG Chatbot** para usar tu estructura
4. **Otra cosa**

Let me know! 🚀
