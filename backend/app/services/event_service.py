# ═══════════════════════════════════════════════════════════════════════════════
# Servicio de Eventos
#Gestiona la lógica de negocio de los eventos
#Proporciona métodos para obtener, crear, actualizar y eliminar eventos
#Proporciona métodos para obtener estadísticas de los eventos
# ═══════════════════════════════════════════════════════════════════════════════   



from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BadRequestError, ConflictError, NotFoundError, ValidationError
from app.repositories import event_repository, queue_history_repository, redis_repository


class EventNotFoundError(NotFoundError):
    pass


class EventAlreadyActiveError(ConflictError):
    pass


class InvalidEventStatusError(BadRequestError):
    pass


class InvalidEventDataError(ValidationError):
    pass


async def get_all_events(db: AsyncSession) -> list[dict]:
    """Obtiene todos los eventos registrados en el sistema, sin importar su estado."""

    events = await event_repository.get_all_events(db)

    return [_event_to_dict(e) for e in events]


async def get_active_events(db: AsyncSession, category: str | None = None) -> list[dict]:
    """Obtiene una lista de todos los eventos que se encuentran en estado 'active'."""
    events = await event_repository.get_active_events(db, category)
    return [_event_to_dict(e) for e in events]


async def get_event_by_id(db: AsyncSession, event_id: str) -> dict:
    """Obtiene los detalles de un evento específico por su ID."""

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
    category: str | None = None,
) -> dict:
    """
    Crea un nuevo evento en estado 'draft'.
    Valida las capacidades, precios y fechas antes de su creación.
    """

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
        "category": category,
    }


    event = await event_repository.create_event(db, event_data)
    await db.commit()

    return _event_to_dict(event)




async def activate_event(db: AsyncSession, event_id: str) -> dict:
    """
    Cambia el estado de un evento de 'draft' a 'active'.
    Solo los eventos en estado borrador pueden ser activados.
    """
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
    await db.commit()
    return _event_to_dict(updated_event)





async def mark_sold_out(db: AsyncSession, event_id: str) -> dict:
    """
    Marca un evento activo como 'sold_out' cuando no quedan entradas.
    Publica una notificación global en Redis para informar a los usuarios.
    """

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
    await db.commit()
    return _event_to_dict(updated_event)


async def get_event_stats(db: AsyncSession, event_id: str) -> dict:
    """
    Recopila métricas en tiempo real de un evento fusionando datos 
    estáticos de la DB y dinámicos cacheados en Redis.
    """

    event = await event_repository.get_event_by_id(db, event_id)
    if event is None:
        raise EventNotFoundError(f"Evento {event_id} no encontrado")

    queue_length = await redis_repository.queue_length(event_id)
    peak_queue = await redis_repository.get_peak_queue_length(event_id)
    avg_wait = await queue_history_repository.get_avg_wait_time(db, event_id)
    
    abandoned_count = await redis_repository.get_abandoned_count(event_id)
    processed_count = await redis_repository.get_processed_count(event_id)
    # Recuperar métricas dinámicas de simulación desde el hash en Redis
    last_stats = await redis_repository.get_event_stats_snapshot(event_id)
    
    effort = float(last_stats.get("effort", 0.0))
    trend = int(last_stats.get("trend", 0))
    last_jump = int(last_stats.get("last_jump", 0))
    incoming_rate = int(last_stats.get("incoming_rate", 0))
    processed_rate = int(last_stats.get("processed_rate", 0))
    

    throughput = last_jump

    tickets_sold = event.total_capacity - event.remaining_capacity
    redis_revenue = float(last_stats.get("revenue", 0.0))
    db_revenue = float(event.price) * tickets_sold
    revenue = max(redis_revenue, db_revenue)

    occupancy_percentage = round(
        (tickets_sold / max(1, event.total_capacity)) * 100, 2
    )

    result = _event_to_dict(event)
    result["stats"] = {
        "tickets_sold": tickets_sold,
        "remaining_capacity": event.remaining_capacity,
        "occupancy_percentage": occupancy_percentage,
        "queue_length": queue_length,
        "revenue": revenue,
        "avg_wait_time_seconds": avg_wait,
        "peak_queue_length": peak_queue,
        "abandoned_count": abandoned_count,
        "processed_count": processed_count,
        "throughput": throughput,
        "effort": effort,
        "trend": trend,
        "last_jump": last_jump,
        "incoming_rate": incoming_rate,
        "processed_rate": processed_rate
    }
    return result



def _event_to_dict(event) -> dict:
    """
    Convierte dinámicamente el modelo SQLAlchemy a diccionario para evitar desincronización.
    Extrae todas las columnas automáticamente, por lo que si se agregan campos a la BD, 
    se incluirán sin necesidad de actualizar esta función.
    """
    # Extraer dinámicamente todas las columnas del modelo SQLAlchemy
    result = {column.name: getattr(event, column.name) for column in event.__table__.columns}
    
    # Renombrar 'id' a 'event_id' para mantener compatibilidad con el Schema de respuesta
    result["event_id"] = result.pop("id", None)
    
    # Formatear fechas y números (Decimals a float)
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = str(value)
        elif value is not None and not isinstance(value, (int, str, float, bool, list, dict)):
            result[key] = float(value)
            
    return result
