# 🔥 SOLUCIÓN DEFINITIVA: Problema DNS con MongoDB Atlas

## ❌ Problema Confirmado
**Error**: `[Errno 11001] getaddrinfo failed`
**Causa**: Firewall/Antivirus bloqueando consultas DNS en puerto 53

---

## ✅ SOLUCIÓN 1: Desactivar Firewall Temporalmente (MÁS RÁPIDO)

### PowerShell COMO ADMINISTRADOR:
```powershell
# Desactivar firewall
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

# Limpiar cache DNS
ipconfig /flushdns

# Probar
curl http://localhost:8000/diag/mongo/health
```

### Reactivar después:
```powershell
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
```

---

## ✅ SOLUCIÓN 2: Añadir Hosts al archivo `hosts` (PERMANENTE)

### Paso 1: Obtener IPs desde MongoDB Compass

1. Abre **MongoDB Compass**
2. Conéctate a tu cluster
3. Abre la consola **Mongosh** (abajo)
4. Ejecuta:
```javascript
db.adminCommand({isMaster: 1}).hosts
```

Esto te dará algo como:
```
[
  "ac-wbpxnks-shard-00-00.yvrx6cs.mongodb.net:27017",
  "ac-wbpxnks-shard-00-01.yvrx6cs.mongodb.net:27017",
  "ac-wbpxnks-shard-00-02.yvrx6cs.mongodb.net:27017"
]
```

### Paso 2: Obtener las IPs

En Mongosh, ejecuta para cada host:
```javascript
// Esto mostrará la IP a la que estás conectado
db.adminCommand({whatsmyuri: 1})
```

O desde **CMD** (NO PowerShell, NO Python):
```cmd
ping ac-wbpxnks-shard-00-00.yvrx6cs.mongodb.net
ping ac-wbpxnks-shard-00-01.yvrx6cs.mongodb.net
ping ac-wbpxnks-shard-00-02.yvrx6cs.mongodb.net
```

**Anota las IPs que obtengas.**

### Paso 3: Editar archivo hosts

1. Abre **PowerShell COMO ADMINISTRADOR**
2. Ejecuta:
```powershell
notepad C:\Windows\System32\drivers\etc\hosts
```

3. Añade al FINAL del archivo (reemplaza con tus IPs reales):
```
# MongoDB Atlas - nasakb cluster
52.5.XXX.XXX    nasakb.yvrx6cs-shard-00-00.mongodb.net
54.175.XXX.XXX  nasakb.yvrx6cs-shard-00-01.mongodb.net
3.213.XXX.XXX   nasakb.yvrx6cs-shard-00-02.mongodb.net
```

4. Guarda (Ctrl+S) y cierra

5. Ejecuta:
```powershell
ipconfig /flushdns
```

6. Reinicia tu aplicación

---

## ✅ SOLUCIÓN 3: Usar otra red (TEMPORAL)

### Opciones:
1. **Hotspot del móvil** (bypasea firewall corporativo)
2. **VPN** (cambia DNS)
3. **Cambiar a red de casa** (si estás en oficina)

```powershell
# Conecta tu PC al hotspot del móvil
# Luego:
ipconfig /flushdns
curl http://localhost:8000/diag/mongo/health
```

---

## ✅ SOLUCIÓN 4: Usar MongoDB Local (DESARROLLO)

Si ninguna solución funciona, usa MongoDB local temporalmente:

### Con Docker:
```powershell
docker run -d -p 27017:27017 --name mongodb `
  -e MONGO_INITDB_ROOT_USERNAME=admin `
  -e MONGO_INITDB_ROOT_PASSWORD=admin `
  mongo:latest
```

### Actualiza `.env`:
```properties
MONGODB_URI=mongodb://admin:admin@localhost:27017/nasakb?authSource=admin
MONGODB_DB=nasakb
MONGODB_COLLECTION=chunks
```

### Reinicia el servidor:
```powershell
uvicorn app.main:app --reload --port 8000
```

**Nota**: Con MongoDB local NO tendrás Vector Search de Atlas, pero `/api/front` funcionará.

---

## 🎯 RECOMENDACIÓN

**Para desarrollo inmediato:**
1. Prueba SOLUCIÓN 1 (desactivar firewall 5 minutos)
2. Si funciona, usa SOLUCIÓN 2 (hosts file) para hacerlo permanente
3. Si nada funciona, usa SOLUCIÓN 4 (MongoDB local)

**Para producción:**
- Contacta a IT para permitir tráfico DNS saliente (puerto 53)
- O usa VPN corporativa que permita DNS

---

## 📝 Verificar solución

Después de aplicar cualquier solución, verifica:

```powershell
# Test 1: Ping
ping nasakb.yvrx6cs-shard-00-00.mongodb.net

# Test 2: Health check
curl http://localhost:8000/diag/mongo/health

# Test 3: Python directo
python test_mongodb_connection.py
```

---

## ❓ ¿Cuál solución prefieres?

Dime qué opción quieres intentar primero y te guío paso a paso.
