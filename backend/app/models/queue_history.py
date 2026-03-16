

from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class QueueHistory(Base):
    __tablename__ = "queue_history"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    user_id: Mapped[str] = mapped_column(
        String(36), index=True
    )

    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id"), index=True
    )

    initial_position: Mapped[int] = mapped_column(Integer)

    
    entered_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    
    allowed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    exited_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    
    exit_reason: Mapped[str | None] = mapped_column(
        SAEnum("purchased", "expired", "abandoned", "disconnected", name="exit_reason"),
        nullable=True,
    )

   
    wait_time_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    def __repr__(self) -> str:
        return f"<QueueHistory user={self.user_id} event={self.event_id} exit={self.exit_reason}>"
