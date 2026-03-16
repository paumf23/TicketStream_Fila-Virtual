

from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


async def get_all_events(db: AsyncSession) -> list[Event]:
    result = await db.execute(select(Event))
    return list(result.scalars().all())


#
async def get_active_events(db: AsyncSession) -> list[Event]:
    result = await db.execute(
        select(Event).where(Event.status == "active")
    )
    return list(result.scalars().all())



async def get_event_by_id(db: AsyncSession, event_id: str) -> Event | None:
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    return result.scalar_one_or_none()



async def create_event(db: AsyncSession, event_data: dict) -> Event:
    event = Event(id=str(uuid4()), **event_data)
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event



async def update_remaining_capacity(
    db: AsyncSession, event_id: str, decrement: int = 1
) -> bool:
    result = await db.execute(
        update(Event)
        .where(Event.id == event_id)
        .where(Event.remaining_capacity >= decrement)
        .values(remaining_capacity=Event.remaining_capacity - decrement)
    )
    await db.flush()
    return result.rowcount > 0



async def update_event_status(
    db: AsyncSession, event_id: str, new_status: str
) -> bool:
    result = await db.execute(
        update(Event)
        .where(Event.id == event_id)
        .values(status=new_status)
    )
    await db.flush()
    return result.rowcount > 0
