

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, DateTime, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

  
    buyer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("buyers.id"), index=True
    )

   
    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id"), index=True
    )

   
    ticket_code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )

   
    price_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    status: Mapped[str] = mapped_column(
        SAEnum("pending", "confirmed", "used", name="ticket_status"),
        default="pending",
    )


    purchased_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} code={self.ticket_code} buyer={self.buyer_id} status={self.status}>"
