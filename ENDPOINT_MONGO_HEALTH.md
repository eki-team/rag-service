# 🏥 Endpoint de Health Status de MongoDB

## 📍 Ruta
```
GET /diag/mongo/health
```

## 🎯 Propósito
Verifica el estado de conexión y salud de MongoDB, proporcionando información detallada sobre el cluster, base de datos, colección y rendimiento.

---

## 📊 Respuesta Exitosa

### Cuando MongoDB está conectado:

```json
{
  "status": "connected",
  "connection_type": "mongodb",
  "database": "nasakb",
  "collection": "chunks",
  "server_info": {
    "version": "7.0.0",
    "connected_to": "54.175.123.45:54321",
    "mongodb_uri": "mongodb://admin:***@nasakb.yvrx6cs-shard-00-00.mongodb.net:27017,..."
  },
  "stats": {
    "collections": 5,
    "collections_list": ["chunks", "users", "sessions"],
    "documents_in_collection": 1234,
    "indexes": 3,
    "index_names": ["_id_", "vector_index", "metadata_idx"],
    "vector_index_exists": true,
    "vector_index_name": "vector_index",
    "database_size_bytes": 52428800,
    "database_size_mb": 50.0
  },
  "latency_ms": 45.2,
  "healthy": true
}
```

---

## ❌ Respuesta de Error

### Cuando hay problemas de conexión:

```json
{
  "status": "error",
  "error": "nasakb.yvrx6cs-shard-00-00.mongodb.net:27017: [Errno 11001] getaddrinfo failed",
  "error_type": "ServerSelectionTimeoutError",
  "connection_type": "mongodb",
  "database": "nasakb",
  "collection": "chunks",
  "healthy": false
}
```

---

## 🔍 Campos de la Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `status` | string | Estado de conexión: `connected` o `error` |
| `connection_type` | string | Tipo de backend: `mongodb` |
| `database` | string | Nombre de la base de datos |
| `collection` | string | Nombre de la colección principal |
| `server_info.version` | string | Versión de MongoDB |
| `server_info.connected_to` | string | Host y puerto al que está conectado |
| `server_info.mongodb_uri` | string | URI de conexión (password oculta) |
| `stats.collections` | integer | Número total de colecciones |
| `stats.collections_list` | array | Lista de nombres de colecciones (max 10) |
| `stats.documents_in_collection` | integer | Documentos en la colección principal |
| `stats.indexes` | integer | Número de índices en la colección |
| `stats.index_names` | array | Nombres de los índices |
| `stats.vector_index_exists` | boolean | Si existe el índice vectorial |
| `stats.vector_index_name` | string | Nombre del índice vectorial esperado |
| `stats.database_size_bytes` | integer | Tamaño de la base de datos en bytes |
| `stats.database_size_mb` | float | Tamaño de la base de datos en MB |
| `latency_ms` | float | Latencia de la conexión en milisegundos |
| `healthy` | boolean | `true` si hay conexión y documentos |
| `error` | string | Mensaje de error (solo cuando falla) |
| `error_type` | string | Tipo de error Python (solo cuando falla) |

---

## 🚀 Uso

### Curl
```bash
curl http://localhost:8000/diag/mongo/health
```

### PowerShell
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/diag/mongo/health" -Method Get
```

### Python
```python
import requests

response = requests.get("http://localhost:8000/diag/mongo/health")
health = response.json()

if health.get("healthy"):
    print(f"✅ MongoDB connected: {health['stats']['documents_in_collection']} docs")
    print(f"   Latency: {health['latency_ms']}ms")
    print(f"   Version: {health['server_info']['version']}")
else:
    print(f"❌ MongoDB error: {health.get('error')}")
```

### JavaScript (Frontend)
```javascript
fetch('http://localhost:8000/diag/mongo/health')
  .then(res => res.json())
  .then(health => {
    if (health.healthy) {
      console.log(`✅ MongoDB: ${health.stats.documents_in_collection} docs`);
      console.log(`   Latency: ${health.latency_ms}ms`);
    } else {
      console.error(`❌ MongoDB error: ${health.error}`);
    }
  });
```

---

## 🎯 Casos de Uso

### 1. **Monitoreo de Producción**
Verificar cada X minutos que MongoDB esté respondiendo:
```bash
while true; do
  curl -s http://localhost:8000/diag/mongo/health | jq '.healthy'
  sleep 60
done
```

### 2. **Health Check en CI/CD**
Verificar que la conexión funciona antes de desplegar:
```yaml
# GitHub Actions
- name: Check MongoDB Health
  run: |
    response=$(curl -s http://localhost:8000/diag/mongo/health)
    healthy=$(echo $response | jq -r '.healthy')
    if [ "$healthy" != "true" ]; then
      echo "MongoDB not healthy"
      exit 1
    fi
```

### 3. **Dashboard de Estado**
Mostrar el estado de MongoDB en tiempo real en el frontend:
```javascript
setInterval(async () => {
  const health = await fetch('/diag/mongo/health').then(r => r.json());
  document.getElementById('mongo-status').innerHTML = 
    health.healthy 
      ? `✅ Connected (${health.latency_ms}ms)` 
      : `❌ Disconnected`;
}, 5000);
```

### 4. **Debugging de Problemas DNS**
Verificar a qué host se está conectando realmente:
```bash
curl -s http://localhost:8000/diag/mongo/health | jq '.server_info.connected_to'
# Output: "54.175.123.45:54321"
```

### 5. **Verificar Vector Index**
Comprobar que el índice vectorial existe:
```bash
curl -s http://localhost:8000/diag/mongo/health | jq '.stats.vector_index_exists'
# Output: true o false
```

---

## 🔧 Troubleshooting

### ❌ Error: "getaddrinfo failed"
**Causa**: Firewall bloqueando DNS o no se puede resolver el hostname.

**Solución**:
1. Verificar conexión de red
2. Cambiar DNS a Google (8.8.8.8)
3. Usar conexión directa con IPs en lugar de hostnames
4. Verificar firewall/antivirus

### ❌ Error: "vector_index_exists: false"
**Causa**: No existe el índice vectorial en MongoDB Atlas.

**Solución**:
1. Ir a MongoDB Atlas → Database → Collections
2. Seleccionar la colección `chunks`
3. Tab "Search Indexes" → Create Index
4. Usar JSON:
```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 1536,
        "similarity": "cosine"
      }
    }
  }
}
```

### ❌ Error: "documents_in_collection: 0"
**Causa**: La colección existe pero está vacía.

**Solución**:
1. Insertar documentos de prueba
2. Verificar que la colección sea la correcta en `.env`
3. Ejecutar script de indexación

---

## 📝 Notas

- **Latency**: Valores normales son 20-100ms para MongoDB Atlas.
- **Security**: El password se oculta en la respuesta (`admin:***@`).
- **Performance**: El endpoint hace múltiples queries, puede tardar 1-2 segundos.
- **Caching**: No se cachea, siempre consulta en tiempo real.

---

## ✅ Ejemplo Completo de Verificación

```bash
# 1. Verificar estado general
curl -s http://localhost:8000/diag/mongo/health | jq '.'

# 2. Solo verificar si está healthy
curl -s http://localhost:8000/diag/mongo/health | jq '.healthy'

# 3. Ver latencia
curl -s http://localhost:8000/diag/mongo/health | jq '.latency_ms'

# 4. Contar documentos
curl -s http://localhost:8000/diag/mongo/health | jq '.stats.documents_in_collection'

# 5. Verificar índice vectorial
curl -s http://localhost:8000/diag/mongo/health | jq '.stats.vector_index_exists'

# 6. Ver a qué servidor está conectado
curl -s http://localhost:8000/diag/mongo/health | jq '.server_info.connected_to'
```

---

## 🎉 ¡Listo!

Endpoint creado y documentado. Ahora puedes:
1. Reiniciar el servidor: `uvicorn app.main:app --reload --port 8000`
2. Probar: `curl http://localhost:8000/diag/mongo/health`
3. Ver docs interactivas: http://localhost:8000/docs
