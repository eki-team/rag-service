"""
NASA Biology RAG - Security
CORS y rate limiting simple (opcional).
"""
from fastapi import Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from app.core.settings import settings


# === Rate Limiter Simple (en memoria) ===
class SimpleRateLimiter:
    """Rate limiter simple basado en IP"""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)
    
    def check(self, client_ip: str) -> bool:
        """Check if client can make request"""
        now = datetime.utcnow()
        # Limpiar requests antiguos
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        self.requests[client_ip].append(now)
        return True


rate_limiter = SimpleRateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW
)


async def rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limiting"""
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
    
    return await call_next(request)


def setup_cors(app):
    """Setup CORS middleware"""
    # Verificar si CORS está configurado para permitir todos los orígenes
    if settings.CORS_ORIGINS.strip(' "') == "*":
        # Permitir todos los orígenes
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,  # IMPORTANTE: False cuando allow_origins=["*"]
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # Usar orígenes específicos
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
