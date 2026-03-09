
# ═══════════════════════════════════════════════════════════════════════════════
# queue.py — Endpoints HTTP para la Cola de Espera
# ═══════════════════════════════════════════════════════════════════════════════


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services import queue_service



from app.schemas.queue import EnterQueueRequest, QueuePositionRequest, LeaveQueueRequest




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
