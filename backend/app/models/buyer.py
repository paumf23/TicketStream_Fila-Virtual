

from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Buyer(Base):
    __tablename__ = "buyers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    first_name: Mapped[str] = mapped_column(String(100))

    last_name: Mapped[str] = mapped_column(String(100))

    dni: Mapped[str] = mapped_column(
        String(20), index=True
    )

    email: Mapped[str] = mapped_column(
        String(100), index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Buyer id={self.id} name={self.first_name} {self.last_name}>"
