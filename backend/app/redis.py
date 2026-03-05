
# ═══════════════════════════════════════════════════════════════════════════════
# redis.py — Pool de Conexiones a Redis
# ═══════════════════════════════════════════════════════════════════════════════
# redis_pool es un POOL (pileta) de conexiones a Redis.
# En vez de abrir y cerrar una conexión cada vez que hacemos un PING, SET o GET,
# el pool MANTIENE hasta 50 conexiones abiertas y las REUTILIZA.
# Esto es mucho más eficiente, especialmente bajo alta concurrencia.
#
# from_url() crea el pool a partir de la URL de Redis (ej: redis://redis:6379).
# decode_responses=True hace que Redis devuelva strings en vez de bytes.
# max_connections=50 limita la cantidad máxima de conexiones simultáneas.
#
# Este objeto se importa en toda la aplicación (health.py, repositories, etc.)
# para interactuar con Redis sin crear conexiones nuevas cada vez.
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
