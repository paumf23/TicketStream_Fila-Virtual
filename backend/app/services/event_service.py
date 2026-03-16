
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BadRequestError, ConflictError, NotFoundError, ValidationError
from app.repositories import event_repository, redis_repository


class EventNotFoundError(NotFoundError):
    pass


class EventAlreadyActiveError(ConflictError):
    pass


class InvalidEventStatusError(BadRequestError):
    pass


class InvalidEventDataError(ValidationError):
    pass


async def get_all_events(db: AsyncSession) -> list[dict]:

    events = await event_repository.get_all_events(db)

    return [_event_to_dict(e) for e in events]


async def get_active_events(db: AsyncSession) -> list[dict]:

    events = await event_repository.get_active_events(db)
    return [_event_to_dict(e) for e in events]


async def get_event_by_id(db: AsyncSession, event_id: str) -> dict:

    event = await event_repository.get_event_by_id(db, event_id)
    if event is None:
        raise EventNotFoundError(
            f"Evento {event_id} no encontrado en la base de datos"
        )

    return _event_to_dict(event)


async def create_event(
    db: AsyncSession,
    name: str,
    description: str | None,
    image_url: str | None,
    total_capacity: int,
    price: float,
    event_date: datetime,
    sale_start: datetime,
    sale_end: datetime,
    currency: str = "ARS",
) -> dict:

    if total_capacity <= 0:
        raise InvalidEventDataError(
            f"La capacidad total debe ser mayor a 0, se recibió: {total_capacity}"
        )


    if price < 0:
        raise InvalidEventDataError(
            f"El precio no puede ser negativo, se recibió: {price}"
        )


    if sale_start >= sale_end:
        raise InvalidEventDataError(
            f"La fecha de inicio de venta ({sale_start}) debe ser anterior "
            f"a la fecha de fin de venta ({sale_end})"
        )


    if event_date <= sale_end:
        raise InvalidEventDataError(
            f"La fecha del evento ({event_date}) debe ser posterior "
            f"al cierre de ventas ({sale_end})"
        )


    event_data = {
        "name": name,
        "description": description,
        "image_url": image_url,
        "total_capacity": total_capacity,
        "remaining_capacity": total_capacity,
        "price": price,
        "currency": currency,
        "event_date": event_date,
        "sale_start": sale_start,
        "sale_end": sale_end,
        "status": "draft",
    }


    event = await event_repository.create_event(db, event_data)



    return _event_to_dict(event)




async def activate_event(db: AsyncSession, event_id: str) -> dict:
    event = await event_repository.get_event_by_id(db, event_id)
    if event is None:
        raise EventNotFoundError(f"Evento {event_id} no encontrado")

    if event.status == "active":
        raise EventAlreadyActiveError(
            f"Evento {event_id} ya se encuentra activo"
        )

    if event.status != "draft":
        raise InvalidEventStatusError(
            f"No se puede activar el evento {event_id} "
            f"desde el estado '{event.status}'. "
            f"Solo eventos en estado 'draft' pueden ser activados."
        )


    updated = await event_repository.update_event_status(db, event_id, "active")
    if not updated:
        raise InvalidEventStatusError(
            f"No se pudo actualizar el estado del evento {event_id}. "
            f"Posible modificación concurrente."
        )



    updated_event = await event_repository.get_event_by_id(db, event_id)
    return _event_to_dict(updated_event)





async def mark_sold_out(db: AsyncSession, event_id: str) -> dict:

    event = await event_repository.get_event_by_id(db, event_id)
    if event is None:
        raise EventNotFoundError(f"Evento {event_id} no encontrado")


    if event.status != "active":
        raise InvalidEventStatusError(
            f"No se puede marcar como sold_out el evento {event_id} "
            f"desde el estado '{event.status}'. "
            f"Solo eventos en estado 'active' pueden agotarse."
        )


    updated = await event_repository.update_event_status(db, event_id, "sold_out")
    if not updated:
        raise InvalidEventStatusError(
            f"No se pudo marcar como sold_out el evento {event_id}. "
            f"Posible modificación concurrente."
        )

    await redis_repository.publish(
        event_id,
        f"EVENT_SOLD_OUT:{event_id}"
    )


    updated_event = await event_repository.get_event_by_id(db, event_id)
    return _event_to_dict(updated_event)


async def get_event_stats(db: AsyncSession, event_id: str) -> dict:

    event = await event_repository.get_event_by_id(db, event_id)
    if event is None:
        raise EventNotFoundError(f"Evento {event_id} no encontrado")

    queue_length = await redis_repository.queue_length(event_id)

    tickets_sold = event.total_capacity - event.remaining_capacity

    occupancy_percentage = round(
        (tickets_sold / max(1, event.total_capacity)) * 100, 2
    )

    result = _event_to_dict(event)
    result["stats"] = {
        "tickets_sold": tickets_sold,
        "remaining_capacity": event.remaining_capacity,
        "occupancy_percentage": occupancy_percentage,
        "queue_length": queue_length,
    }
    return result



def _event_to_dict(event) -> dict:
    return {
        "event_id": event.id,
        "name": event.name,
        "description": event.description,
        "image_url": event.image_url,
        "total_capacity": event.total_capacity,
        "remaining_capacity": event.remaining_capacity,
        "price": float(event.price),
        "currency": event.currency,
        "event_date": str(event.event_date),
        "sale_start": str(event.sale_start),
        "sale_end": str(event.sale_end),
        "status": event.status,
        "created_at": str(event.created_at),
        "updated_at": str(event.updated_at),
    }
