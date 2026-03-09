from typing import Optional
from pydantic import BaseModel, Field

class PurchaseRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        description="UUID del usuario en la cola",
        examples=["user-550e8400-e29b-41d4-a716-446655440000"],
    )
    event_id: str = Field(
        ...,
        min_length=1,
        description="UUID del evento para el cual compra",
        examples=["evt-123e4567-e89b-12d3-a456-426614174000"],
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del comprador",
        examples=["Juan"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Apellido del comprador",
        examples=["Pérez"],
    )
    dni: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="DNI del comprador",
        examples=["35123456"],
    )
    email: str = Field(
        ...,
        min_length=1,
        description="Email del comprador",
        examples=["juan.perez@email.com"],
    )
    payment_method: str = Field(
        ...,
        description="Método de pago",
        examples=["credit_card", "mercadopago"],
    )
    card_number: Optional[str] = Field(
        None,
        description="Número de tarjeta ficticio (para simulación)",
        examples=["4500 0000 0000 0001"],
    )
    quantity: int = Field(
        1,
        gt=0,
        le=10,
        description="Cantidad de entradas a comprar (máximo 10)",
        examples=[2],
    )
