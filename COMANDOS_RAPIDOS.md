# 🚀 Comandos Rápidos - OpenAI Embeddings

## ✅ 1. Probar que funciona

```bash
python test_openai_embeddings.py
```

**Resultado esperado:**
```
✅ All tests passed!
- Model: text-embedding-3-small
- Dimensions: 1536
```

---

## ✅ 2. Iniciar servidor

```bash
uvicorn app.main:app --reload --port 8000
```

---

## ✅ 3. Probar endpoints

### Health Check
```bash
curl http://localhost:8000/diag/health
```

### Test Embedding
```bash
curl -X POST "http://localhost:8000/diag/emb" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"microgravity effects\"}"
```

**Esperas ver:**
```json
{
  "text": "microgravity effects",
  "embedding_length": 1536,
  "model": "text-embedding-3-small"
}
```

---

## ⚠️ 4. Actualizar índice MongoDB Atlas

### Opción 1: UI
1. Atlas → Database → Collections
2. `mydb.pub_chunks` → Search Indexes
3. Eliminar índice actual
4. Crear nuevo con 1536 dimensiones

### Opción 2: Shell
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

---

## ⚠️ 5. Re-indexar documentos (si tienes datos)

```bash
# Re-indexar todos
python re_index_with_openai.py

# Con opciones
python re_index_with_openai.py --batch-size 50 --skip-existing
```

**Nota:** Esto costará ~$0.014 por cada 1000 documentos

---

## 📊 6. Ver estadísticas

```bash
curl http://localhost:8000/api/front/stats
```

---

## 🧪 7. Probar RAG Chatbot

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the effects of microgravity on the immune system?",
    "top_k": 8
  }'
```

---

## 📚 Swagger UI

Abre en navegador: **http://localhost:8000/docs**

---

## 🐛 Si algo falla:

### Error de API Key:
```bash
# Verifica que la key esté en .env
cat .env | grep OPENAI_API_KEY
```

### Error de dimensiones:
```bash
# Verifica configuración
cat .env | grep EMBEDDING
```

### Ver logs del servidor:
```bash
# En la terminal donde corre uvicorn
# Los logs mostrarán errores detallados
```

---

## 📝 Checklist Rápido

- [ ] `python test_openai_embeddings.py` → ✅
- [ ] Actualizar índice MongoDB → 1536 dims
- [ ] Re-indexar documentos (si tienes)
- [ ] `uvicorn app.main:app --reload`
- [ ] `curl http://localhost:8000/diag/health` → ✅
- [ ] `curl POST /diag/emb` → 1536 dims ✅
- [ ] Probar chatbot en Swagger UI

---

¡Eso es todo! 🎉
