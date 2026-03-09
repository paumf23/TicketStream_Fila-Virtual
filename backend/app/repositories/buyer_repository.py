
from uuid import uuid4
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.buyer import Buyer


async def create_buyer(
    db: AsyncSession,
    first_name: str,
    last_name: str,
    dni: str,
    email: str,
) -> Buyer:

    buyer = Buyer(
        id=str(uuid4()),
        first_name=first_name,
        last_name=last_name,
        dni=dni,
        email=email,
    )
    db.add(buyer)
    await db.flush()
    await db.refresh(buyer)
    return buyer


async def get_buyer_by_id(
    db: AsyncSession, buyer_id: str
) -> Optional[Buyer]:
    result = await db.execute(
        select(Buyer).where(Buyer.id == buyer_id)
    )
    return result.scalar_one_or_none()


async def get_buyer_by_dni(
    db: AsyncSession, dni: str
) -> Optional[Buyer]:
    result = await db.execute(
        select(Buyer).where(Buyer.dni == dni)
    )
    return result.scalar_one_or_none()
