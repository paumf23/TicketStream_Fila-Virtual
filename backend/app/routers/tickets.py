

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services import purchase_service



from app.schemas.ticket import PurchaseRequest


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
            quantity=body.quantity,
        )
        return result

    except purchase_service.UserNotAllowedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    except purchase_service.TicketNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except purchase_service.InsufficientCapacityError as e:
        raise HTTPException(status_code=409, detail=str(e))


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
