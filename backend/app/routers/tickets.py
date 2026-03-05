

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services import purchase_service



class PurchaseRequest(BaseModel):
   
    user_id: str = Field(
        ...,
        min_length=1,
        description="UUID del usuario en la cola",
        examples=["user-550e8400-e29b-41d4-a716-446655440000"],
    )

    
    event_id: str = Field(
        ...,
        min_length=1,
        description="UUID del evento para el cual compra",
        examples=["evt-123e4567-e89b-12d3-a456-426614174000"],
    )

    

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del comprador",
        examples=["Juan"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Apellido del comprador",
        examples=["Pérez"],
    )
    dni: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="DNI del comprador",
        examples=["35123456"],
    )
    email: str = Field(
        ...,
        min_length=1,
        description="Email del comprador",
        examples=["juan.perez@email.com"],
    )

    
    payment_method: str = Field(
        ...,
        description="Método de pago",
        examples=["credit_card"],
    )


router = APIRouter()


@router.post("/purchase", status_code=201)
async def purchase_ticket(
    body: PurchaseRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await purchase_service.initiate_purchase(
            db,
            user_id=body.user_id,
            event_id=body.event_id,
            first_name=body.first_name,
            last_name=body.last_name,
            dni=body.dni,
            email=body.email,
            payment_method=body.payment_method,
        )
        return result

    except purchase_service.UserNotAllowedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    except purchase_service.TicketNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except purchase_service.InsufficientCapacityError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{ticket_id}/confirm")
async def confirm_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await purchase_service.confirm_purchase(db, ticket_id)
        return result
    except purchase_service.TicketNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except purchase_service.TicketAlreadyProcessedError as e:
       
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/buyer/{buyer_id}")
async def get_buyer_tickets(
    buyer_id: str,
    db: AsyncSession = Depends(get_db),
):
    tickets = await purchase_service.get_buyer_tickets(db, buyer_id)
    return {"tickets": tickets, "total": len(tickets)}


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await purchase_service.get_ticket_detail(db, ticket_id)
        return result
    except purchase_service.TicketNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
