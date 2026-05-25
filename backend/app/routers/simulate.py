# ═══════════════════════════════════════════════════════════════════════════════
# simulate.py — Endpoint de Simulación de Carga
# ═══════════════════════════════════════════════════════════════════════════════


from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, rate_limit
from app.schemas.responses import SimulateLoadResponse
from app.schemas.simulate import SimulateLoadRequest, AdvancedSimulateRequest
from app.services import simulate_service


router = APIRouter()


@router.post("/load", status_code=201, response_model=SimulateLoadResponse, dependencies=[Depends(rate_limit(limit=2, window=60))])
async def simulate_load(
    body: SimulateLoadRequest,
    db: AsyncSession = Depends(get_db),
):
    return await simulate_service.execute_basic_simulation(db, body)


@router.post("/advanced", status_code=201, dependencies=[Depends(rate_limit(limit=2, window=60))])
async def simulate_advanced(
    body: AdvancedSimulateRequest,
    db: AsyncSession = Depends(get_db),
):
    return await simulate_service.execute_advanced_simulation(db, body)
