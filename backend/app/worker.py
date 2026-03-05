
# ═══════════════════════════════════════════════════════════════════════════════
# worker.py — Procesador de Cola (Background Worker)
# ═══════════════════════════════════════════════════════════════════════════════


import asyncio
import json
import signal

from app.config import settings
from app.database import AsyncSessionLocal
from app.repositories import redis_repository
from app.repositories import event_repository


_running = True


def _handle_shutdown(signum, frame):
    global _running
    print(f"\n⚠️  Señal {signum} recibida. Deteniendo worker...")
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
 
    print(f"🔄 Worker iniciado")
    print(f"   BATCH_SIZE: {settings.BATCH_SIZE}")
    print(f"   PROCESS_INTERVAL: {settings.PROCESS_INTERVAL}s")
    print(f"   ALLOWED_TTL: {settings.ALLOWED_TTL}s")
    print()

    while _running:
        try:
          
            async with AsyncSessionLocal() as db:
            
                active_events = await event_repository.get_active_events(db)

                total_processed = 0

                for event in active_events:
                    processed = await process_event_queue(
                        event_id=event.id,
                        event_name=event.name,
                    )
                    total_processed += processed

                if total_processed > 0:
                    print(
                        f"✅ Ciclo: {total_processed} usuarios procesados "
                        f"en {len(active_events)} evento(s) activo(s)"
                    )

        except Exception as e:
            print(f"❌ Error en ciclo del worker: {e}")

      
        await asyncio.sleep(settings.PROCESS_INTERVAL)

    print("👋 Worker finalizado")


def main():
   
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    print("=" * 60)
    print("  VIRTUAL QUEUE — Worker (Procesador de Cola)")
    print("=" * 60)

    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
