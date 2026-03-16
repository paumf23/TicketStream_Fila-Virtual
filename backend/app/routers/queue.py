

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.queue import EnterQueueRequest, LeaveQueueRequest
from app.schemas.responses import EnterQueueResponse, LeaveQueueResponse, QueuePositionResponse
from app.services import queue_service

router = APIRouter()


@router.post("/enter", status_code=201, response_model=EnterQueueResponse)
async def enter_queue(
    body: EnterQueueRequest,
    db: AsyncSession = Depends(get_db),
):
    return await queue_service.enter_queue(
        db,
        user_id=body.user_id,
        event_id=body.event_id,
        first_name=body.first_name,
        last_name=body.last_name,
    )


@router.get("/position", response_model=QueuePositionResponse)
async def get_position(
    user_id: str,
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await queue_service.get_position(
        db,
        user_id=user_id,
        event_id=event_id,
    )


@router.delete("/leave", response_model=LeaveQueueResponse)
async def leave_queue(
    body: LeaveQueueRequest,
    db: AsyncSession = Depends(get_db),
):
    return await queue_service.leave_queue(
        db,
        user_id=body.user_id,
        event_id=body.event_id,
    )
