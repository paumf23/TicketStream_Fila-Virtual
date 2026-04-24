

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.event import CreateEventRequest
from app.schemas.responses import ErrorResponse, EventListResponse, EventResponse, EventStatsResponse
from app.services import event_service

router = APIRouter()


@router.get("/", response_model=EventListResponse)
async def list_all_events(db: AsyncSession = Depends(get_db)):
    events = await event_service.get_all_events(db)
    return {"events": events, "total": len(events)}


@router.get("/active", response_model=EventListResponse)
async def list_active_events(
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    events = await event_service.get_active_events(db, category)
    return {"events": events, "total": len(events)}


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    return await event_service.get_event_by_id(db, event_id)


@router.get(
    "/{event_id}/stats",
    response_model=EventStatsResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_event_stats(event_id: str, db: AsyncSession = Depends(get_db)):
    return await event_service.get_event_stats(db, event_id)


@router.post("/", status_code=201, response_model=EventResponse)
async def create_event(
    body: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
):
    return await event_service.create_event(
        db,
        name=body.name,
        description=body.description,
        image_url=body.image_url,
        total_capacity=body.total_capacity,
        price=body.price,
        event_date=body.event_date,
        sale_start=body.sale_start,
        sale_end=body.sale_end,
        currency=body.currency,
    )


@router.put(
    "/{event_id}/activate",
    response_model=EventResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def activate_event(event_id: str, db: AsyncSession = Depends(get_db)):
    return await event_service.activate_event(db, event_id)


@router.put(
    "/{event_id}/sold-out",
    response_model=EventResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def mark_sold_out(event_id: str, db: AsyncSession = Depends(get_db)):
    return await event_service.mark_sold_out(db, event_id)
