

from datetime import datetime

from sqlalchemy import String, DateTime, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    ticket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tickets.id"), unique=True, index=True
    )

    amount: Mapped[float] = mapped_column(Numeric(10, 2))

    payment_method: Mapped[str] = mapped_column(
        SAEnum(
            "credit_card", "debit_card", "mercado_pago",
            name="payment_method"
        ),
    )

    status: Mapped[str] = mapped_column(
        SAEnum("completed", "failed", name="payment_status"),
        default="completed",
    )

    payment_reference: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Payment id={self.id} ticket={self.ticket_id} status={self.status}>"
