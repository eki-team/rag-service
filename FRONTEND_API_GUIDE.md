# 📦 Frontend API - Guía de Endpoints

Endpoints para operaciones del frontend independientes del chatbot RAG.

Base URL: `http://localhost:8000/api/front`

---

## 📋 Endpoints Disponibles

### 1. **GET /api/front/documents** - Listar Documentos

Lista todos los documentos únicos (papers) con paginación.

**Query Parameters:**
- `skip` (int, default=0): Documentos a saltar
- `limit` (int, default=20, max=100): Documentos por página

**Ejemplo:**
```bash
curl http://localhost:8000/api/front/documents?skip=0&limit=20
```

**Respuesta:**
```json
{
  "total": 150,
  "documents": [
    {
      "source_id": "GLDS-123_chunk_1",
      "title": "Effects of microgravity on immune response in mice",
      "year": 2023,
      "doi": "10.1038/s41586-023-12345",
      "osdr_id": "GLDS-123",
      "organism": "Mus musculus",
      "mission_env": "ISS",
      "exposure": "microgravity",
      "system": "immune",
      "tissue": "spleen",
      "assay": "RNA-seq"
    }
  ]
}
```

---

### 2. **POST /api/front/documents/search** - Buscar con Filtros

Buscar documentos aplicando filtros facetados y/o búsqueda de texto.

**Query Parameters:**
- `skip` (int, default=0)
- `limit` (int, default=20, max=100)

**Body:**
```json
{
  "organism": ["Mus musculus", "Homo sapiens"],
  "mission_env": ["ISS", "LEO"],
  "exposure": ["microgravity"],
  "system": ["immune", "musculoskeletal"],
  "tissue": ["muscle", "bone"],
  "assay": ["RNA-seq", "proteomics"],
  "year_min": 2020,
  "year_max": 2024,
  "search_text": "immune response"
}
```

**Nota:** Todos los campos son opcionales. Puedes enviar solo los filtros que necesites.

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/front/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "organism": ["Mus musculus"],
    "year_min": 2020,
    "search_text": "immune"
  }'
```

**Respuesta:** Igual que GET /documents

---

### 3. **GET /api/front/documents/{source_id}** - Detalle de Documento

Obtener todos los chunks (fragmentos) de un documento específico.

**Path Parameter:**
- `source_id` (string): ID del documento (ej: "GLDS-123")

**Ejemplo:**
```bash
curl http://localhost:8000/api/front/documents/GLDS-123
```

**Respuesta:**
```json
{
  "metadata": {
    "source_id": "GLDS-123_chunk_1",
    "title": "Effects of microgravity...",
    "year": 2023,
    "doi": "10.1038/...",
    "organism": "Mus musculus",
    "mission_env": "ISS",
    ...
  },
  "chunks": [
    {
      "source_id": "GLDS-123_chunk_1",
      "pk": "nasa",
      "title": "Effects of microgravity...",
      "section": "Introduction",
      "text": "Space exploration presents unique challenges...",
      "chunk_index": 1,
      ...
    },
    {
      "source_id": "GLDS-123_chunk_2",
      "section": "Methods",
      "text": "Mice were housed in the ISS...",
      "chunk_index": 2,
      ...
    }
  ],
  "total_chunks": 25
}
```

---

### 4. **GET /api/front/filters** - Valores de Filtros

Obtener todos los valores únicos disponibles para cada filtro.
Útil para poblar dropdowns/selects en el frontend.

**Ejemplo:**
```bash
curl http://localhost:8000/api/front/filters
```

**Respuesta:**
```json
{
  "organisms": [
    "Mus musculus",
    "Homo sapiens",
    "Arabidopsis thaliana",
    "Caenorhabditis elegans",
    "Drosophila melanogaster"
  ],
  "mission_envs": [
    "ISS",
    "LEO",
    "Ground",
    "Lunar",
    "Mars analog"
  ],
  "exposures": [
    "microgravity",
    "radiation",
    "spaceflight",
    "simulated microgravity"
  ],
  "systems": [
    "immune",
    "musculoskeletal",
    "cardiovascular",
    "nervous",
    "reproductive"
  ],
  "tissues": [
    "muscle",
    "bone",
    "liver",
    "spleen",
    "brain",
    "heart"
  ],
  "assays": [
    "RNA-seq",
    "proteomics",
    "metabolomics",
    "microarray",
    "Western blot"
  ],
  "years": [
    2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015
  ]
}
```

---

### 5. **GET /api/front/stats** - Estadísticas

Obtener estadísticas generales de la base de datos.

**Ejemplo:**
```bash
curl http://localhost:8000/api/front/stats
```

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

## 🎯 Casos de Uso Comunes

### Caso 1: Cargar página inicial con lista de documentos

```javascript
// JavaScript/React ejemplo
async function loadDocuments(page = 1, pageSize = 20) {
  const skip = (page - 1) * pageSize;
  const response = await fetch(
    `http://localhost:8000/api/front/documents?skip=${skip}&limit=${pageSize}`
  );
  const data = await response.json();
  return data; // { total, documents }
}
```

### Caso 2: Poblar filtros en UI

```javascript
async function loadFilters() {
  const response = await fetch('http://localhost:8000/api/front/filters');
  const filters = await response.json();
  
  // Poblar dropdowns
  populateDropdown('organism-select', filters.organisms);
  populateDropdown('mission-select', filters.mission_envs);
  populateDropdown('exposure-select', filters.exposures);
  // etc...
}
```

### Caso 3: Búsqueda con múltiples filtros

```javascript
async function searchDocuments(filters, page = 1) {
  const response = await fetch(
    `http://localhost:8000/api/front/documents/search?skip=${(page-1)*20}&limit=20`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        organism: filters.selectedOrganisms,
        mission_env: filters.selectedMissions,
        year_min: filters.yearFrom,
        year_max: filters.yearTo,
        search_text: filters.searchQuery
      })
    }
  );
  return await response.json();
}
```

### Caso 4: Ver detalle completo de un paper

```javascript
async function viewDocumentDetail(sourceId) {
  const response = await fetch(
    `http://localhost:8000/api/front/documents/${sourceId}`
  );
  const doc = await response.json();
  
  // Mostrar metadata
  console.log('Title:', doc.metadata.title);
  console.log('Year:', doc.metadata.year);
  
  // Mostrar chunks por sección
  doc.chunks.forEach(chunk => {
    console.log(`[${chunk.section}] ${chunk.text}`);
  });
}
```

---

## 📊 Diferencias con /api/chat (RAG)

| Feature | `/api/front/*` | `/api/chat` |
|---------|----------------|-------------|
| **Propósito** | Operaciones CRUD, listado, filtrado | Chatbot RAG con IA |
| **Búsqueda** | Filtros tradicionales + texto | Búsqueda semántica vectorial |
| **Respuesta** | Documentos/chunks crudos | Respuesta generada por GPT |
| **Uso** | Frontend UI, exploración | Conversación con usuario |
| **Requiere LLM** | ❌ No | ✅ Sí (GPT-4o-mini) |
| **Requiere Atlas** | ❌ No (funciona en MongoDB local) | ✅ Sí (vector search) |

---

## 🧪 Testing con Postman

### Collection para Frontend API

Puedes importar esta collection en Postman:

```json
{
  "info": {
    "name": "NASA RAG - Frontend API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "List Documents",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/api/front/documents?skip=0&limit=20",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "front", "documents"],
          "query": [
            {"key": "skip", "value": "0"},
            {"key": "limit", "value": "20"}
          ]
        }
      }
    },
    {
      "name": "Search Documents",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"organism\": [\"Mus musculus\"],\n  \"year_min\": 2020\n}"
        },
        "url": {
          "raw": "http://localhost:8000/api/front/documents/search?skip=0&limit=20",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "front", "documents", "search"]
        }
      }
    },
    {
      "name": "Get Document Detail",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:8000/api/front/documents/GLDS-123"
      }
    },
    {
      "name": "Get Filter Values",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:8000/api/front/filters"
      }
    },
    {
      "name": "Get Statistics",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:8000/api/front/stats"
      }
    }
  ]
}
```

---

## 🔧 Troubleshooting

### Error: "Document not found"
- Verifica que el `source_id` sea correcto
- El ID debe coincidir con el prefijo de los chunks (ej: "GLDS-123")

### Error: "Connection refused"
- Verifica que el servidor esté corriendo en puerto 8000
- Verifica que MongoDB esté conectado

### Respuesta vacía en búsqueda
- Verifica que los filtros no sean demasiado restrictivos
- Prueba sin filtros primero
- Verifica que haya datos en la base de datos

### Performance lento
- Considera añadir índices en MongoDB para campos filtrados
- Reduce el `limit` si es muy alto
- Para búsqueda de texto, considera usar índices de texto de MongoDB

---

## 📚 Ver También

- **Swagger UI**: http://localhost:8000/docs (documentación interactiva)
- **ReDoc**: http://localhost:8000/redoc (documentación alternativa)
- **Chat RAG**: Ver `POSTMAN_GUIDE.md` para endpoints del chatbot
