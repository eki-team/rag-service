# Fix para Error de Instalación - NumPy en Python 3.13

## 🐛 **Problema**
```
ERROR: Unknown compiler(s): [['icl'], ['cl'], ['cc'], ['gcc'], ['clang']]
```

**Causa**: NumPy 1.26.4 no tiene wheels precompilados para Python 3.13 y requiere compilar desde source (necesita MSVC/gcc).

---

## ✅ **Solución Aplicada**

### Cambios en `requirements.txt`:

```diff
# === Embeddings (sentence-transformers) ===
sentence-transformers==3.0.1
- numpy==1.26.4
+ numpy>=1.26.4,<2.0.0  # Use latest compatible with Python 3.13
torch==2.3.1

# === Vector Store (MongoDB - Option A) ===
- pymongo==4.6.1
+ pymongo>=4.6.1,<5.0.0  # Use latest with precompiled wheels
dnspython==2.7.0
```

### Razones:
1. **NumPy**: Versiones >= 1.26.4 tienen wheels precompilados para Python 3.13
2. **PyMongo**: Versiones recientes también tienen wheels, evita compilación

---

## 📦 **Instalación**

### Paso 1: Actualizar pip/setuptools
```powershell
pip install --upgrade pip setuptools wheel
```

### Paso 2: Instalar dependencias
```powershell
pip install -r requirements.txt
```

### Paso 3: Verificar instalación
```powershell
python -c "import numpy; print(f'NumPy {numpy.__version__}')"
python -c "import pymongo; print(f'PyMongo {pymongo.__version__}')"
python -c "import sentence_transformers; print('✅ sentence-transformers OK')"
```

---

## 🚨 **Si Aún Falla**

### Opción A: Usar versiones específicas con wheels
```powershell
pip install numpy==2.0.2  # Latest con wheel para Py3.13
pip install pymongo==4.10.1  # Latest con wheel
pip install -r requirements.txt
```

### Opción B: Instalar Visual Studio Build Tools (NO recomendado)
1. Descargar: https://visualstudio.microsoft.com/downloads/
2. Instalar "Build Tools for Visual Studio 2022"
3. Seleccionar: "C++ build tools"
4. Reintentar instalación

**Nota**: Opción B toma >6GB de espacio y es innecesaria si usamos wheels precompilados.

---

## 🔍 **Verificación de Compatibilidad**

### Comprobar versiones disponibles con wheels:
```powershell
# NumPy
pip index versions numpy | Select-String "Available versions"

# PyMongo
pip index versions pymongo | Select-String "Available versions"
```

### Verificar Python instalado:
```powershell
python --version
# Debe mostrar: Python 3.13.x
```

---

## 📊 **Versiones Compatibles Python 3.13**

| Paquete | Versión Vieja | Versión Nueva | Wheel? |
|---------|---------------|---------------|--------|
| numpy | 1.26.4 | >=1.26.4 | ✅ Yes |
| pymongo | 4.6.1 | >=4.6.1 | ✅ Yes |
| torch | 2.3.1 | 2.3.1 | ✅ Yes |
| sentence-transformers | 3.0.1 | 3.0.1 | ✅ Yes |

---

## ⚡ **Instalación Rápida (Recomendado)**

```powershell
# 1. Limpiar instalación anterior
pip uninstall numpy pymongo -y

# 2. Actualizar pip
pip install --upgrade pip

# 3. Instalar con wheels precompilados
pip install numpy pymongo --only-binary :all:

# 4. Instalar resto de requirements
pip install -r requirements.txt
```

**Nota**: `--only-binary :all:` fuerza el uso de wheels y evita compilación.

---

## 🎯 **Resultado Esperado**

```powershell
Successfully installed:
- numpy-2.0.2
- pymongo-4.10.1
- sentence-transformers-3.0.1
- torch-2.3.1
- fastapi-0.116.0
- ... (resto de dependencias)
```

---

## 🔧 **Alternativa: requirements_minimal.txt**

Si aún hay problemas, creamos un archivo con versiones flexibles:

```txt
# Core
fastapi>=0.116.0
uvicorn[standard]>=0.35.0
pydantic>=2.11.0
python-dotenv>=1.1.0

# OpenAI
openai>=1.57.0

# MongoDB
pymongo>=4.6.0
dnspython>=2.7.0

# ML/NLP (flexibles)
sentence-transformers>=3.0.0
numpy>=1.26.0
torch>=2.3.0
rapidfuzz>=3.9.0
tiktoken>=0.7.0
```

Y luego:
```powershell
pip install -r requirements_minimal.txt
```

---

**Siguiente paso**: Ejecuta el comando de instalación después de los cambios aplicados.
