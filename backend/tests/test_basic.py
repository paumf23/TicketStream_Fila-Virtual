
import pytest


import pytest
from unittest.mock import patch, AsyncMock

@pytest.fixture(autouse=True)
def mock_rate_limit():
    """Mock global para aislar la dependencia rate_limit en todos los tests de basic."""
    with patch("app.dependencies.redis_repository.check_rate_limit", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        yield mock_check

@pytest.mark.anyio
@patch("app.routers.health.redis_pool", new_callable=AsyncMock)
async def test_health_check_returns_200(mock_redis_pool, client):
    mock_redis_pool.ping.return_value = True
    
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["service"] == "virtual-queue-api"
    assert data["redis"] == "connected"
    mock_redis_pool.ping.assert_called_once()


@pytest.mark.anyio
@patch("app.routers.health.redis_pool", new_callable=AsyncMock)
async def test_health_check_redis_disconnected(mock_redis_pool, client):
    """Verifica que el sistema indique estado degraded si Redis falla."""
    mock_redis_pool.ping.side_effect = Exception("Connection refused")
    
    response = await client.get("/health")
    assert response.status_code == 200  # API sigue viva
    
    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"] == "disconnected"
    mock_redis_pool.ping.assert_called_once()


@pytest.mark.anyio
async def test_nonexistent_route_returns_404(client):
    """Verifica que rutas inexistentes devuelvan 404."""
    response = await client.get("/ruta-inexistente")
    assert response.status_code == 404


@pytest.mark.anyio
@patch("app.routers.events.event_service.get_all_events", new_callable=AsyncMock)
async def test_events_list_returns_valid_response(mock_get_all, client):
    """Verifica que el listado de eventos responde correctamente con la DB mockeada."""
    mock_get_all.return_value = []  # Retorna lista vacía como si no hubiera eventos

    response = await client.get("/api/events/")
    assert response.status_code == 200

    data = response.json()
    assert "events" in data
    assert "total" in data
    assert isinstance(data["events"], list)
    assert data["total"] >= 0


@pytest.mark.anyio
async def test_create_event_validation_error(client):
    response = await client.post("/api/events/", json={})
    assert response.status_code == 422

    data = response.json()
    assert "errors" in data
    assert len(data["errors"]) > 0
    for error in data["errors"]:
        assert "campo" in error
        assert "mensaje" in error
        assert "tipo" in error


@pytest.mark.anyio
async def test_create_event_invalid_price(client):
    response = await client.post("/api/events/", json={
        "name": "Evento Test",
        "total_capacity": 100,
        "price": -50,
        "event_date": "2026-12-01T20:00:00",
        "sale_start": "2026-11-01T00:00:00",
        "sale_end": "2026-11-30T23:59:59",
    })
    assert response.status_code == 422


@pytest.mark.anyio
async def test_queue_enter_validation_error(client):
    response = await client.post("/api/queue/enter", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_ticket_purchase_validation_error(client):
    response = await client.post("/api/tickets/purchase", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_simulate_load_validation_error(client):
    response = await client.post("/api/simulate/load", json={})
    assert response.status_code == 422
