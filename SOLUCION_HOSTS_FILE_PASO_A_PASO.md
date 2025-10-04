# 🔧 SOLUCIÓN DEFINITIVA: Modificar Archivo Hosts (Bypass DNS Completo)

## ❌ Problema
Tu firewall/antivirus bloquea el puerto DNS 53, haciendo imposible resolver:
- `nasakb.yvrx6cs-shard-00-00.mongodb.net`
- `nasakb.yvrx6cs-shard-00-01.mongodb.net`
- `nasakb.yvrx6cs-shard-00-02.mongodb.net`

Error: `The resolution lifetime expired after 10.011 seconds: Server Do53:185.228.168.168@53 answered The DNS operation timed out.`

## ✅ Solución: Agregar IPs Manualmente al Archivo Hosts

### PASO 1: Obtener las IPs de MongoDB Compass

1. **Abre MongoDB Compass** (que SÍ funciona)
2. **Conéctate** a tu cluster nasakb
3. Una vez conectado, ve a: **"Performance" tab** o busca la sección **"Server Status"**
4. **Copia las IPs** de los 3 shards

#### Si no encuentras las IPs en Compass, usa `nslookup` desde otra red:

**Opción A: Desde tu celular con hotspot móvil:**
```powershell
# Conecta tu PC al hotspot de tu celular
# Luego ejecuta:
nslookup nasakb.yvrx6cs-shard-00-00.mongodb.net
nslookup nasakb.yvrx6cs-shard-00-01.mongodb.net
nslookup nasakb.yvrx6cs-shard-00-02.mongodb.net
```

**Opción B: Desde una VPN:**
```powershell
# Activa una VPN (ProtonVPN, Windscribe, etc.)
# Luego ejecuta los mismos comandos nslookup
```

### PASO 2: Editar el Archivo Hosts (Requiere Administrador)

1. **Abre Notepad como Administrador:**
   - Presiona `Win + X`
   - Selecciona **"Windows PowerShell (Admin)"** o **"Terminal (Admin)"**
   
2. **Abre el archivo hosts:**
   ```powershell
   notepad C:\Windows\System32\drivers\etc\hosts
   ```

3. **Agrega al final del archivo** (reemplaza las IPs XXX.XXX.XXX.XXX con las reales):
   ```
   # MongoDB Atlas - nasakb cluster
   XXX.XXX.XXX.XXX nasakb.yvrx6cs-shard-00-00.mongodb.net
   YYY.YYY.YYY.YYY nasakb.yvrx6cs-shard-00-01.mongodb.net
   ZZZ.ZZZ.ZZZ.ZZZ nasakb.yvrx6cs-shard-00-02.mongodb.net
   ```

4. **Guarda el archivo** (Ctrl + S)

5. **Cierra Notepad**

### PASO 3: Limpiar Caché DNS

```powershell
# Ejecuta como Administrador:
ipconfig /flushdns
```

### PASO 4: Verificar que Funciona

```powershell
# Debería devolver las IPs que agregaste:
ping nasakb.yvrx6cs-shard-00-00.mongodb.net
ping nasakb.yvrx6cs-shard-00-01.mongodb.net
ping nasakb.yvrx6cs-shard-00-02.mongodb.net
```

### PASO 5: Probar MongoDB

```powershell
# En tu proyecto:
cd "c:\Users\insec\OneDrive\Escritorio\EKI-TEAM\rag-service"
.\.venv\Scripts\Activate.ps1
python test_mongo_simple.py
```

---

## 📝 Ejemplo Real de Archivo Hosts

```
# Copyright (c) 1993-2009 Microsoft Corp.
#
# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.
#
# ... (contenido existente) ...

127.0.0.1       localhost
::1             localhost

# MongoDB Atlas - nasakb cluster
3.7.184.117     nasakb.yvrx6cs-shard-00-00.mongodb.net
54.165.42.89    nasakb.yvrx6cs-shard-00-01.mongodb.net
18.208.247.221  nasakb.yvrx6cs-shard-00-02.mongodb.net
```

*(⚠️ Las IPs de ejemplo arriba son ficticias - usa las reales de tu cluster)*

---

## 🎯 ¿Por Qué Funciona Esta Solución?

✅ **Bypass total del DNS** - Windows ya no pregunta al DNS, usa las IPs directamente  
✅ **Compatible con tu firewall** - No usa el puerto 53  
✅ **Permanente** - No se pierde al reiniciar  
✅ **Sin necesidad de desactivar firewall**  

---

## 🚨 Alternativa si no puedes editar el archivo hosts:

### Método 1: Usar MongoDB Atlas con IP Pública
```bash
# En vez de hostname, usa IP directamente:
MONGODB_URI=mongodb://admin:admin@3.7.184.117:27017,54.165.42.89:27017,18.208.247.221:27017/nasakb?retryWrites=true&w=majority&authSource=admin&tls=true&tlsAllowInvalidCertificates=true
```

### Método 2: Usar MongoDB Local con Docker
```powershell
# Instalar Docker Desktop
# Luego ejecutar:
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

---

## 📞 ¿Necesitas Ayuda?

Si no puedes obtener las IPs, dime y te ayudo con otros métodos para obtenerlas.
