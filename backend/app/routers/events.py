
# ═══════════════════════════════════════════════════════════════════════════════
# events.py — Endpoints HTTP para Gestión de Eventos
# ═══════════════════════════════════════════════════════════════════════════════

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services import event_service


class CreateEventRequest(BaseModel):

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nombre del evento",
        examples=["Lollapalooza Argentina 2026"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Descripción opcional del evento",
    )
    image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL de la imagen del evento (para las cards del frontend)",
        examples=["https://ejemplo.com/images/lollapalooza-2026.jpg"],
    )
    total_capacity: int = Field(
        ...,
        gt=0,
        description="Capacidad total de entradas disponibles",
        examples=[10000],
    )
    price: float = Field(
        ...,
        ge=0,
        description="Precio unitario por entrada (0 = gratuito)",
        examples=[5000.00],
    )
    event_date: datetime = Field(
        ...,
        description="Fecha y hora del evento",
    )
    sale_start: datetime = Field(
        ...,
        description="Inicio de la ventana de venta",
    )
    sale_end: datetime = Field(
        ...,
        description="Fin de la ventana de venta",
    )
    currency: str = Field(
        default="ARS",
        max_length=3,
        description="Código de moneda ISO 4217",
    )





# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE CONSULTA (GET)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/")
async def list_all_events(db: AsyncSession = Depends(get_db)):
    events = await event_service.get_all_events(db)
    return {"events": events, "total": len(events)}


@router.get("/active")
async def list_active_events(db: AsyncSession = Depends(get_db)):
    events = await event_service.get_active_events(db)
    return {"events": events, "total": len(events)}


@router.get("/{event_id}")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
   
    try:
        event = await event_service.get_event_by_id(db, event_id)
        return event
    except event_service.EventNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{event_id}/stats")
async def get_event_stats(event_id: str, db: AsyncSession = Depends(get_db)):
   
    try:
        stats = await event_service.get_event_stats(db, event_id)
        return stats
    except event_service.EventNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT DE CREACIÓN (POST)
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/", status_code=201)
async def create_event(
    body: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
):
    
    try:
        event = await event_service.create_event(
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
        return event
    except event_service.InvalidEventDataError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE TRANSICIÓN DE ESTADO 
# ═══════════════════════════════════════════════════════════════════════════════

@router.put("/{event_id}/activate")
async def activate_event(event_id: str, db: AsyncSession = Depends(get_db)):
   
    try:
        event = await event_service.activate_event(db, event_id)
        return event
    except event_service.EventNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except event_service.EventAlreadyActiveError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except event_service.InvalidEventStatusError as e:
        raise HTTPException(status_code=400, detail=str(e))





@router.put("/{event_id}/sold-out")
async def mark_sold_out(event_id: str, db: AsyncSession = Depends(get_db)):
    
    try:
        event = await event_service.mark_sold_out(db, event_id)
        return event
    except event_service.EventNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except event_service.InvalidEventStatusError as e:
        raise HTTPException(status_code=400, detail=str(e))
