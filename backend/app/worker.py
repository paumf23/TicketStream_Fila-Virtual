# ═══════════════════════════════════════════════════════════════════════════════
# Este archivo es el motor de la simulación del sistema.
# Funciona como un proceso en segundo plano que procesa la fila
# virtual en tiempo real, implementado bajo un patrón de Inyección de Dependencias.
# ═══════════════════════════════════════════════════════════════════════════════

import asyncio
import json
import logging
import signal
import random
import time
import psutil

class QueueWorker:
    def __init__(self, redis_repo, app_settings):
        """
        Inicializa el Worker inyectando sus dependencias principales.
        """
        self.redis_repo = redis_repo
        self.settings = app_settings
        self._running = True
        self.logger = logging.getLogger("app.worker.QueueWorker")

    def stop(self):
        """Detiene el bucle principal del worker de forma segura."""
        self.logger.warning("Deteniendo el QueueWorker de forma segura...")
        self._running = False

    async def process_event_queue(self, event_id: str, batch_size: int, interval: float, abandon_rate: float = 2.0) -> dict:
        start_time = time.time()

        #===============================================================    
        # 1. CONFIGURACIÓN DE SIMULACIÓN
        #===============================================================    
        config = await self.redis_repo.get_event_config(event_id)
        speed = config["speed"]  # usuarios por minuto
        abandon_rate = config["abandon_rate"]  # 0-100

        # ==============================================================    
        # 2. CUOTAS DE SALIDA PROYECTADAS
        # ==============================================================    
        queue_length = await self.redis_repo.queue_length(event_id)
        
        # Abandonos se calculan sobre el BATCH actual (lógica local)
        abandon_quota = round(batch_size * (abandon_rate / 100))
        # Probabilístico: si el cálculo da 0 pero hay tasa de abandono, dar una chance
        if abandon_quota == 0 and abandon_rate > 0:
            if random.random() < (batch_size * abandon_rate / 100):
                abandon_quota = 1
                
        abandon_quota = min(abandon_quota, batch_size - 1)
        processed_quota = batch_size - abandon_quota
        
        total_to_pop = batch_size  # siempre saca exactamente batch_size

        self.logger.info(f"Evento {event_id}: Q_Len={queue_length}, Proc_Quota={processed_quota}, Aband_Quota={abandon_quota}")

        # ==============================================================
        # 3. PROCESAMIENTO DE LOTE (POP SEGURO → RELIABLE QUEUE)
        # ==============================================================
        users = await self.redis_repo.queue_pop_safe(
            event_id, batch_size=total_to_pop
        )

        if not users:
            # Si no hay nadie, verificamos si la cola está realmente vacía para desactivar el Worker
            if queue_length == 0:
                self.logger.info(f"Fila vacía para evento {event_id}. Desactivando Worker automáticamente.")
                await self.redis_repo.remove_active_simulation(event_id)

            incoming = await self.redis_repo.get_incoming_count(event_id)
            await self.redis_repo.reset_incoming_count(event_id)
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
            await self.redis_repo.set_allowed(
                event_id, user_id, ttl_seconds=self.settings.ALLOWED_TTL
            )
            processed_count += 1

            # Notificar solo si es un usuario real (no simulado) o para depuración
            await self.redis_repo.publish(
                event_id,
                json.dumps({
                    "type": "your_turn",
                    "user_id": user_id,
                    "event_id": event_id,
                    "ttl_seconds": self.settings.ALLOWED_TTL,
                }),
            )

        self.logger.info(f"[DEBUG] Evento {event_id}: Salieron {len(users)} (Proc: {processed_count}, Aband: {abandoned_count})")

        # Limpiar la lista de processing ANTES de actualizar contadores.
        # Si el Worker crashea después de este punto, los contadores no se duplican
        # en el recovery (porque la lista de processing ya está vacía).
        await self.redis_repo.clear_processing(event_id)

        # Actualizar contadores globales en Redis
        if abandoned_count > 0:
            await self.redis_repo.increment_abandoned_count(event_id, abandoned_count)
        if processed_count > 0:
            await self.redis_repo.increment_processed_count(event_id, processed_count)

        # Calcular Tendencia (Entraron - Salieron)
        incoming = await self.redis_repo.get_incoming_count(event_id)
        await self.redis_repo.reset_incoming_count(event_id)
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
        last_stats = await self.redis_repo.get_event_stats_snapshot(event_id)
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
        redis_start = time.time()
        await self.redis_repo.set_event_stats_snapshot(event_id, stats_data)
        redis_latency_ms = (time.time() - redis_start) * 1000

        # ===============================================================
        # 6. LOGS TÉCNICOS ROTATIVOS
        # ===============================================================
        tick_cycle = int(time.time()) % 4
        tech_logs = []
        
        # Log 1: Siempre el estado del lote y la carga del worker
        if tick_cycle == 0:
            tech_logs.append(f"[WORKER] Batch_ID: {random.getrandbits(16):04x} | Proc: {len(users)}u | Load: {effort}%")
        # Log 2: Redis (Latencia real del HSET anterior)
        elif tick_cycle == 1:
            tech_logs.append(f"[REDIS] Latency: {redis_latency_ms:.2f}ms | Pipeline: HSET [OK] | Shard: queue_0")
        # Log 3: Sistema (Memoria y CPU reales usando psutil)
        elif tick_cycle == 2:
            mem_mb = psutil.virtual_memory().used / (1024 * 1024)
            cpu_percent = psutil.cpu_percent()
            tech_logs.append(f"[SYSTEM] Mem: {mem_mb:.1f}MB | CPU_Core: {cpu_percent}% | IO: Stable")
        # Log 4: Red (Estimación del payload de WebSocket enviado)
        else:
            payload_estimate = len(json.dumps(stats_data)) + 300  # Estimación en bytes
            ws_broad_kb = payload_estimate / 1024
            tech_logs.append(f"[NETWORK] WS_Broad: {ws_broad_kb:.2f}KB | Event: {event_id[:8]}...")

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

    async def run(self):
        self.logger.info("🔄 Worker iniciado")

        # ═══ RECOVERY: re-encolar usuarios que quedaron en processing ═══
        # Si el Worker crasheó en un ciclo anterior, puede haber usuarios
        # atrapados en la lista "processing:{event_id}" de Redis.
        # Los movemos de vuelta al frente de la cola para que sean procesados.
        try:
            sim_event_ids_recovery = await self.redis_repo.get_active_simulations()
            for event_id in sim_event_ids_recovery:
                recovered = await self.redis_repo.requeue_processing(event_id)
                if recovered > 0:
                    self.logger.warning(
                        f"♻️ RECOVERY: {recovered} usuarios re-encolados para evento {event_id}"
                    )
        except Exception as e:
            self.logger.error(f"Error durante recovery: {e}")

        self.logger.info(f"   DEFAULT_BATCH: {self.settings.BATCH_SIZE}")
        self.logger.info(f"   PROCESS_INTERVAL: {self.settings.PROCESS_INTERVAL}s")

        while self._running:
            try:
                # 1. EVENTOS CON SIMULACIÓN ACTIVA
                sim_event_ids = await self.redis_repo.get_active_simulations()
                
                if not sim_event_ids:
                    # Si no hay simulaciones, esperamos un poco más
                    await asyncio.sleep(2)
                    continue

                for event_id in sim_event_ids:
                    # 2. CONFIGURACIÓN DE SIMULACIÓN POR EVENTO
                    config = await self.redis_repo.get_event_config(event_id)
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
                    interval = self.settings.PROCESS_INTERVAL

                    # 3. PROCESAMIENTO DE LA COLA (REDIS-ONLY)
                    result = await self.process_event_queue(
                        event_id=event_id,
                        batch_size=batch_size,
                        interval=interval,
                        abandon_rate=abandon_rate
                    )

                    if result:
                        # Publicar telemetría vía WebSocket global
                        await self.redis_repo.publish(event_id, json.dumps(result))

                # Esperar el intervalo configurado
                await asyncio.sleep(self.settings.PROCESS_INTERVAL)

            except Exception as e:
                self.logger.error(f"Error en el ciclo del worker: {e}")
                await asyncio.sleep(5)

        self.logger.info(" Worker finalizado")


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():
    """Punto de entrada principal para ejecutar el worker de forma autónoma."""
    from app.config import settings
    from app.repositories import redis_repository

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("app.worker.main")

    # Inicializar la instancia del worker inyectando las dependencias reales
    worker_instance = QueueWorker(redis_repo=redis_repository, app_settings=settings)

    def _handle_shutdown(signum, frame):
        logger.warning(f"Señal {signum} recibida. Deteniendo worker...")
        worker_instance.stop()

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    logger.info("=" * 60)
    logger.info("  VIRTUAL QUEUE — Worker OOP (Procesador de Cola)")
    logger.info("=" * 60)

    # Iniciar el bucle de eventos
    asyncio.run(worker_instance.run())


if __name__ == "__main__":
    main()
