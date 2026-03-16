

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.responses import PurchaseResponse, TicketDetailResponse
from app.schemas.ticket import PurchaseRequest
from app.services import purchase_service

router = APIRouter()


@router.post("/purchase", status_code=201, response_model=PurchaseResponse)
async def purchase_ticket(
    body: PurchaseRequest,
    db: AsyncSession = Depends(get_db),
):
    return await purchase_service.initiate_purchase(
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


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await purchase_service.get_ticket_detail(db, ticket_id)
