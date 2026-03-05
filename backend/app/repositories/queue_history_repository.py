
from typing import Optional
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


from app.models.queue_history import QueueHistory


async def record_entry(
    db: AsyncSession,
    user_id: str,
    event_id: str,
    initial_position: int,
) -> QueueHistory:
  
    record = QueueHistory(
        user_id=user_id,
        event_id=event_id,
        initial_position=initial_position,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record



async def record_allowed(db: AsyncSession, record_id: int) -> bool:
    result = await db.execute(
        update(QueueHistory)
        .where(QueueHistory.id == record_id)
        .values(allowed_at=datetime.utcnow())
    )
    await db.commit()
    return result.rowcount > 0


async def record_exit(
    db: AsyncSession,
    record_id: int,
    exit_reason: str,
) -> bool:

    result = await db.execute(
        select(QueueHistory).where(QueueHistory.id == record_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        return False

    now = datetime.utcnow()
    wait_seconds = int((now - record.entered_at).total_seconds())

    await db.execute(
        update(QueueHistory)
        .where(QueueHistory.id == record_id)
        .values(
            exited_at=now,
            exit_reason=exit_reason,
            wait_time_seconds=wait_seconds,
        )
    )
    await db.commit()
    return True


async def get_history_by_event(
    db: AsyncSession, event_id: str
) -> list[QueueHistory]:
   
    result = await db.execute(
        select(QueueHistory).where(QueueHistory.event_id == event_id)
    )
    return list(result.scalars().all())


async def get_active_record(
    db: AsyncSession, user_id: str, event_id: str
) -> Optional[QueueHistory]:
   
    result = await db.execute(
        select(QueueHistory)
        .where(QueueHistory.user_id == user_id)
        .where(QueueHistory.event_id == event_id)
        .where(QueueHistory.exited_at.is_(None))
    )
    return result.scalar_one_or_none()
