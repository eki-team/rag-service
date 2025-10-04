# 📮 Guía de Testing con Postman

Guía completa para probar todos los endpoints del servicio NASA RAG con Postman.

---

## 🚀 Quick Start

### 1. Importar la Colección

1. Abre Postman
2. Click en **Import** (esquina superior izquierda)
3. Arrastra el archivo `NASA_RAG.postman_collection.json` o usa "Upload Files"
4. La colección aparecerá en el sidebar izquierdo

### 2. Verificar Variable de Entorno

La colección usa la variable `{{base_url}}` configurada como `http://localhost:8000`.

Si necesitas cambiarla:
- Click derecho en la colección → **Edit**
- Tab **Variables**
- Cambia el valor de `base_url`

### 3. Iniciar el Servidor

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📋 Endpoints Disponibles

La colección incluye **16 requests** organizados en 3 categorías:

### 🤖 **RAG Chatbot (6 endpoints)**

Endpoints para el chatbot con búsqueda vectorial y síntesis con IA.

#### 1. **Chat - Simple Query**
```json
POST /api/chat
{
  "query": "What are the effects of microgravity on mice?"
}
```
Query simple sin filtros. Ideal para pruebas rápidas.

#### 2. **Chat - Con Filtros (Organism)**
```json
POST /api/chat
{
  "query": "How does spaceflight affect immune response?",
  "filters": {
    "organism": ["Mus musculus"]
  },
  "top_k": 8
}
```
Query con filtro por organismo.

#### 3. **Chat - Múltiples Filtros**
```json
POST /api/chat
{
  "query": "Effects of radiation on plant growth",
  "filters": {
    "organism": ["Arabidopsis thaliana"],
    "mission_env": ["ISS", "LEO"],
    "exposure": ["radiation", "microgravity"],
    "system": ["plant"]
  },
  "top_k": 10
}
```
Query con múltiples filtros combinados.

#### 4. **Chat - Year Range**
```json
POST /api/chat
{
  "query": "Recent studies on spaceflight effects",
  "filters": {
    "year_range": [2020, 2024]
  }
}
```
Query filtrando por rango de años.

#### 5. **Chat - Radiation Studies**
```json
POST /api/chat
{
  "query": "What are the biological effects of space radiation?",
  "filters": {
    "exposure": ["radiation"]
  },
  "top_k": 10
}
```
Query específica sobre radiación.

#### 6. **Chat - Plant Biology**
```json
POST /api/chat
{
  "query": "How do plants adapt to microgravity?",
  "filters": {
    "system": ["plant"]
  }
}
```
Query específica sobre biología de plantas.

---

### 🔧 **Diagnóstico (3 endpoints)**

Endpoints para debugging y health checks.

#### 7. **Health Check**
```
GET /diag/health
```
Verifica el estado del servicio. Debe retornar `status: "healthy"`.

#### 8. **Test Embedding**
```json
POST /diag/emb
{
  "text": "microgravity effects on immune system"
}
```
Genera embedding de un texto (debug). Retorna vector de 384 dimensiones.

#### 9. **Test Retrieval (sin LLM)**
```json
POST /diag/retrieval
{
  "query": "What are the effects of microgravity?",
  "top_k": 5
}
```
Test de retrieval sin síntesis LLM. Retorna chunks recuperados directamente.

---

### 📦 **Frontend API (7 endpoints)**

Endpoints para operaciones CRUD y búsquedas sin IA (no requiere Atlas Vector Search).

#### 10. **Frontend - List Documents**
```
GET /api/front/documents?skip=0&limit=20
```
Lista todos los documentos únicos con paginación.

**Query Parameters:**
- `skip`: Documentos a saltar (default: 0)
- `limit`: Documentos por página (default: 20, max: 100)

#### 11. **Frontend - Search Documents**
```json
POST /api/front/documents/search?skip=0&limit=20
{
  "organism": ["Mus musculus"],
  "mission_env": ["ISS"],
  "year_min": 2020,
  "year_max": 2024,
  "search_text": "immune"
}
```
Búsqueda con filtros facetados. Todos los filtros son opcionales.

**Filtros disponibles:**
- `organism`: Array de organismos
- `mission_env`: Array de entornos de misión
- `exposure`: Array de tipos de exposición
- `system`: Array de sistemas biológicos
- `tissue`: Array de tejidos
- `assay`: Array de tipos de ensayo
- `year_min`, `year_max`: Rango de años
- `search_text`: Búsqueda de texto en título/contenido

#### 12. **Frontend - Search (Solo Organism)**
```json
POST /api/front/documents/search?skip=0&limit=20
{
  "organism": ["Mus musculus"]
}
```
Ejemplo: búsqueda solo por organismo.

#### 13. **Frontend - Search (Text Only)**
```json
POST /api/front/documents/search
{
  "search_text": "microgravity"
}
```
Ejemplo: búsqueda solo por texto.

#### 14. **Frontend - Get Document Detail**
```
GET /api/front/documents/GLDS-123
```
Obtener detalle completo de un documento con todos sus chunks.

⚠️ **Nota:** Cambia `GLDS-123` por un `source_id` real de tu base de datos.

#### 15. **Frontend - Get Filter Values**
```
GET /api/front/filters
```
Obtener todos los valores únicos para cada filtro. Útil para poblar dropdowns en el frontend.

**Respuesta:**
```json
{
  "organisms": ["Mus musculus", "Homo sapiens", ...],
  "mission_envs": ["ISS", "LEO", ...],
  "exposures": ["microgravity", "radiation", ...],
  "systems": ["immune", "musculoskeletal", ...],
  "tissues": ["muscle", "bone", ...],
  "assays": ["RNA-seq", "proteomics", ...],
  "years": [2024, 2023, 2022, ...]
}
```

#### 16. **Frontend - Get Statistics**
```
GET /api/front/stats
```
Obtener estadísticas generales de la base de datos.

**Respuesta:**
```json
{
  "total_documents": 150,
  "total_chunks": 3500,
  "organisms_count": 25,
  "mission_envs_count": 8,
  "years_range": [2015, 2024]
}
```

---

## 🎯 Flujo de Testing Recomendado

### **Primer Test - Verificación Básica**

1. **Health Check** → Verificar que el servidor esté corriendo
2. **Frontend - Get Filter Values** → Ver qué datos hay disponibles
3. **Frontend - Get Statistics** → Ver cuántos documentos existen
4. **Frontend - List Documents** → Ver primeros 20 documentos

### **Test de Búsqueda Frontend**

1. **Frontend - Search (Text Only)** → Búsqueda simple por texto
2. **Frontend - Search (Solo Organism)** → Filtrar por organismo
3. **Frontend - Search Documents** → Búsqueda con múltiples filtros
4. **Frontend - Get Document Detail** → Ver detalle de un documento específico

### **Test de RAG Chatbot**

⚠️ **Nota:** Estos endpoints requieren MongoDB Atlas con Vector Search.

1. **Chat - Simple Query** → Query básica
2. **Chat - Con Filtros (Organism)** → Query con filtro
3. **Chat - Múltiples Filtros** → Query compleja
4. **Test Retrieval (sin LLM)** → Verificar retrieval sin síntesis

---

## 📊 Comparación: Frontend API vs RAG Chatbot

| Característica | Frontend API | RAG Chatbot |
|----------------|--------------|-------------|
| **Propósito** | CRUD, listado, filtrado | Conversación con IA |
| **Búsqueda** | Filtros tradicionales + texto | Búsqueda semántica vectorial |
| **Respuesta** | Documentos/chunks crudos | Respuesta generada por GPT |
| **Requiere LLM** | ❌ No | ✅ Sí (GPT-4o-mini) |
| **Requiere Atlas** | ❌ No (MongoDB local OK) | ✅ Sí (Vector Search) |
| **Uso típico** | Listar, filtrar, explorar | Preguntas en lenguaje natural |
| **Endpoints** | `/api/front/*` | `/api/chat` |

---

## ⚠️ Errores Comunes

### 1. **Connection Refused (ECONNREFUSED)**
```json
{
  "error": "connect ECONNREFUSED 127.0.0.1:8000"
}
```
**Solución:** El servidor no está corriendo. Ejecuta:
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. **500 Internal Server Error**
```json
{
  "detail": "..."
}
```
**Posibles causas:**
- MongoDB no está conectado
- Falta configuración en `.env`
- Error en los datos de entrada

**Solución:** Revisa los logs del servidor en la terminal.

### 3. **Empty Citations (RAG Chatbot)**
```json
{
  "answer": "I don't have enough information...",
  "citations": []
}
```
**Causas:**
- No hay datos en la base de datos
- Los filtros son muy restrictivos
- MongoDB Atlas Vector Search no está configurado

**Solución:**
- Verifica que haya datos: `GET /api/front/stats`
- Usa filtros menos restrictivos
- Para RAG, configura MongoDB Atlas

### 4. **404 Not Found - Document Detail**
```json
{
  "detail": "Document GLDS-123 not found"
}
```
**Causa:** El `source_id` no existe en la base de datos.

**Solución:**
1. Obtén un `source_id` real: `GET /api/front/documents`
2. Usa ese `source_id` en el endpoint de detalle

---

## 🔐 Autenticación

Actualmente los endpoints no requieren autenticación. Si necesitas añadir autenticación:

1. Configura un token en la colección:
   - Collection → Edit → Variables
   - Añade variable: `auth_token`

2. Añade header en los requests:
   ```
   Authorization: Bearer {{auth_token}}
   ```

---

## 📈 Performance Tips

### Para el Frontend API:

1. **Paginación**: Usa `limit` razonable (20-50 documentos)
2. **Filtros**: Combina filtros para reducir resultados
3. **Caché**: Los filter values cambian poco, cachéalos en el frontend

### Para el RAG Chatbot:

1. **top_k**: Usa 5-10 para mejor balance velocidad/calidad
2. **Filtros**: Reduce el espacio de búsqueda con filtros específicos
3. **Queries cortas**: Queries más específicas dan mejores resultados

---

## 🆘 Troubleshooting

### Problema: "No chunks retrieved from vector search"

**En RAG Chatbot:**
- Verifica que uses MongoDB Atlas (no local)
- Verifica que el índice vectorial esté creado
- Configura `MONGODB_VECTOR_INDEX` en `.env`

**En Frontend API:**
- No debería pasar (no usa vector search)
- Si aparece, revisa que haya datos en MongoDB

### Problema: Respuestas lentas

**Causas:**
- Primera query descarga el modelo de embeddings (~6 segundos)
- LLM synthesis toma tiempo
- Base de datos lenta

**Soluciones:**
- Primera query siempre es lenta (caché del modelo)
- Reduce `top_k` para menos chunks
- Añade índices en MongoDB para campos filtrados

---

## 📚 Recursos Adicionales

- **Swagger UI**: http://localhost:8000/docs (documentación interactiva)
- **ReDoc**: http://localhost:8000/redoc (documentación alternativa)
- **Frontend API Guide**: Ver `FRONTEND_API_GUIDE.md`
- **Logs del servidor**: Revisa la terminal donde corre uvicorn

---

## 🎓 Ejemplos de Uso en Código

### JavaScript/Fetch

```javascript
// Frontend API - List documents
async function getDocuments(page = 1, pageSize = 20) {
  const skip = (page - 1) * pageSize;
  const response = await fetch(
    `http://localhost:8000/api/front/documents?skip=${skip}&limit=${pageSize}`
  );
  return await response.json();
}

// Frontend API - Search with filters
async function searchDocuments(filters) {
  const response = await fetch(
    'http://localhost:8000/api/front/documents/search',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters)
    }
  );
  return await response.json();
}

// RAG Chatbot
async function chatWithRAG(query, filters = {}) {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, filters, top_k: 8 })
  });
  return await response.json();
}
```

### Python/Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Frontend API - List documents
def get_documents(skip=0, limit=20):
    response = requests.get(
        f"{BASE_URL}/api/front/documents",
        params={"skip": skip, "limit": limit}
    )
    return response.json()

# Frontend API - Search with filters
def search_documents(filters, skip=0, limit=20):
    response = requests.post(
        f"{BASE_URL}/api/front/documents/search",
        params={"skip": skip, "limit": limit},
        json=filters
    )
    return response.json()

# RAG Chatbot
def chat_with_rag(query, filters=None, top_k=8):
    payload = {"query": query, "top_k": top_k}
    if filters:
        payload["filters"] = filters
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload
    )
    return response.json()
```

---

¡Happy Testing! 🚀
