
# ═══════════════════════════════════════════════════════════════════════════════
# simulate.py — Endpoint de Simulación de Carga
# ═══════════════════════════════════════════════════════════════════════════════


import uuid
import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.repositories import redis_repository
from app.repositories import event_repository


FIRST_NAMES = [
    "Martín", "Lucía", "Santiago", "Valentina", "Mateo",
    "Sofía", "Benjamín", "Catalina", "Joaquín", "Emilia",
    "Tomás", "Isabella", "Agustín", "Camila", "Felipe",
    "Julieta", "Nicolás", "Florencia", "Thiago", "Renata",
    "Facundo", "Milagros", "Lautaro", "Candela", "Bautista",
    "Pilar", "Ignacio", "Rocío", "Manuel", "Abril",
]

LAST_NAMES = [
    "González", "Rodríguez", "Martínez", "López", "García",
    "Pérez", "Fernández", "Díaz", "Romero", "Alvarez",
    "Torres", "Ruiz", "Ramírez", "Flores", "Herrera",
    "Medina", "Castro", "Vargas", "Morales", "Gutiérrez",
    "Sánchez", "Ortiz", "Silva", "Molina", "Acosta",
    "Rojas", "Cabrera", "Núñez", "Peralta", "Figueroa",
]


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


router = APIRouter()


@router.post("/load", status_code=201)
async def simulate_load(
    body: SimulateLoadRequest,
    db: AsyncSession = Depends(get_db),
):

    event = await event_repository.get_event_by_id(db, body.event_id)
    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Evento {body.event_id} no encontrado",
        )
    if event.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Evento {body.event_id} no está activo (status: {event.status})",
        )

    created_users = []
    for i in range(body.num_users):
        user_id = f"sim-{uuid.uuid4().hex[:12]}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        await redis_repository.set_user_name(user_id, first_name, last_name)
        await redis_repository.queue_push(body.event_id, user_id)
        created_users.append({
            "user_id": user_id,
            "name": f"{first_name} {last_name}",
        })

    queue_length = await redis_repository.queue_length(body.event_id)

    return {
        "event_id": body.event_id,
        "event_name": event.name,
        "users_created": len(created_users),
        "queue_length": queue_length,
        "sample_users": created_users[:5],
    }
