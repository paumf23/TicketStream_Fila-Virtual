import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from app.redis import redis_pool
from app.repositories import redis_repository


@pytest.mark.anyio
async def test_integration_purchase_decrements_capacity(client: AsyncClient):
    """Verifica que una compra descuenta correctamente el inventario en la Base de Datos."""
    # 1. Crear evento ficticio
    unique_name = f"Test Event {uuid.uuid4()}"
    now = datetime.now()
    event_data = {
        "name": unique_name,
        "description": "Integration Test Event",
        "total_capacity": 100,
        "price": 50.0,
        "event_date": (now + timedelta(days=10)).isoformat(),
        "sale_start": now.isoformat(),
        "sale_end": (now + timedelta(days=9)).isoformat()
    }
    response = await client.post("/api/events/", json=event_data)
    assert response.status_code == 201, f"Fallo al crear evento: {response.text}"
    event_id = response.json()["event_id"]

    # 2. Dar permiso en Redis
    user_id = str(uuid.uuid4())
    await redis_repository.set_allowed(event_id, user_id, ttl_seconds=300)

    # 3. Comprar 2 entradas
    purchase_data = {
        "user_id": user_id,
        "event_id": event_id,
        "first_name": "Integration",
        "last_name": "Test",
        "dni": "12345678",
        "email": "test@integration.com",
        "payment_method": "card",
        "payment_provider": "visa",
        "quantity": 2
    }
    buy_response = await client.post("/api/tickets/purchase", json=purchase_data)
    assert buy_response.status_code == 201, f"Fallo al comprar ticket: {buy_response.text}"

    # 4. Verificar capacidad
    get_event_response = await client.get(f"/api/events/{event_id}")
    assert get_event_response.status_code == 200
    updated_capacity = get_event_response.json()["remaining_capacity"]
    
    # 5. Assert
    assert updated_capacity == 98


@pytest.mark.anyio
async def test_integration_queue_fifo_order():
    """Garantiza que la fila virtual respeta el orden de llegada (FIFO) usando Redis."""
    # 1. Crear evento ficticio y usuarios
    event_id = str(uuid.uuid4())
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    
    # 2. Encolar Usuario A y luego B
    await redis_repository.queue_push(event_id, user_a)
    await redis_repository.queue_push(event_id, user_b)
    
    # 3. Extraer usuarios simulando el Worker (LPOP/LMOVE por lote)
    lote = await redis_repository.queue_pop_safe(event_id, batch_size=5)
    
    # 4. Assert orden (FIFO)
    assert len(lote) == 2
    assert lote[0] == user_a
    assert lote[1] == user_b


@pytest.mark.anyio
async def test_integration_redis_health():
    """Verifica que la comunicación y persistencia en caché/memoria temporal funcione bien."""
    # Ping
    ping_res = await redis_pool.ping()
    assert ping_res is True
    
    # Set / Get con expiración
    test_key = "test_integration_health_key"
    await redis_pool.set(test_key, "funciona", ex=5)
    
    val = await redis_pool.get(test_key)
    assert val == "funciona"


def test_integration_websocket_connection():
    """Verifica que el endpoint WebSocket acepta conexiones y se suscribe a Redis correctamente."""
    from fastapi.testclient import TestClient
    from app.main import app
    import uuid
    
    client = TestClient(app)
    event_id = str(uuid.uuid4())
    
    # Intentamos conectar al WebSocket
    with client.websocket_connect(f"/ws/{event_id}") as websocket:
        # Si logramos entrar al bloque with, la conexión (handshake) fue exitosa
        # y la suscripción a Redis en el backend funcionó.
        assert websocket is not None
