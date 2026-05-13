# ═══════════════════════════════════════════════════════════════════════════════
# Configuración y conexión con la base de datos Redis
# Se crea pool de conexiones para manejar las operaciones asíncronas con Redis
# Se utiliza redis.asyncio (módulo async de redis-py 5.x, importado como aioredis)
# Con get_redis() los módulos del backend obtienen la instancia de Redis para
# guardar o recuperar datos (como la fila de espera o métricas en tiempo real   )
# ═══════════════════════════════════════════════════════════════════════════════

import redis.asyncio as aioredis

from app.config import settings

redis_pool = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=50,
)


async def get_redis() -> aioredis.Redis:
    return redis_pool
