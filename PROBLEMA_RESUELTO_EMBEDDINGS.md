# 🎯 PROBLEMA RESUELTO: Incompatibilidad de Dimensiones de Embeddings

## ❌ Problema Identificado

El sistema estaba configurado con **dos sistemas de embeddings incompatibles**:

1. **MongoDB tiene vectores de 1536 dimensiones** (OpenAI text-embedding-3-small)
2. **El pipeline RAG estaba usando vectores de 384 dimensiones** (sentence-transformers/all-MiniLM-L6-v2)

Resultado: **0 resultados en las búsquedas** porque los vectores no coinciden.

---

## ✅ Solución Aplicada

### Archivo modificado: `app/services/rag/pipeline.py`

**ANTES:**
```python
from app.services.embeddings.sentence_transformer import get_embeddings_service  # 384 dims ❌
```

**DESPUÉS:**
```python
from app.services.embeddings import get_embeddings_service  # OpenAI 1536 dims ✅
```

Ahora el sistema usa **OpenAI embeddings (1536 dims)** que coinciden con los vectores en MongoDB.

---

## 🚀 Cómo Probar

### 1. Reiniciar el servidor

Si el servidor está corriendo, detenlo (Ctrl+C) y vuelve a iniciar:

```powershell
# En la terminal con el entorno activado:
uvicorn app.main:app --reload --port 8000
```

### 2. Probar con Postman o cURL

**Request:**
```json
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "query": "What are the effects of microgravity on mice?"
}
```

**O con el paper específico que probaste:**
```json
{
  "query": "Give me information about this following paper: Title: Mice in Bion-M 1 Space Mission: Training and Selection of Animal Subjects"
}
```

### 3. Verificar la respuesta

Ahora deberías ver:
```json
{
  "answer": "...(respuesta generada)...",
  "citations": [
    {
      "source_id": "...",
      "title": "...",
      "snippet": "..."
    }
  ],
  "metrics": {
    "retrieved_k": 8,  // ✅ Ahora debería ser > 0
    "latency_ms": 1234.5
  }
}
```

---

## 📊 Verificación con el Health Endpoint

```bash
GET http://localhost:8000/diag/mongo/health
```

Deberías ver:
```json
{
  "status": "ok",
  "latency_ms": 1313.82,
  "connected": true,
  "database": "nasakb",
  "collection": "chunks",
  "document_count": 151,  // ✅ Tienes 151 documentos
  "indexes": [...],
  "has_vector_index": true
}
```

---

## 🔍 Diagnóstico Adicional (Opcional)

Si todavía tienes problemas, ejecuta:

```powershell
python diagnose_mongodb.py
```

Esto te mostrará:
- ✅ Estructura de los documentos
- ✅ Dimensiones de los embeddings
- ✅ Estado del índice vectorial
- ✅ Campos disponibles

---

## 💡 Notas Importantes

### ¿Por qué pasó esto?

El proyecto tenía configurados **dos sistemas de embeddings**:
1. `openai_embeddings.py` - Para producción (1536 dims, $$$)
2. `sentence_transformer.py` - Para desarrollo local (384 dims, gratis)

El pipeline estaba importando el **incorrecto** para tus datos de MongoDB.

### ¿Qué costos tiene OpenAI embeddings?

- **Modelo**: text-embedding-3-small
- **Costo**: ~$0.00002 / 1,000 tokens
- **Por query**: ~$0.0001 (muy barato)

### ¿Necesito regenerar embeddings?

**NO** - Los embeddings ya están en MongoDB. Solo necesitabas que el pipeline usara el mismo modelo.

---

## 🎉 ¡Listo!

El sistema ahora debería funcionar correctamente:
1. ✅ MongoDB conectado (151 documentos)
2. ✅ Embeddings coinciden (1536 dims - OpenAI)
3. ✅ RAG pipeline configurado correctamente
4. ✅ Búsquedas vectoriales funcionando

**Reinicia el servidor y prueba tu query nuevamente.**
