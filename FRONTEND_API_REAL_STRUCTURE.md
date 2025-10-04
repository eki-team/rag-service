# 📦 Frontend API - Guía Completa (Estructura Real)

API REST para frontend con operaciones CRUD sobre la base de datos MongoDB.
**Totalmente independiente del chatbot RAG** - no requiere búsqueda vectorial ni OpenAI.

---

## 🏗️ Estructura de Documentos en MongoDB

### Ejemplo de documento (chunk) en la colección:

```json
{
  "pk": "mice-in-bion-m-1-space-mission-training-and-selection",
  "text": "Title: Mice in Bion-M 1 Space Mission: Training and Selection...",
  "source_type": "article",
  "source_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/",
  "metadata": {
    "article_metadata": {
      "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/",
      "title": "Mice in Bion-M 1 Space Mission: Training and Selection",
      "authors": ["Alexander Andreev-Andrievskiy", "..."],
      "scraped_at": "2025-10-04T11:30:44.123766",
      "pmc_id": "4136787",
      "doi": "https://doi.org/10.1371/journal.pone.0104830",
      "statistics": {
        "total_authors": 19,
        "abstract_words": 295,
        "total_words": 9146
      }
    },
    "char_count": 1464,
    "word_count": 194,
    "sentences_count": 4,
    "tags": ["biomedical", "bion", "mice", "mission", "space"],
    "category": "space"
  },
  "chunk_index": 0,
  "total_chunks": 55,
  "created_at": {"$date": "2025-10-04T15:56:12.543Z"},
  "updated_at": {"$date": "2025-10-04T15:56:12.543Z"}
}
```

**Campos principales:**
- `pk`: ID único del documento (slug del título)
- `text`: Contenido del chunk
- `source_type`: Tipo de fuente ("article", etc)
- `source_url`: URL del artículo original
- `metadata.article_metadata`: Metadatos del artículo (título, autores, DOI, PMC ID, etc)
- `metadata.tags`: Array de tags descriptivos
- `metadata.category`: Categoría principal ("space", "biology", etc)
- `chunk_index`: Índice del chunk (0-based)
- `total_chunks`: Total de chunks del documento

---

## 📋 Endpoints Disponibles

### 1. **GET /api/front/documents** - Listar documentos

Lista todos los documentos únicos con paginación.

**Query Parameters:**
- `skip` (int, default=0): Documentos a saltar
- `limit` (int, default=20, max=100): Documentos por página

**Ejemplo:**
```bash
curl "http://localhost:8000/api/front/documents?skip=0&limit=20"
```

**Respuesta:**
```json
{
  "total": 1,
  "documents": [
    {
      "pk": "mice-in-bion-m-1-space-mission-training-and-selection",
      "title": "Mice in Bion-M 1 Space Mission: Training and Selection",
      "source_type": "article",
      "source_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/",
      "category": "space",
      "tags": ["biomedical", "bion", "mice", "mission", "space"],
      "total_chunks": 55,
      "article_metadata": {
        "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/",
        "title": "Mice in Bion-M 1 Space Mission: Training and Selection",
        "authors": ["Alexander Andreev-Andrievskiy", "..."],
        "pmc_id": "4136787",
        "doi": "https://doi.org/10.1371/journal.pone.0104830"
      }
    }
  ]
}
```

---

### 2. **POST /api/front/documents/search** - Buscar con filtros

Buscar documentos con filtros facetados y/o texto.

**Query Parameters:**
- `skip` (int, default=0)
- `limit` (int, default=20, max=100)

**Body (JSON):**
```json
{
  "category": "space",
  "tags": ["mice", "mission"],
  "search_text": "microgravity",
  "source_type": "article",
  "pmc_id": "4136787"
}
```

**Todos los filtros son opcionales:**
- `category` (string): Filtrar por categoría
- `tags` (array): Filtrar por tags (busca documentos que tengan al menos uno)
- `search_text` (string): Búsqueda de texto en título, contenido y tags
- `source_type` (string): Filtrar por tipo de fuente
- `pmc_id` (string): Filtrar por ID de PubMed Central

**Ejemplos:**

```bash
# Buscar por categoría
curl -X POST "http://localhost:8000/api/front/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"category": "space"}'

# Buscar por tags
curl -X POST "http://localhost:8000/api/front/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["mice", "bion"]}'

# Búsqueda de texto
curl -X POST "http://localhost:8000/api/front/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"search_text": "microgravity"}'

# Combinación de filtros
curl -X POST "http://localhost:8000/api/front/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "space",
    "tags": ["mice"],
    "search_text": "training"
  }'
```

---

### 3. **GET /api/front/documents/{pk}** - Detalle de documento

Obtener todos los chunks de un documento específico.

**Path Parameter:**
- `pk` (string): ID del documento (campo `pk` en MongoDB)

**Ejemplo:**
```bash
curl "http://localhost:8000/api/front/documents/mice-in-bion-m-1-space-mission-training-and-selection"
```

**Respuesta:**
```json
{
  "metadata": {
    "pk": "mice-in-bion-m-1-space-mission-training-and-selection",
    "title": "Mice in Bion-M 1 Space Mission: Training and Selection",
    "source_type": "article",
    "source_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/",
    "category": "space",
    "tags": ["biomedical", "bion", "mice", "mission", "space"],
    "total_chunks": 55,
    "article_metadata": {...}
  },
  "chunks": [
    {
      "pk": "mice-in-bion-m-1-space-mission-training-and-selection",
      "text": "Title: Mice in Bion-M 1 Space Mission...",
      "source_type": "article",
      "source_url": "https://...",
      "category": "space",
      "tags": ["biomedical", "bion", "mice"],
      "chunk_index": 0,
      "total_chunks": 55,
      "char_count": 1464,
      "word_count": 194,
      "sentences_count": 4,
      "article_metadata": {...}
    },
    {
      "chunk_index": 1,
      "text": "...",
      ...
    }
  ],
  "total_chunks": 55
}
```

---

### 4. **GET /api/front/filters** - Valores disponibles para filtros

Obtener todos los valores únicos de cada filtro. Útil para poblar dropdowns.

**Ejemplo:**
```bash
curl "http://localhost:8000/api/front/filters"
```

**Respuesta:**
```json
{
  "categories": ["space", "biology"],
  "tags": [
    "biomedical", "bion", "bion-m", "mice", "mission",
    "physics", "planets", "program", "science", "space",
    "technology", "training"
  ],
  "source_types": ["article"],
  "total_documents": 1,
  "total_chunks": 55
}
```

**Uso típico:**
- `categories`: Para dropdown de categorías
- `tags`: Para tag selector / autocomplete (top 50 tags)
- `source_types`: Para filtro de tipo de fuente
- `total_documents` / `total_chunks`: Para mostrar estadísticas

---

### 5. **GET /api/front/stats** - Estadísticas generales

Obtener estadísticas de la base de datos.

**Ejemplo:**
```bash
curl "http://localhost:8000/api/front/stats"
```

**Respuesta:**
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

---

## 🎯 Casos de Uso en Frontend

### Caso 1: Pantalla de inicio con estadísticas

```javascript
async function loadDashboard() {
  // Obtener estadísticas
  const stats = await fetch('http://localhost:8000/api/front/stats').then(r => r.json());
  
  // Mostrar en dashboard
  document.getElementById('total-docs').innerText = stats.total_documents;
  document.getElementById('total-chunks').innerText = stats.total_chunks;
  document.getElementById('categories').innerText = stats.categories.join(', ');
}
```

---

### Caso 2: Lista de documentos con paginación

```javascript
async function loadDocuments(page = 1, pageSize = 20) {
  const skip = (page - 1) * pageSize;
  const response = await fetch(
    `http://localhost:8000/api/front/documents?skip=${skip}&limit=${pageSize}`
  );
  const data = await response.json();
  
  // Renderizar documentos
  data.documents.forEach(doc => {
    console.log(`${doc.title} (${doc.total_chunks} chunks)`);
  });
  
  // Paginación
  const totalPages = Math.ceil(data.total / pageSize);
  console.log(`Página ${page} de ${totalPages}`);
}
```

---

### Caso 3: Filtros dinámicos

```javascript
async function setupFilters() {
  // Obtener valores de filtros
  const filters = await fetch('http://localhost:8000/api/front/filters').then(r => r.json());
  
  // Poblar dropdown de categorías
  const categorySelect = document.getElementById('category-select');
  filters.categories.forEach(category => {
    const option = document.createElement('option');
    option.value = category;
    option.text = category;
    categorySelect.appendChild(option);
  });
  
  // Poblar tag selector
  const tagContainer = document.getElementById('tags');
  filters.tags.forEach(tag => {
    const tagEl = document.createElement('span');
    tagEl.className = 'tag';
    tagEl.textContent = tag;
    tagEl.onclick = () => filterByTag(tag);
    tagContainer.appendChild(tagEl);
  });
}
```

---

### Caso 4: Búsqueda con múltiples filtros

```javascript
async function searchDocuments(searchFilters) {
  const response = await fetch(
    'http://localhost:8000/api/front/documents/search?skip=0&limit=20',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(searchFilters)
    }
  );
  
  const data = await response.json();
  return data.documents;
}

// Ejemplo de uso:
const results = await searchDocuments({
  category: 'space',
  tags: ['mice', 'mission'],
  search_text: 'microgravity'
});
```

---

### Caso 5: Ver detalle de documento

```javascript
async function viewDocument(pk) {
  const response = await fetch(`http://localhost:8000/api/front/documents/${pk}`);
  const doc = await response.json();
  
  // Mostrar metadata
  console.log(`Título: ${doc.metadata.title}`);
  console.log(`Categoría: ${doc.metadata.category}`);
  console.log(`Tags: ${doc.metadata.tags.join(', ')}`);
  console.log(`Total chunks: ${doc.total_chunks}`);
  
  // Renderizar chunks
  doc.chunks.forEach((chunk, i) => {
    console.log(`\nChunk ${i + 1}/${doc.total_chunks}:`);
    console.log(chunk.text.substring(0, 200) + '...');
  });
}

// Ejemplo de uso:
await viewDocument('mice-in-bion-m-1-space-mission-training-and-selection');
```

---

## 📊 Comparación: Frontend API vs RAG Chatbot

| Característica | Frontend API (`/api/front/*`) | RAG Chatbot (`/api/chat`) |
|----------------|-------------------------------|---------------------------|
| **Propósito** | CRUD, listado, filtrado | Conversación con IA |
| **Búsqueda** | Filtros tradicionales + regex | Búsqueda vectorial semántica |
| **Respuesta** | Documentos/chunks crudos | Respuesta sintetizada por GPT |
| **Requiere LLM** | ❌ No | ✅ Sí (GPT-4o-mini) |
| **Requiere Vector Search** | ❌ No | ✅ Sí (MongoDB Atlas) |
| **Funciona local** | ✅ Sí (MongoDB local OK) | ❌ No (requiere Atlas) |
| **Uso típico** | Listar, filtrar, explorar | Preguntas en lenguaje natural |
| **Costo** | Gratis | Cuesta tokens de OpenAI |

---

## ⚡ Performance Tips

### Paginación eficiente:
```javascript
// Usar limit razonable (20-50)
const pageSize = 20;

// Implementar "Load More" en lugar de páginas numeradas
let currentSkip = 0;
async function loadMore() {
  const docs = await loadDocuments(currentSkip, pageSize);
  currentSkip += pageSize;
  appendToList(docs);
}
```

### Caché de filtros:
```javascript
// Los filtros cambian poco, cachéalos
let cachedFilters = null;
async function getFilters() {
  if (!cachedFilters) {
    cachedFilters = await fetch('/api/front/filters').then(r => r.json());
  }
  return cachedFilters;
}
```

### Búsqueda debounced:
```javascript
// Evita llamadas en cada tecla
const debounce = (func, delay) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), delay);
  };
};

const searchInput = document.getElementById('search');
searchInput.addEventListener('input', debounce(async (e) => {
  const results = await searchDocuments({ search_text: e.target.value });
  renderResults(results);
}, 300));
```

---

## 🐛 Troubleshooting

### Problema: "Empty documents array"
```json
{
  "total": 0,
  "documents": []
}
```

**Causa:** No hay datos en la base de datos o los filtros son muy restrictivos.

**Solución:**
1. Verifica que haya datos: `GET /api/front/stats`
2. Si `total_documents: 0`, necesitas cargar datos a MongoDB
3. Si hay datos pero la búsqueda no devuelve nada, revisa los filtros

---

### Problema: "404 Not Found" en documento específico
```json
{
  "detail": "Document mice-... not found"
}
```

**Causa:** El `pk` no existe o es incorrecto.

**Solución:**
1. Lista documentos primero: `GET /api/front/documents`
2. Copia el valor exacto de `pk` de la respuesta
3. Úsalo en `GET /api/front/documents/{pk}`

---

### Problema: Búsqueda de texto no funciona

**Causa:** El regex es case-sensitive o el texto no coincide.

**Solución:**
- La búsqueda es **case-insensitive**
- Busca palabras completas o parciales: `"micro"` encuentra `"microgravity"`
- Prueba con términos más genéricos

---

## 🔐 Seguridad (Producción)

Para producción, añade autenticación:

```python
# En app/api/routers/front.py
from fastapi import Depends, HTTPException, Header

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.replace("Bearer ", "")
    # Verificar token aquí
    return token

# Añade a cada endpoint:
@router.get("/documents", dependencies=[Depends(verify_token)])
async def list_documents(...):
    ...
```

---

## 📚 Schemas de Respuesta (TypeScript)

```typescript
interface ArticleMetadata {
  url?: string;
  title: string;
  authors: string[];
  scraped_at?: string;
  pmc_id?: string;
  doi?: string;
  statistics?: {
    total_authors: number;
    abstract_words: number;
    total_words: number;
  };
}

interface DocumentMetadata {
  pk: string;
  title: string;
  source_type?: string;
  source_url?: string;
  category?: string;
  tags: string[];
  total_chunks: number;
  article_metadata?: ArticleMetadata;
}

interface DocumentChunk {
  pk: string;
  text: string;
  source_type?: string;
  source_url?: string;
  category?: string;
  tags: string[];
  chunk_index: number;
  total_chunks: number;
  char_count?: number;
  word_count?: number;
  sentences_count?: number;
  article_metadata?: ArticleMetadata;
}

interface DocumentListResponse {
  total: number;
  documents: DocumentMetadata[];
}

interface SearchFilters {
  category?: string;
  tags?: string[];
  search_text?: string;
  pmc_id?: string;
  source_type?: string;
}

interface FilterValuesResponse {
  categories: string[];
  tags: string[];
  source_types: string[];
  total_documents: number;
  total_chunks: number;
}

interface DocumentDetailResponse {
  metadata: DocumentMetadata;
  chunks: DocumentChunk[];
  total_chunks: number;
}
```

---

¡Listo para usar! 🚀

Prueba primero con:
```bash
curl http://localhost:8000/api/front/stats
curl http://localhost:8000/api/front/filters
curl http://localhost:8000/api/front/documents
```
