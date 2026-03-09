

from uuid import uuid4
import secrets

from typing import Optional
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket


def _generate_ticket_code() -> str:
    return f"VQ-{secrets.token_hex(6).upper()}"


async def create_ticket(
    db: AsyncSession,
    buyer_id: str,
    event_id: str,
    price_paid: float,
    quantity: int = 1,
) -> Ticket:

    ticket = Ticket(
        id=str(uuid4()),
        buyer_id=buyer_id,
        event_id=event_id,
        ticket_code=_generate_ticket_code(),
        price_paid=price_paid,
        quantity=quantity,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return ticket



async def get_ticket_by_id(db: AsyncSession, ticket_id: str) -> Optional[Ticket]:
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def get_ticket_by_code(db: AsyncSession, ticket_code: str) -> Optional[Ticket]:
    result = await db.execute(
        select(Ticket).where(Ticket.ticket_code == ticket_code)
    )
    return result.scalar_one_or_none()


async def get_tickets_by_buyer(db: AsyncSession, buyer_id: str) -> list[Ticket]:
    result = await db.execute(
        select(Ticket).where(Ticket.buyer_id == buyer_id)
    )
    return list(result.scalars().all())


async def get_tickets_by_event(db: AsyncSession, event_id: str) -> list[Ticket]:
    result = await db.execute(
        select(Ticket).where(Ticket.event_id == event_id)
    )
    return list(result.scalars().all())




async def confirm_ticket(db: AsyncSession, ticket_id: str) -> bool:
    result = await db.execute(
        update(Ticket)
        .where(Ticket.id == ticket_id)
        .where(Ticket.status == "pending")
        .values(status="confirmed", confirmed_at=datetime.utcnow())
    )
    await db.flush()
    return result.rowcount > 0

