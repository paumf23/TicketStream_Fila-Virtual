

import asyncio
import json
import logging
import signal

from app.config import settings
from app.database import AsyncSessionLocal
from app.repositories import event_repository, redis_repository

logger = logging.getLogger("app.worker")

_running = True


def _handle_shutdown(signum, frame):
    global _running
    logger.warning(f"Señal {signum} recibida. Deteniendo worker...")
    _running = False


import random
import time

async def process_event_queue(event_id: str, batch_size: int, interval: float, abandon_rate: float = 2.0) -> dict:
    start_time = time.time()
    
    # 1. Obtener configuración de simulación
    config = await redis_repository.get_event_config(event_id)
    speed = config["speed"]  # usuarios por minuto
    abandon_rate = config["abandon_rate"]  # 0-100

    # 2. Obtener el lote dinámico
    users = await redis_repository.queue_pop(
        event_id, batch_size=batch_size
    )

    if not users:
        # Si no hay nadie, igual calculamos tendencia basada en entradas
        incoming = await redis_repository.get_incoming_count(event_id)
        await redis_repository.reset_incoming_count(event_id)
        # Tendencia = Entraron - Salieron (en este caso 0 salieron)
        # Convertimos a rate por minuto: (count / interval) * 60
        trend = int((incoming / interval) * 60)
        return {"total": 0, "effort": 0, "jump": 0, "trend": trend}

    processed_count = 0
    abandoned_count = 0

    for user_id in users:
        # Simular abandono
        if random.random() * 100 < abandon_rate:
            abandoned_count += 1
            continue

        await redis_repository.set_allowed(
            event_id, user_id, ttl_seconds=settings.ALLOWED_TTL
        )
        processed_count += 1

        await redis_repository.publish(
            event_id,
            json.dumps({
                "type": "your_turn",
                "user_id": user_id,
                "event_id": event_id,
                "ttl_seconds": settings.ALLOWED_TTL,
            }),
        )

    # Actualizar contadores globales
    if abandoned_count > 0:
        await redis_repository.increment_abandoned_count(event_id, abandoned_count)
    if processed_count > 0:
        await redis_repository.increment_processed_count(event_id, processed_count)

    # Calcular Tendencia (Entraron - Salieron)
    incoming = await redis_repository.get_incoming_count(event_id)
    await redis_repository.reset_incoming_count(event_id)
    outgoing = processed_count + abandoned_count
    
    # Tendencia por minuto
    trend = int(((incoming - outgoing) / interval) * 60)
    
    # Ritmo de Ingreso por minuto
    incoming_rate = int((incoming / interval) * 60)
    
    # Calcular Esfuerzo (Tiempo real vs Intervalo disponible)
    execution_time = time.time() - start_time
    effort = min(100, round((execution_time / interval) * 100, 1))

    queue_length = await redis_repository.queue_length(event_id)
    
    # Guardar último snapshot para el App (REST API)
    await redis_repository.redis_pool.hset(
        f"event:{event_id}:stats",
        mapping={
            "effort": effort,
            "last_jump": outgoing,
            "trend": trend,
            "incoming_rate": incoming_rate
        }
    )

    # Métricas técnicas adicionales para la consola
    import psutil
    cpu_percent = psutil.cpu_percent()
    
    # Medir latencia de Redis (ping simple)
    r_start = time.time()
    await redis_repository.redis_pool.ping()
    # El flujo total de salida en este tick
    outgoing = processed_count + abandoned_count
    
    # Obtener stats actuales para calcular tendencia
    last_stats = await redis_repository.redis_pool.hgetall(f"event:{event_id}:stats")
    
    total_capacity = int(last_stats.get("total_capacity", 1000))
    price = float(last_stats.get("price", 0.0))
    # Para la simulación, recalculamos remaining_capacity localmente o la pedimos a Redis
    # Aquí vamos a simular que el procesamiento reduce el remaining (aunque no toque MySQL aún)
    prev_remaining = int(last_stats.get("remaining_capacity", total_capacity))
    remaining_capacity = max(0, prev_remaining - processed_count)

    # Simular esfuerzo del servidor (oscilación aleatoria)
    effort = round(random.uniform(15.0, 45.0), 2)
    
    # Simular ritmo de ingreso (en simulación avanzada, suele ser 0 o lo que venga de Redis)
    incoming_rate = int(last_stats.get("incoming_rate", 0))
    
    # Tendencia: (Ingreso - Salida) proyectado a 1 minuto
    # Asumimos que outgoing es por intervalo, así que (outgoing/interval)*60 es el rate
    throughput_rate = int((outgoing / interval) * 60)
    trend = incoming_rate - throughput_rate

    # 4. Guardar snapshot de métricas en Redis
    stats_data = {
        "effort": effort,
        "last_jump": outgoing,
        "trend": trend,
        "incoming_rate": incoming_rate,
        "processed_rate": int((processed_count / interval) * 60),
        "total_capacity": total_capacity,
        "remaining_capacity": remaining_capacity,
        "price": price
    }
    await redis_repository.redis_pool.hset(f"event:{event_id}:stats", mapping=stats_data)

    # 5. Retornar telemetría para el WebSocket global
    return {
        "type": "position_update",
        "event_id": event_id,
        "queue_length": queue_length,
        "users_processed": processed_count,
        "users_abandoned": abandoned_count,
        "processed_rate": stats_data["processed_rate"],
        "throughput": throughput_rate,
        "incoming_rate": incoming_rate,
        "effort": effort,
        "last_jump": outgoing,
        "trend": trend,
        "tech_logs": [
            f"[WORKER] Lote de {len(users)} usuarios procesado (Pipeline OK)",
            f"[REDIS] {processed_count} compras / {abandoned_count} abandonos",
            f"[DIAG] Rendimiento: {throughput_rate} u/min | Esfuerzo: {effort}%"
        ]
    }


async def run_worker():

    logger.info("🔄 Worker iniciado")
    logger.info(f"   DEFAULT_BATCH: {settings.BATCH_SIZE}")
    logger.info(f"   PROCESS_INTERVAL: {settings.PROCESS_INTERVAL}s")

    while True:
        try:
            # 1. Obtener eventos con simulación activa desde REDIS (Redis-only)
            sim_event_ids = await redis_repository.get_active_simulations()
            
            if not sim_event_ids:
                # Si no hay simulaciones, esperamos un poco más
                await asyncio.sleep(2)
                continue

            for event_id in sim_event_ids:
                # Obtener configuración de simulación desde Redis
                config = await redis_repository.get_event_config(event_id)
                if not config:
                    continue

                batch_size = config.get("speed", settings.BATCH_SIZE)
                abandon_rate = config.get("abandon_rate", 2.0)
                interval = settings.PROCESS_INTERVAL

                # Procesar la cola (Redis-only)
                result = await process_event_queue(
                    event_id=event_id,
                    batch_size=batch_size,
                    interval=interval,
                    abandon_rate=abandon_rate
                )

                if result:
                    # Publicar telemetría vía WebSocket global
                    await redis_repository.publish(event_id, json.dumps(result))

            # Esperar el intervalo configurado
            await asyncio.sleep(settings.PROCESS_INTERVAL)

        except Exception as e:
            logger.error(f"Error en el ciclo del worker: {e}")
            await asyncio.sleep(5)

    logger.info(" Worker finalizado")


def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    logger.info("=" * 60)
    logger.info("  VIRTUAL QUEUE — Worker (Procesador de Cola)")
    logger.info("=" * 60)

    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
