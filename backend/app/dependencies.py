from fastapi import Request
from app.repositories import redis_repository
from app.exceptions import RateLimitError
from app.database import get_db

def rate_limit(limit: int, window: int):
    """
    Dependencia de FastAPI para aplicar rate limiting basado en IP y ruta.
    
    Uso:
    @router.post("/un-path", dependencies=[Depends(rate_limit(5, 60))])
    """
    async def dependency(request: Request):
        # Identificamos al usuario por su IP
        # En entornos Docker, si hay un proxy, se debería usar el header X-Forwarded-For
        client_ip = request.client.host
        path = request.url.path
        
        # Llave única en Redis para este usuario y este endpoint
        key = f"ratelimit:{client_ip}:{path}"
        
        # Consultamos al repositorio si el usuario puede proceder
        allowed = await redis_repository.check_rate_limit(key, limit, window)
        
        if not allowed:
            # Si superó el límite, lanzamos la excepción de dominio (429)
            raise RateLimitError(
                f"Límite de peticiones excedido. Máximo {limit} peticiones cada {window} segundos."
            )
            
    return dependency
