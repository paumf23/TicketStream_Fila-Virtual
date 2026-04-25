# ═══════════════════════════════════════════════════════════════════════════════
# Lógica de negocio para la cola
# Proporciona métodos para entrar, salir y obtener la posición en la cola
# ═══════════════════════════════════════════════════════════════════════════════   



import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.repositories import event_repository, queue_history_repository, redis_repository

logger = logging.getLogger("app.services.queue")



class EventNotFoundError(NotFoundError):
    pass


class EventNotActiveError(BadRequestError):
    pass


class AlreadyInQueueError(ConflictError):
    pass


class NotInQueueError(NotFoundError):
    pass



async def enter_queue(
    db: AsyncSession,
    user_id: str,
    event_id: str,
    first_name: str,
    last_name: str,
) -> dict:

    event = await event_repository.get_event_by_id(db, event_id)
    if event is None:
        raise EventNotFoundError(f"Evento {event_id} no encontrado")


    if event.status != "active":
        raise EventNotActiveError(
            f"Evento {event_id} no está activo (status: {event.status})"
        )


    existing = await queue_history_repository.get_active_record(
        db, user_id, event_id
    )

    if existing is not None:
        raise AlreadyInQueueError(
            f"Usuario {user_id} ya está en la cola del evento {event_id}"
        )

    await redis_repository.set_user_name(user_id, first_name, last_name)

    position = await redis_repository.queue_push(event_id, user_id)
    logger.info(f"Usuario {user_id} ingresó a la cola del evento {event_id}. Posición: {position}")


    history_record = await queue_history_repository.record_entry(
        db, user_id, event_id, position
    )
    await db.commit()


    return {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "event_id": event_id,
        "position": position,
        "queue_length": position,
        "history_record_id": history_record.id,
        "event_name": event.name,
    }



async def get_position(
    db: AsyncSession,
    user_id: str,
    event_id: str,
) -> dict:

    position = await redis_repository.queue_position(event_id, user_id)
    if position is None:
        raise NotInQueueError(
            f"Usuario {user_id} no está en la cola del evento {event_id}"
        )


    total = await redis_repository.queue_length(event_id)

   
    config = await redis_repository.get_event_config(event_id)
    speed = config.get("speed", 60)

    return {
        "user_id": user_id,
        "event_id": event_id,
        "position": position + 1,
        "queue_length": total,
        "estimated_wait": await _estimate_wait(position, speed),
    }


async def _estimate_wait(position: int, speed: int) -> str:
    if speed <= 0:
        return "Pendiente..."
    
    minutes = position / speed
    
    if minutes < 0.5:
        return "Pocos segundos"
    if minutes < 1:
        return "Menos de 1 minuto"
    
    return f"~{int(minutes) + 1} minutos"



async def leave_queue(
    db: AsyncSession,
    user_id: str,
    event_id: str,
) -> dict:

    existing = await queue_history_repository.get_active_record(
        db, user_id, event_id
    )
    if existing is None:
        raise NotInQueueError(
            f"Usuario {user_id} no está en la cola del evento {event_id}"
        )

    await redis_repository.queue_remove(event_id, user_id)
    logger.info(f"Usuario {user_id} abandonó la cola del evento {event_id}")


    await queue_history_repository.record_exit(
        db, existing.id, exit_reason="abandoned"
    )
    await db.commit()

    return {
        "user_id": user_id,
        "event_id": event_id,
        "status": "left",
    }
