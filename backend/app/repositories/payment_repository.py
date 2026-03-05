
from uuid import uuid4
import secrets
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


def _generate_payment_reference() -> str:
    return f"PAY-{secrets.token_hex(8).upper()}"


async def create_payment(
    db: AsyncSession,
    ticket_id: str,
    amount: float,
    payment_method: str,
    status: str = "completed",
) -> Payment:

    payment = Payment(
        id=str(uuid4()),
        ticket_id=ticket_id,
        amount=amount,
        payment_method=payment_method,
        status=status,
        payment_reference=_generate_payment_reference(),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payment_by_ticket_id(
    db: AsyncSession, ticket_id: str
) -> Optional[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.ticket_id == ticket_id)
    )
    return result.scalar_one_or_none()
