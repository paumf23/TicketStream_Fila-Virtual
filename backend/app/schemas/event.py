from datetime import datetime

from pydantic import BaseModel, Field


class CreateEventRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nombre del evento",
        examples=["Lollapalooza Argentina 2026"],
    )
    description: str | None = Field(
        default=None,
        description="Descripción opcional del evento",
    )
    image_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL de la imagen del evento (para las cards del frontend)",
        examples=["https://ejemplo.com/images/lollapalooza-2026.jpg"],
    )
    total_capacity: int = Field(
        ...,
        gt=0,
        description="Capacidad total de entradas disponibles",
        examples=[10000],
    )
    price: float = Field(
        ...,
        ge=0,
        description="Precio unitario por entrada (0 = gratuito)",
        examples=[5000.00],
    )
    event_date: datetime = Field(
        ...,
        description="Fecha y hora del evento",
    )
    sale_start: datetime = Field(
        ...,
        description="Inicio de la ventana de venta",
    )
    sale_end: datetime = Field(
        ...,
        description="Fin de la ventana de venta",
    )
    currency: str = Field(
        default="ARS",
        max_length=3,
        description="Código de moneda ISO 4217",
    )
