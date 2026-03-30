

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


async def process_event_queue(event_id: str, event_name: str) -> int:

    users = await redis_repository.queue_pop(
        event_id, batch_size=settings.BATCH_SIZE
    )

    if not users:
        return 0

    for user_id in users:
        await redis_repository.set_allowed(
            event_id, user_id, ttl_seconds=settings.ALLOWED_TTL
        )

        await redis_repository.publish(
            event_id,
            json.dumps({
                "type": "your_turn",
                "user_id": user_id,
                "event_id": event_id,
                "event_name": event_name,
                "ttl_seconds": settings.ALLOWED_TTL,
            }),
        )


    queue_length = await redis_repository.queue_length(event_id)
    await redis_repository.publish(
        event_id,
        json.dumps({
            "type": "position_update",
            "event_id": event_id,
            "queue_length": queue_length,
            "users_processed": len(users),
        }),
    )

    return len(users)


async def run_worker():

    logger.info("🔄 Worker iniciado")
    logger.info(f"   BATCH_SIZE: {settings.BATCH_SIZE}")
    logger.info(f"   PROCESS_INTERVAL: {settings.PROCESS_INTERVAL}s")
    logger.info(f"   ALLOWED_TTL: {settings.ALLOWED_TTL}s")

    while _running:
        try:

            async with AsyncSessionLocal() as db:

                active_events = await event_repository.get_active_events(db)
                await db.commit()

                total_processed = 0

                for event in active_events:
                    processed = await process_event_queue(
                        event_id=event.id,
                        event_name=event.name,
                    )
                    total_processed += processed

                if total_processed > 0:
                    logger.info(
                        f"✅ Ciclo: {total_processed} usuarios procesados "
                        f"en {len(active_events)} evento(s) activo(s)"
                    )

        except Exception as e:
            logger.error(f" Error en ciclo del worker: {e}", exc_info=True)


        await asyncio.sleep(settings.PROCESS_INTERVAL)

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
