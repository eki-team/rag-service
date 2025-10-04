
"""
NASA Biology RAG Service - Main FastAPI App
"""
from fastapi import FastAPI
from app.core.settings import settings
from app.core.security import setup_cors
from app.api.routers import chat, diag
import logging

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NASA Biology RAG Service",
    description="RAG service for NASA space biology research (OSDR, LSL, TASKBOOK)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup CORS
setup_cors(app)

# Include routers
app.include_router(chat.router)
app.include_router(diag.router)

logger.info(f"🚀 NASA RAG initialized - Backend: {settings.VECTOR_BACKEND}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "nasa-rag",
        "version": "1.0.0",
        "status": "running",
        "mode": "nasa-biology" if settings.NASA_MODE else "generic",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Simple health check"""
    return {
        "status": "ok",
        "service": "nasa-rag",
    }