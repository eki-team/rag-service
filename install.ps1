#!/usr/bin/env pwsh
# Script de instalación para rag-service en Python 3.13

Write-Host "🔧 Instalando dependencias para rag-service..." -ForegroundColor Cyan

# Paso 1: Verificar versión de Python
Write-Host "`n📌 Verificando Python..." -ForegroundColor Yellow
python --version

# Paso 2: Actualizar pip
Write-Host "`n📦 Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Paso 3: Instalar dependencias (numpy 2.x ya está instalado)
Write-Host "`n📥 Instalando dependencias desde requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

# Paso 4: Verificar instalación
Write-Host "`n✅ Verificando instalación..." -ForegroundColor Green
python -c "import numpy; print(f'✅ NumPy {numpy.__version__}')"
python -c "import pymongo; print(f'✅ PyMongo {pymongo.__version__}')"
python -c "import fastapi; print(f'✅ FastAPI {fastapi.__version__}')"
python -c "import openai; print(f'✅ OpenAI {openai.__version__}')"
python -c "import sentence_transformers; print('✅ sentence-transformers OK')"

Write-Host "`n🎉 Instalación completada!" -ForegroundColor Green
Write-Host "Para iniciar el servicio: uvicorn app.main:app --reload" -ForegroundColor Cyan
