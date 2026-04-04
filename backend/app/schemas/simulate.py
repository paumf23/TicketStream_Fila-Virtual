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


class AdvancedSimulateRequest(BaseModel):
    event_id: str = Field(..., description="UUID del evento")
    num_users: int = Field(..., gt=0, le=10000, description="Población total simulada")
    include_me: bool = Field(default=False, description="Si se debe incluir al usuario real")
    user_id: str | None = Field(default=None, description="ID del usuario real si include_me es true")
    target_position: int | None = Field(default=None, gt=0, description="Posición objetivo del usuario real")
    processing_speed: int = Field(default=60, gt=0, description="Usuarios por minuto")
    abandon_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="Tasa de abandono (0-100%)")
