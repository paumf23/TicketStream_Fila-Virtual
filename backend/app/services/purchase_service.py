# ═══════════════════════════════════════════════════════════════════════════════
# Lógica de negocio para compra de tickets
# Proporciona métodos para iniciar, obtener y validar compras
# ═══════════════════════════════════════════════════════════════════════════════       


import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.repositories import (
    buyer_repository,
    event_repository,
    payment_repository,
    queue_history_repository,
    redis_repository,
    ticket_repository,
)

logger = logging.getLogger("app.services.purchase")



class UserNotAllowedError(ForbiddenError):
    pass


class InsufficientCapacityError(ConflictError):
    pass


class TicketNotFoundError(NotFoundError):
    pass


class TicketAlreadyProcessedError(ConflictError):
    pass



async def initiate_purchase(
    db: AsyncSession,
    user_id: str,
    event_id: str,
    first_name: str,
    last_name: str,
    dni: str,
    email: str,
    payment_method: str,
    payment_provider: str | None = None,
    quantity: int = 1,
) -> dict:
    logger.info(f"Iniciando flujo de compra: Usuario {user_id} para evento {event_id} (Cantidad: {quantity})")

    allowed = await redis_repository.is_allowed(event_id, user_id)
    if not allowed:
        raise UserNotAllowedError(
            f"Usuario {user_id} no está autorizado para comprar en evento {event_id}. "
            f"Debe esperar en la cola hasta ser habilitado por el sistema."
        )

    event = await event_repository.get_event_by_id(db, event_id)
    if event is None:
        await redis_repository.remove_allowed(event_id, user_id)
        raise TicketNotFoundError(f"Evento {event_id} no encontrado")

    total_price = float(event.price) * quantity


    async with db.begin_nested():
        capacity_reserved = await event_repository.update_remaining_capacity(
            db, event_id, decrement=quantity
        )

        if not capacity_reserved:
            raise InsufficientCapacityError(
                f"Evento {event_id} sin capacidad suficiente para {quantity} entradas."
            )

        buyer = await buyer_repository.create_buyer(
            db,
            first_name=first_name,
            last_name=last_name,
            dni=dni,
            email=email,
        )

        ticket = await ticket_repository.create_ticket(
            db,
            buyer_id=buyer.id,
            event_id=event_id,
            price_paid=total_price,
            quantity=quantity,
        )

        payment = await payment_repository.create_payment(
            db,
            ticket_id=ticket.id,
            amount=total_price,
            payment_method=payment_method,
            payment_provider=payment_provider,
        )


        await ticket_repository.confirm_ticket(db, ticket.id)


    await db.commit()

    
    try:
        active_record = await queue_history_repository.get_active_record(
            db, user_id, event_id
        )
        if active_record is not None:
            await queue_history_repository.record_exit(
                db, active_record.id, exit_reason="purchased"
            )
            await db.commit()
    except Exception as e:
        logger.warning(f"No se pudo registrar la salida de cola para {user_id}: {e}")

    
    await redis_repository.remove_allowed(event_id, user_id)

    logger.info(f"Compra finalizada con éxito: Ticket {ticket.id} para usuario {user_id}")

    await db.refresh(ticket)

    return {
        "status": "success",
        "message": "Operación exitosa, gracias por su compra.",
        "ticket_id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "quantity": ticket.quantity,
        "buyer_id": buyer.id,
        "buyer_name": f"{first_name} {last_name}",
        "event_id": event_id,
        "event_name": event.name,
        "price_paid": float(ticket.price_paid),
        "ticket_status": ticket.status,
        "payment_reference": payment.payment_reference,
        "purchased_at": str(ticket.purchased_at),
        "confirmed_at": str(ticket.confirmed_at),
    }



async def get_ticket_detail(
    db: AsyncSession,
    ticket_id: str,
) -> dict:

    ticket = await ticket_repository.get_ticket_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(
            f"Ticket {ticket_id} no encontrado en la base de datos"
        )

    event = await event_repository.get_event_by_id(db, ticket.event_id)
    buyer = await buyer_repository.get_buyer_by_id(db, ticket.buyer_id)

    payment = await payment_repository.get_payment_by_ticket_id(db, ticket_id)

    return {
        "ticket_id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "buyer_id": ticket.buyer_id,
        "buyer_name": f"{buyer.first_name} {buyer.last_name}" if buyer else None,
        "event_id": ticket.event_id,
        "event_name": event.name if event else "Evento no disponible",
        "event_date": str(event.event_date) if event else None,
        "price_paid": float(ticket.price_paid),
        "status": ticket.status,
        "payment_reference": payment.payment_reference if payment else None,
        "payment_method": payment.payment_method if payment else None,
        "payment_provider": payment.payment_provider if payment else None,
        "purchased_at": str(ticket.purchased_at),
        "confirmed_at": str(ticket.confirmed_at) if ticket.confirmed_at else None,
    }
