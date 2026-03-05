
# ═══════════════════════════════════════════════════════════════════════════════
# queue.py — Endpoints HTTP para la Cola de Espera
# ═══════════════════════════════════════════════════════════════════════════════


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services import queue_service



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




router = APIRouter()





@router.post("/enter", status_code=201)
async def enter_queue(
    body: EnterQueueRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await queue_service.enter_queue(
            db,
            user_id=body.user_id,
            event_id=body.event_id,
            first_name=body.first_name,
            last_name=body.last_name,
        )
        return result
    except queue_service.EventNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except queue_service.EventNotActiveError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except queue_service.AlreadyInQueueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/position")
async def get_position(
    user_id: str,
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    
    try:
        result = await queue_service.get_position(
            db,
            user_id=user_id,
            event_id=event_id,
        )
        return result
    except queue_service.NotInQueueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/leave")
async def leave_queue(
    body: LeaveQueueRequest,
    db: AsyncSession = Depends(get_db),
):
   
    try:
        result = await queue_service.leave_queue(
            db,
            user_id=body.user_id,
            event_id=body.event_id,
        )
        return result
    except queue_service.NotInQueueError as e:
        raise HTTPException(status_code=404, detail=str(e))
