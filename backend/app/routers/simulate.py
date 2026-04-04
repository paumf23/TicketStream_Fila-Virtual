
# ═══════════════════════════════════════════════════════════════════════════════
# simulate.py — Endpoint de Simulación de Carga
# ═══════════════════════════════════════════════════════════════════════════════


import random
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.exceptions import BadRequestError, NotFoundError
from app.repositories import event_repository, redis_repository
from app.schemas.responses import SimulateLoadResponse
from app.schemas.simulate import SimulateLoadRequest, AdvancedSimulateRequest

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



router = APIRouter()


@router.post("/load", status_code=201, response_model=SimulateLoadResponse)
async def simulate_load(
    body: SimulateLoadRequest,
    db: AsyncSession = Depends(get_db),
):

    event = await event_repository.get_event_by_id(db, body.event_id)
    if event is None:
        raise NotFoundError(f"Evento {body.event_id} no encontrado")
    if event.status != "active":
        raise BadRequestError(
            f"Evento {body.event_id} no está activo (status: {event.status})"
        )

    created_users = []
    for _ in range(body.num_users):
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


@router.post("/advanced", status_code=201)
async def simulate_advanced(
    body: AdvancedSimulateRequest,
    db: AsyncSession = Depends(get_db),
):
    event = await event_repository.get_event_by_id(db, body.event_id)
    if event is None:
        raise NotFoundError(f"Evento {body.event_id} no encontrado")

    # 1. Limpiar todo rastro previo PRIMERO
    await redis_repository.clear_queue(body.event_id)
    await redis_repository.redis_pool.delete(f"event:{body.event_id}:stats")
    await redis_repository.redis_pool.delete(f"event:{body.event_id}:processed")
    await redis_repository.redis_pool.delete(f"event:{body.event_id}:abandoned")

    # 2. Guardar configuración de simulación (velocidad y abandono)
    await redis_repository.set_event_config(
        body.event_id, body.processing_speed, body.abandon_rate
    )
    
    # 3. Guardar snapshot inicial de datos del evento
    await redis_repository.redis_pool.hset(
        f"event:{body.event_id}:stats",
        mapping={
            "total_capacity": event.total_capacity,
            "remaining_capacity": event.remaining_capacity,
            "price": float(event.price),
        }
    )

    # 4. Registrar simulación activa en Redis
    await redis_repository.add_active_simulation(body.event_id)

    # Preparar el pool de IDs
    total_simulated = body.num_users
    if body.include_me:
        total_simulated -= 1
    
    # Calcular cuántos van antes de mí
    target_pos = body.target_position or (total_simulated // 2)
    # No podemos estar en una posición mayor al total
    target_pos = min(target_pos, total_simulated + 1)
    
    users_before = target_pos - 1
    users_after = total_simulated - users_before

    all_user_ids = []
    
    # Usuarios antes
    for _ in range(users_before):
        uid = f"sim-{uuid.uuid4().hex[:10]}"
        all_user_ids.append(uid)
    
    # Yo
    if body.include_me and body.user_id:
        all_user_ids.append(body.user_id)
    
    # Usuarios después
    for _ in range(max(0, users_after)):
        uid = f"sim-{uuid.uuid4().hex[:10]}"
        all_user_ids.append(uid)

    # Ejecutar el push masivo
    await redis_repository.bulk_push(body.event_id, all_user_ids)

    return {
        "status": "success",
        "message": f"Simulación iniciada con {len(all_user_ids)} usuarios",
        "target_position": target_pos if body.include_me else None,
        "config": {
            "speed": body.processing_speed,
            "abandon_rate": body.abandon_rate
        }
    }
