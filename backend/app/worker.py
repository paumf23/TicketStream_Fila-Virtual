# ═══════════════════════════════════════════════════════════════════════════════
# Este archivo es el motor de la simulación del sistema.
# Funciona como un proceso en segundo plano que procesa la fila
# virtual en tiempo real
# ═══════════════════════════════════════════════════════════════════════════════

import asyncio
import json
import logging
import signal
import random
import time

from app.config import settings
from app.database import AsyncSessionLocal
from app.repositories import event_repository, redis_repository

logger = logging.getLogger("app.worker")

_running = True


def _handle_shutdown(signum, frame):
    global _running
    logger.warning(f"Señal {signum} recibida. Deteniendo worker...")
    _running = False




async def process_event_queue(event_id: str, batch_size: int, interval: float, abandon_rate: float = 2.0) -> dict:
    start_time = time.time()

#===============================================================    
# 1. CONFIGURACIÓN DE SIMULACIÓN
#===============================================================    
    config = await redis_repository.get_event_config(event_id)
    speed = config["speed"]  # usuarios por minuto
    abandon_rate = config["abandon_rate"]  # 0-100

# ==============================================================    
# 2. CUOTAS DE SALIDA PROYECTADAS
# ==============================================================    
    queue_length = await redis_repository.queue_length(event_id)
    
    # Abandonos se calculan sobre el BATCH actual (lógica local)
    abandon_quota = round(batch_size * (abandon_rate / 100))
    # Probabilístico: si el cálculo da 0 pero hay tasa de abandono, dar una chance
    if abandon_quota == 0 and abandon_rate > 0:
        if random.random() < (batch_size * abandon_rate / 100):
            abandon_quota = 1
            
    abandon_quota = min(abandon_quota, batch_size - 1)
    processed_quota = batch_size - abandon_quota
    
    total_to_pop = batch_size  # siempre saca exactamente batch_size

    logger.info(f"Evento {event_id}: Q_Len={queue_length}, Proc_Quota={processed_quota}, Aband_Quota={abandon_quota}")

# = =============================================================
    # 3. PROCESAMIENTO DE LOTE (POP)
# ==============================================================
    users = await redis_repository.queue_pop(
        event_id, batch_size=total_to_pop
    )

    if not users:
        # Si no hay nadie, verificamos si la cola está realmente vacía para desactivar el Worker
        if queue_length == 0:
            logger.info(f"Fila vacía para evento {event_id}. Desactivando Worker automáticamente.")
            await redis_repository.remove_active_simulation(event_id)

        incoming = await redis_repository.get_incoming_count(event_id)
        await redis_repository.reset_incoming_count(event_id)
        # Tendencia = Entraron - Salieron
        trend = int((incoming / interval) * 60)
        return {"total": 0, "effort": 0, "jump": 0, "trend": trend}

    processed_count = 0
    abandoned_count = 0

    for i, user_id in enumerate(users):
        is_sim = user_id.startswith("sim-")
        
        # ¿Debe ser un abandono simulado?
        should_abandon = is_sim and (processed_count >= processed_quota)

        if should_abandon:
            abandoned_count += 1
            continue

        # Procesar como turno entregado
        await redis_repository.set_allowed(
            event_id, user_id, ttl_seconds=settings.ALLOWED_TTL
        )
        processed_count += 1

        # Notificar solo si es un usuario real (no simulado) o para depuración
        await redis_repository.publish(
            event_id,
            json.dumps({
                "type": "your_turn",
                "user_id": user_id,
                "event_id": event_id,
                "ttl_seconds": settings.ALLOWED_TTL,
            }),
        )

    logger.info(f"[DEBUG] Evento {event_id}: Salieron {len(users)} (Proc: {processed_count}, Aband: {abandoned_count})")

    # Actualizar contadores globales en Redis
    if abandoned_count > 0:
        await redis_repository.increment_abandoned_count(event_id, abandoned_count)
    if processed_count > 0:
        await redis_repository.increment_processed_count(event_id, processed_count)

    # Calcular Tendencia (Entraron - Salieron)
    incoming = await redis_repository.get_incoming_count(event_id)
    await redis_repository.reset_incoming_count(event_id)
    outgoing = processed_count + abandoned_count
    
    # Ritmo de Ingreso por minuto
    incoming_rate = int((incoming / interval) * 60)
    
# =================================================================
# 4. MÉTRICAS FINALES
# =================================================================
    execution_time = time.time() - start_time
    effort = min(100, round((execution_time / interval) * 100, 1))
    
    # Flujo total de salida (Throughput)
    throughput_rate = int((outgoing / interval) * 60)
    
    # Tendencia: (Ingreso - Salida) proyectado a 1 minuto
    trend = incoming_rate - throughput_rate

    # Obtener stats actuales para precio y recaudación
    last_stats = await redis_repository.redis_pool.hgetall(f"event:{event_id}:stats")
    total_capacity = int(last_stats.get("total_capacity", 1000))
    price = float(last_stats.get("price", 0.0))
    current_revenue = float(last_stats.get("revenue", 0.0))
    
    # Calcular capacidad restante (solo contar como venta si hay capacidad)
    prev_remaining = int(last_stats.get("remaining_capacity", total_capacity))
    saleable = min(processed_count, prev_remaining)  # solo los que caben
    new_revenue = saleable * price
    total_revenue = current_revenue + new_revenue
    remaining_capacity = max(0, prev_remaining - saleable)

# ===============================================================
# 5. ACTUALIZAR SNAPSHOT EN REDIS
# ===============================================================
    stats_data = {
        "effort": effort,
        "last_jump": outgoing,
        "trend": trend,
        "incoming_rate": incoming_rate,
        "processed_rate": int((processed_count / interval) * 60),
        "total_capacity": total_capacity,
        "remaining_capacity": remaining_capacity,
        "revenue": total_revenue,
        "processed_count": int(last_stats.get("processed_count", 0)) + processed_count,
        "abandoned_count": int(last_stats.get("abandoned_count", 0)) + abandoned_count
    }
    await redis_repository.redis_pool.hset(f"event:{event_id}:stats", mapping=stats_data)

# ===============================================================
# 6. LOGS TÉCNICOS ROTATIVOS (DECORACIÓN)
# ===============================================================
    tick_count = int(time.time())
    tech_logs = []
    
    # Log 1: Siempre el estado del lote
    tech_logs.append(f"[WORKER] Batch_ID: {random.getrandbits(16):04x} | Proc: {len(users)}u | Load: {effort}%")
    
    # Log 2: Rotar entre Redis y Sistema
    if tick_count % 3 == 0:
        tech_logs.append(f"[REDIS] Latency: {random.uniform(0.1, 0.9):.2f}ms | Pipeline: HSET [OK] | Shard: queue_0")
    elif tick_count % 3 == 1:
        tech_logs.append(f"[SYSTEM] Mem: {200 + random.randint(10, 50)}MB | CPU_Core: {random.randint(5, 15)}% | IO: Stable")
    else:
        tech_logs.append(f"[NETWORK] WS_Broad: 1.4KB | Clients: 1 | Latency: {random.randint(5, 25)}ms")

    return {
        "type": "position_update",
        "event_id": event_id,
        "queue_length": queue_length - len(users),
        "users_processed": processed_count,
        "users_abandoned": abandoned_count,
        "processed_rate": stats_data["processed_rate"],
        "throughput": throughput_rate,
        "incoming_rate": incoming_rate,
        "effort": effort,
        "last_jump": outgoing,
        "trend": trend,
        "revenue": total_revenue,
        "remaining_capacity": remaining_capacity,
        "occupancy_percentage": ((total_capacity - remaining_capacity) / total_capacity) * 100 if total_capacity > 0 else 0,
        "tech_logs": tech_logs
    }


async def run_worker():

    logger.info("🔄 Worker iniciado")
    logger.info(f"   DEFAULT_BATCH: {settings.BATCH_SIZE}")
    logger.info(f"   PROCESS_INTERVAL: {settings.PROCESS_INTERVAL}s")

    while True:
        try:
            # 1. EVENTOS CON SIMULACIÓN ACTIVA
            sim_event_ids = await redis_repository.get_active_simulations()
            
            if not sim_event_ids:
                # Si no hay simulaciones, esperamos un poco más
                await asyncio.sleep(2)
                continue

            for event_id in sim_event_ids:
                # 2. CONFIGURACIÓN DE SIMULACIÓN POR EVENTO
                config = await redis_repository.get_event_config(event_id)
                if not config:
                    continue

                # Speed default 360 u/min → base = 6 u/tick
                # Dividimos por 60 para que el Worker (que corre cada 1s) procese ~6 u/seg.
                speed = config.get("speed", 360)
                batch_size = int(speed / 60)
                # Variación dinámica proporcional
                variation = 1 if speed < 120 else random.randint(-2, 3)
                batch_size = max(1, batch_size + variation)
                
                # Clamp solo para simulación normal (para mantener realismo visual)
                if speed <= 360:
                    batch_size = min(9, max(4, batch_size))
                
                abandon_rate = config.get("abandon_rate", 2.0)
                interval = settings.PROCESS_INTERVAL

                # 3. PROCESAMIENTO DE LA COLA (REDIS-ONLY)
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
