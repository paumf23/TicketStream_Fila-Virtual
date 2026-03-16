from pydantic import BaseModel, Field


class SimulateLoadRequest(BaseModel):
    event_id: str = Field(
        ...,
        min_length=1,
        description="UUID del evento al cual simular usuarios",
        examples=["evt-123e4567-e89b-12d3-a456-426614174000"],
    )
    num_users: int = Field(
        ...,
        gt=0,
        le=10000,
        description="Cantidad de usuarios ficticios a generar (máximo 10000)",
        examples=[100],
    )
