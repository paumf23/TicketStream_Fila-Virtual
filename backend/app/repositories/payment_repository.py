
import secrets
from uuid import uuid4

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
    payment_provider: str | None = None,
    status: str = "completed",
) -> Payment:

    payment = Payment(
        id=str(uuid4()),
        ticket_id=ticket_id,
        amount=amount,
        payment_method=payment_method,
        payment_provider=payment_provider,
        status=status,
        payment_reference=_generate_payment_reference(),
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return payment


async def get_payment_by_ticket_id(
    db: AsyncSession, ticket_id: str
) -> Payment | None:
    result = await db.execute(
        select(Payment).where(Payment.ticket_id == ticket_id)
    )
    return result.scalar_one_or_none()
