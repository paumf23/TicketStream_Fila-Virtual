from pydantic import BaseModel, Field

class EnterQueueRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        description="UUID del usuario que quiere entrar a la cola",
        examples=["user-550e8400-e29b-41d4-a716-446655440000"],
    )
    event_id: str = Field(
        ...,
        min_length=1,
        description="UUID del evento al cual quiere entrar",
        examples=["evt-123e4567-e89b-12d3-a456-426614174000"],
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del usuario",
        examples=["Juan"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Apellido del usuario",
        examples=["Pérez"],
    )

class QueuePositionRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        description="UUID del usuario",
    )
    event_id: str = Field(
        ...,
        min_length=1,
        description="UUID del evento",
    )

class LeaveQueueRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=1,
        description="UUID del usuario que quiere salir de la cola",
    )
    event_id: str = Field(
        ...,
        min_length=1,
        description="UUID del evento del cual quiere salir",
    )
