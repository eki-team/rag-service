# ✅ Migración Completada: OpenAI Embeddings

## 🎯 Resumen de Cambios

Has migrado exitosamente de **sentence-transformers local** a **OpenAI embeddings** para la vectorización.

---

## 📦 Archivos Creados/Modificados

### ✅ Nuevos Archivos:

1. **`app/services/embeddings/openai_embeddings.py`**
   - Servicio de embeddings con OpenAI API
   - Modelo: `text-embedding-3-small`
   - Dimensiones: 1536

2. **`test_openai_embeddings.py`**
   - Script de prueba para verificar funcionamiento
   - Ejecutar: `python test_openai_embeddings.py`

3. **`re_index_with_openai.py`**
   - Script para re-indexar documentos existentes
   - Convierte embeddings 384D → 1536D
   - Ejecutar: `python re_index_with_openai.py`

4. **`MIGRACION_OPENAI_EMBEDDINGS.md`**
   - Guía completa de la migración
   - Instrucciones para actualizar índice MongoDB

### ✅ Archivos Modificados:

1. **`.env`**
   ```properties
   EMBEDDING_MODEL=text-embedding-3-small
   EMBEDDING_DIMENSIONS=1536
   EMBEDDING_BATCH_SIZE=100
   ```

2. **`requirements.txt`**
   - Añadido: `openai==1.57.4`
   - Añadido: `tqdm==4.67.1`

3. **`app/services/embeddings/__init__.py`**
   - Ahora exporta `OpenAIEmbeddings` por defecto
   - `get_embeddings_service()` retorna instancia de OpenAI

4. **`app/api/routers/diag.py`**
   - Endpoint `/diag/emb` usa OpenAI embeddings
   - Health check muestra "OpenAI" en lugar de "local"

---

## 🚀 Próximos Pasos

### 1. **Probar OpenAI Embeddings** ✅ (Recomendado primero)

```bash
python test_openai_embeddings.py
```

**Esperas ver:**
```
✅ All tests passed!
- Model: text-embedding-3-small
- Dimensions: 1536
- Single embedding: ✅
- Batch embeddings: ✅
- Similarity calculation: ✅
```

### 2. **Actualizar Índice Vectorial en MongoDB Atlas** ⚠️ (OBLIGATORIO)

Como cambiaste de 384 → 1536 dimensiones, **DEBES** recrear el índice:

#### Opción A: MongoDB Atlas UI

1. Ve a Atlas → Database → Collections
2. Selecciona `mydb.pub_chunks`
3. Tab "Search Indexes"
4. **ELIMINA** índice `vector_index` actual
5. Crea nuevo con:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    }
  ]
}
```

#### Opción B: MongoDB Shell

```javascript
use mydb;
db.pub_chunks.dropIndex("vector_index");
db.pub_chunks.createSearchIndex(
  "vector_index",
  "vectorSearch",
  {
    fields: [{
      type: "vector",
      path: "embedding",
      numDimensions: 1536,
      similarity: "cosine"
    }]
  }
);
```

### 3. **Re-indexar Documentos Existentes** ⚠️ (OBLIGATORIO si tienes datos)

Los embeddings actuales en MongoDB son de 384 dimensiones. Debes regenerarlos:

```bash
# Re-indexar todos los documentos
python re_index_with_openai.py

# O con opciones:
python re_index_with_openai.py --batch-size 50 --skip-existing
```

**Nota:** Esto costará tokens de OpenAI (~$0.02 por cada millón de tokens)

### 4. **Probar Endpoints de la API**

```bash
# Health check
curl http://localhost:8000/diag/health

# Test embedding
curl -X POST "http://localhost:8000/diag/emb" \
  -H "Content-Type: application/json" \
  -d '{"text": "microgravity effects on immune system"}'

# Test retrieval (requiere re-indexación)
curl -X POST "http://localhost:8000/diag/retrieval" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the effects of microgravity?", "top_k": 5}'
```

---

## 📊 Comparación: Antes vs Ahora

| Aspecto | Antes (Sentence-Transformers) | Ahora (OpenAI) |
|---------|------------------------------|----------------|
| **Modelo** | all-MiniLM-L6-v2 | text-embedding-3-small |
| **Dimensiones** | 384 | 1536 |
| **Calidad** | Buena | Excelente |
| **Velocidad** | Rápido (local) | Depende de API (~1s) |
| **Costo** | Gratis | $0.02 / 1M tokens |
| **Dependencias** | PyTorch (~2GB) | openai (~5MB) |
| **RAM** | ~500MB | Mínimo |
| **Multilingüe** | Bueno | Excelente |
| **Offline** | ✅ Funciona | ❌ Requiere internet |

---

## 💰 Estimación de Costos

### Para Re-indexar:
- **1 documento** = ~500 palabras = ~700 tokens
- **1000 documentos** = ~700K tokens = **$0.014** (1.4 centavos)
- **10,000 documentos** = ~7M tokens = **$0.14** (14 centavos)

### Para Uso Normal:
- **1 query** = ~20 palabras = ~30 tokens = **$0.0000006** (despreciable)
- **1000 queries/día** = ~30K tokens/día = **$0.0006/día** = **$0.18/mes**

**Conclusión:** El costo es **mínimo** para proyectos pequeños/medianos.

---

## ⚠️ Notas Importantes

1. **MongoDB Atlas requerido**: Vector Search no funciona en MongoDB local
2. **Re-indexación obligatoria**: Los embeddings actuales (384D) no son compatibles
3. **Internet requerido**: OpenAI API necesita conexión
4. **API Key válida**: Verifica que `OPENAI_API_KEY` esté configurada correctamente

---

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY no está configurado"
**Solución:** Verifica que `.env` tiene la key correcta:
```properties
OPENAI_API_KEY=sk-proj-...
```

### Error: "401 Unauthorized"
**Solución:** La API key es inválida o expiró. Genera una nueva en https://platform.openai.com/api-keys

### Error: "Embedding dimensions mismatch"
**Solución:** Actualiza el índice vectorial en MongoDB Atlas a 1536 dimensiones

### Error: "Rate limit exceeded"
**Solución:** Reduce `batch_size` en `re_index_with_openai.py` o espera unos minutos

---

## 📚 Documentación Adicional

- **OpenAI Embeddings Guide**: https://platform.openai.com/docs/guides/embeddings
- **Pricing**: https://openai.com/api/pricing/
- **MongoDB Vector Search**: https://www.mongodb.com/docs/atlas/atlas-vector-search/

---

## ✅ Checklist de Migración

- [x] Crear servicio OpenAI embeddings
- [x] Actualizar `.env` con configuración
- [x] Instalar dependencias (`openai`, `tqdm`)
- [x] Actualizar exports en `__init__.py`
- [x] Modificar endpoint `/diag/emb`
- [x] Crear scripts de testing y re-indexación
- [ ] **Probar embeddings** → `python test_openai_embeddings.py`
- [ ] **Actualizar índice MongoDB** → Atlas UI o Shell
- [ ] **Re-indexar documentos** → `python re_index_with_openai.py`
- [ ] **Probar endpoints** → `/diag/health`, `/diag/emb`, `/api/chat`

---

¡Listo! 🚀 Ahora tienes embeddings de OpenAI configurados. 

**Siguiente paso:** Ejecuta `python test_openai_embeddings.py` para verificar.
