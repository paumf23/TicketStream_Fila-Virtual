
import pytest


@pytest.mark.anyio
async def test_health_check_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["service"] == "virtual-queue-api"


@pytest.mark.anyio
async def test_nonexistent_route_returns_404(client):
    """Verifica que rutas inexistentes devuelvan 404."""
    response = await client.get("/ruta-inexistente")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_events_list_returns_valid_response(client):
    """Verifica que el listado de eventos responde correctamente con la DB disponible."""
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
