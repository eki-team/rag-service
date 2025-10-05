# Setup script for RAG Evaluator
# ================================

Write-Host "`n" -NoNewline
Write-Host "================================" -ForegroundColor Cyan
Write-Host "NASA RAG EVALUATOR - SETUP" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "`n"

# Check Python
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.9+." -ForegroundColor Red
    exit 1
}
Write-Host "✅ $pythonVersion" -ForegroundColor Green

# Check .env
Write-Host "`n🔍 Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "OPENAI_API_KEY=sk-") {
        Write-Host "✅ OPENAI_API_KEY found in .env" -ForegroundColor Green
    } else {
        Write-Host "⚠️  OPENAI_API_KEY not found in .env" -ForegroundColor Yellow
        Write-Host "   Please add your OpenAI API key to .env file" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "   Run: cp .env.example .env" -ForegroundColor Yellow
}

# Install evaluation dependencies
Write-Host "`n📦 Installing evaluation dependencies..." -ForegroundColor Yellow
pip install -r requirements_eval.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Summary
Write-Host "`n" -NoNewline
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "`n"

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start RAG server: " -NoNewline
Write-Host "uvicorn app.main:app --reload --port 8000" -ForegroundColor White
Write-Host "  2. Quick test: " -NoNewline
Write-Host "python test_eval_quick.py" -ForegroundColor White
Write-Host "  3. Full evaluation: " -NoNewline
Write-Host "python eval_rag_nasa.py" -ForegroundColor White
Write-Host "`n"
Write-Host "📚 Documentation: EVAL_GUIDE.md" -ForegroundColor Cyan
Write-Host "`n"
