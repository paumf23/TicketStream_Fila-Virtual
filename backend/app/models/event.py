

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Text, DateTime, Numeric, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    name: Mapped[str] = mapped_column(String(255))

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    total_capacity: Mapped[int] = mapped_column(Integer)

    remaining_capacity: Mapped[int] = mapped_column(Integer)

 
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    
    currency: Mapped[str] = mapped_column(String(3), default="ARS")

    
    event_date: Mapped[datetime] = mapped_column(DateTime)

   
    sale_start: Mapped[datetime] = mapped_column(DateTime)
    
    sale_end: Mapped[datetime] = mapped_column(DateTime)

   
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "active", "sold_out", name="event_status"),
        default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} name={self.name} remaining={self.remaining_capacity}>"
