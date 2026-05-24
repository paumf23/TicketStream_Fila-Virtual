"""
Repositorio para la gestión de datos en Redis: operaciones de cola, 
configuración de eventos y métricas de simulación en tiempo real.
"""

import redis.asyncio as aioredis

from app.redis import redis_pool


# --- Helpers y Utilidades Internas ---
# Funciones internas para la generación de llaves y gestión de estados auxiliares de Redis.

def _queue_key(event_id: str) -> str:
    return f"queue:{event_id}"


def _allowed_key(event_id: str, user_id: str) -> str:
    return f"allowed:{event_id}:{user_id}"


def _channel_key(event_id: str) -> str:
    return f"channel:queue:{event_id}"


def _peak_queue_key(event_id: str) -> str:
    return f"peak_queue:{event_id}"


def _user_name_key(user_id: str) -> str:
    return f"user_name:{user_id}"


def _event_config_key(event_id: str) -> str:
    return f"event_config:{event_id}"


def _processing_key(event_id: str) -> str:
    return f"processing:{event_id}"


async def _update_peak_queue_length(event_id: str, current_length: int) -> None:
    key = _peak_queue_key(event_id)
    current_peak = await redis_pool.get(key)
    if current_peak is None or current_length > int(current_peak):
        await redis_pool.set(key, str(current_length))


# --- Operaciones de Cola ---
# Métodos para gestionar el flujo de usuarios, posiciones y estados de la fila virtual.

async def queue_push(event_id: str, user_id: str) -> int:
    position = await redis_pool.rpush(_queue_key(event_id), user_id)
    await increment_incoming_count(event_id, 1)
    await _update_peak_queue_length(event_id, position)
    # Activar el Worker automáticamente para este evento
    await add_active_simulation(event_id)
    return position


async def bulk_push(event_id: str, user_ids: list[str]) -> None:
    if not user_ids:
        return
    
    key = _queue_key(event_id)
    async with redis_pool.pipeline(transaction=True) as pipe:
        for i in range(0, len(user_ids), 100):
            chunk = user_ids[i : i + 100]
            pipe.rpush(key, *chunk)
        pipe.llen(key)
        results = await pipe.execute()
        
        # El último resultado es el tamaño total de la cola
        new_length = results[-1]
        await _update_peak_queue_length(event_id, new_length)
    await increment_incoming_count(event_id, len(user_ids))
    # Activar el Worker automáticamente para este evento
    await add_active_simulation(event_id)


# --- Cola Segura (Reliable Queue Pattern) ---
# Lua script ejecutado atómicamente dentro de Redis.
# Mueve N elementos de la cola principal a una lista temporal de "processing".
# Si el Worker crashea, los usuarios quedan en "processing" y pueden recuperarse.

_SAFE_POP_SCRIPT = """
local source = KEYS[1]
local dest = KEYS[2]
local count = tonumber(ARGV[1])
local moved = {}

for i = 1, count do
    local val = redis.call('LPOP', source)
    if not val then break end
    redis.call('RPUSH', dest, val)
    table.insert(moved, val)
end

return moved
"""


async def queue_pop_safe(event_id: str, batch_size: int = 10) -> list[str]:
    """Mueve usuarios de la cola a la lista de processing (atómico via Lua)."""
    source = _queue_key(event_id)
    dest = _processing_key(event_id)

    result = await redis_pool.eval(
        _SAFE_POP_SCRIPT, 2, source, dest, batch_size
    )
    return [r if isinstance(r, str) else r.decode() for r in (result or [])]


async def clear_processing(event_id: str) -> None:
    """Limpia la lista de processing después de un batch exitoso."""
    await redis_pool.delete(_processing_key(event_id))


async def get_processing_users(event_id: str) -> list[str]:
    """Obtiene los usuarios que quedaron en processing (para recovery)."""
    users = await redis_pool.lrange(_processing_key(event_id), 0, -1)
    return [u if isinstance(u, str) else u.decode() for u in users]


async def requeue_processing(event_id: str) -> int:
    """Mueve usuarios de processing de vuelta a la cola (recovery al reiniciar)."""
    processing_key = _processing_key(event_id)
    queue_key = _queue_key(event_id)

    users = await redis_pool.lrange(processing_key, 0, -1)
    if not users:
        return 0

    # Re-insertar al frente de la cola (tienen prioridad, ya esperaron)
    async with redis_pool.pipeline(transaction=True) as pipe:
        for user in reversed(users):  # reversed para mantener orden original
            pipe.lpush(queue_key, user)
        pipe.delete(processing_key)
        await pipe.execute()

    return len(users)


async def queue_position(event_id: str, user_id: str) -> int | None:
    pos = await redis_pool.lpos(_queue_key(event_id), user_id)
    return pos


async def queue_length(event_id: str) -> int:
    return await redis_pool.llen(_queue_key(event_id))


async def queue_remove(event_id: str, user_id: str) -> bool:
    removed = await redis_pool.lrem(_queue_key(event_id), 1, user_id)
    return removed > 0


async def remove_queue_entry(event_id: str, user_id: str) -> None:
    key = f"event:{event_id}:queue"
    await redis_pool.lrem(key, 0, user_id)


async def clear_queue(event_id: str) -> None:
    """Limpia completamente el estado de la cola y estadísticas de simulación."""
    await redis_pool.delete(_queue_key(event_id))
    await redis_pool.delete(f"event:{event_id}:abandoned")
    await redis_pool.delete(f"event:{event_id}:processed")
    await redis_pool.delete(f"event:{event_id}:incoming")
    await redis_pool.delete(f"event:{event_id}:stats")


# --- Configuración y Métricas de Simulación ---
# Gestión de parámetros de simulación y contadores estadísticos de flujo de usuarios.

async def get_event_stats_snapshot(event_id: str) -> dict:
    """Obtiene el snapshot de métricas dinámicas (stats) del evento."""
    return await redis_pool.hgetall(f"event:{event_id}:stats")


async def set_event_stats_snapshot(event_id: str, stats_data: dict) -> None:
    """Actualiza el snapshot de métricas dinámicas (stats) del evento."""
    await redis_pool.hset(f"event:{event_id}:stats", mapping=stats_data)


async def set_event_config(
    event_id: str, speed: int, abandon_rate: float
) -> None:
    key = _event_config_key(event_id)
    # Guardamos en un hash para recuperarlo fácilmente
    await redis_pool.hset(
        key,
        mapping={"speed": speed, "abandon_rate": abandon_rate}
    )


async def get_event_config(event_id: str) -> dict:
    key = _event_config_key(event_id)
    data = await redis_pool.hgetall(key)
    return {
        "speed": int(data.get("speed") or 360),
        "abandon_rate": float(data.get("abandon_rate") or 1.5),
    }


async def get_peak_queue_length(event_id: str) -> int:
    result = await redis_pool.get(_peak_queue_key(event_id))
    return int(result) if result is not None else 0


async def increment_abandoned_count(event_id: str, count: int = 1) -> None:
    await redis_pool.incrby(f"event:{event_id}:abandoned", count)


async def get_abandoned_count(event_id: str) -> int:
    val = await redis_pool.get(f"event:{event_id}:abandoned")
    return int(val) if val else 0


async def increment_processed_count(event_id: str, count: int = 1) -> None:
    await redis_pool.incrby(f"event:{event_id}:processed", count)


async def get_processed_count(event_id: str) -> int:
    val = await redis_pool.get(f"event:{event_id}:processed")
    return int(val) if val else 0


async def increment_incoming_count(event_id: str, count: int = 1) -> None:
    await redis_pool.incrby(f"event:{event_id}:incoming", count)


async def get_incoming_count(event_id: str) -> int:
    val = await redis_pool.get(f"event:{event_id}:incoming")
    return int(val) if val else 0


async def reset_incoming_count(event_id: str) -> None:
    await redis_pool.delete(f"event:{event_id}:incoming")


# --- Control de Acceso y Permisos ---
# Funciones para autorizar y verificar el paso de usuarios hacia la sección de compra.

async def set_allowed(event_id: str, user_id: str, ttl_seconds: int = 300) -> None:
    key = _allowed_key(event_id, user_id)
    await redis_pool.set(key, "1", ex=ttl_seconds)


async def is_allowed(event_id: str, user_id: str) -> bool:
    result = await redis_pool.get(_allowed_key(event_id, user_id))
    return result is not None


async def remove_allowed(event_id: str, user_id: str) -> None:
    await redis_pool.delete(_allowed_key(event_id, user_id))


# --- Gestión de Simulación Activa y Mensajería ---
# Orquestación de eventos activos y publicación de mensajes en tiempo real mediante Pub/Sub.

async def add_active_simulation(event_id: str) -> None:
    await redis_pool.sadd("sim:active_events", event_id)


async def remove_active_simulation(event_id: str) -> None:
    await redis_pool.srem("sim:active_events", event_id)


async def get_active_simulations() -> list[str]:
    events = await redis_pool.smembers("sim:active_events")
    return [e.decode("utf-8") if isinstance(e, bytes) else e for e in events]


async def publish(event_id: str, message: str) -> int:
    return await redis_pool.publish(_channel_key(event_id), message)


async def subscribe(event_id: str) -> aioredis.client.PubSub:
    pubsub = redis_pool.pubsub()
    await pubsub.subscribe(_channel_key(event_id))
    return pubsub


# --- Información del Usuario ---
# Almacenamiento temporal y recuperación de datos descriptivos de los participantes.

async def set_user_name(
    user_id: str, first_name: str, last_name: str
) -> None:
    key = _user_name_key(user_id)
    await redis_pool.hset(key, mapping={
        "first_name": first_name,
        "last_name": last_name,
    })
    await redis_pool.expire(key, 3600)


async def get_user_name(user_id: str) -> dict | None:
    key = _user_name_key(user_id)
    data = await redis_pool.hgetall(key)
    if not data:
        return None
    return {
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
    }


# --- Rate Limiting ---
# Control de tasa de peticiones basado en IP y endpoint.

# LUA SCRIPT PARA RATE LIMITING ATÓMICO
# ¿Qué es Lua?: Es un lenguaje de programación rápido y ligero integrado dentro de Redis.
# ¿Por qué lo usamos aquí?: Cuando enviamos un script Lua a Redis, este lo ejecuta entero como una sola
# operación "atómica". Ninguna otra petición puede meterse en el medio. Esto soluciona la "Race Condition"
# donde dos peticiones simultáneas podrían leer el mismo contador antes de incrementarlo.
_RATE_LIMIT_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if current and tonumber(current) >= tonumber(ARGV[1]) then
    return 0 -- Superó el límite
end
current = redis.call('INCR', KEYS[1])
if tonumber(current) == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
end
return 1 -- Permitido
"""

async def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """
    Verifica si una llave (IP:path) superó el límite en una ventana de tiempo.
    Retorna True si puede proceder, False si debe ser bloqueado.
    Utiliza un script Lua para garantizar que la lectura y el incremento sean atómicos.
    """
    result = await redis_pool.eval(
        _RATE_LIMIT_SCRIPT, 
        1,       # Número de llaves (solo usamos 1 llave)
        key,     # Se mapea a KEYS[1]
        limit,   # Se mapea a ARGV[1]
        window   # Se mapea a ARGV[2]
    )
    return bool(result)
