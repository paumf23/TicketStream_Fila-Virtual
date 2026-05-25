import pytest
from unittest.mock import AsyncMock, patch

from app import worker

@pytest.fixture
def mock_redis_repo():
    with patch("app.worker.redis_repository") as mock_repo:
        mock_repo.get_event_config = AsyncMock(return_value={"speed": 360, "abandon_rate": 0.0})
        mock_repo.queue_length = AsyncMock(return_value=100)
        mock_repo.queue_pop_safe = AsyncMock(return_value=["user1", "user2", "user3"])
        mock_repo.get_incoming_count = AsyncMock(return_value=10)
        mock_repo.reset_incoming_count = AsyncMock()
        mock_repo.remove_active_simulation = AsyncMock()
        mock_repo.set_allowed = AsyncMock()
        mock_repo.publish = AsyncMock()
        mock_repo.clear_processing = AsyncMock()
        mock_repo.increment_abandoned_count = AsyncMock()
        mock_repo.increment_processed_count = AsyncMock()
        mock_repo.get_event_stats_snapshot = AsyncMock(
            return_value={"total_capacity": 1000, "price": 50.0, "revenue": 100.0, "processed_count": 0, "abandoned_count": 0}
        )
        mock_repo.set_event_stats_snapshot = AsyncMock()
        mock_repo.get_active_simulations = AsyncMock(return_value=["event-1"])
        mock_repo.requeue_processing = AsyncMock(return_value=5)

        yield mock_repo


def test_handle_shutdown():
    """Prueba que el manejador de señales cambie la variable global para apagar el worker de forma segura."""
    # Reset global var to True just in case
    worker._running = True

    # Call handler with dummy signal and frame
    worker._handle_shutdown(15, None)

    assert worker._running is False


@pytest.mark.asyncio
async def test_process_event_queue_nominal(mock_redis_repo):
    """Prueba el procesamiento de un lote normal, sin abandonos."""
    result = await worker.process_event_queue(
        event_id="test-event",
        batch_size=3,
        interval=1.0,
        abandon_rate=0.0
    )

    # Validaciones sobre el resultado
    assert result["users_processed"] == 3
    assert result["users_abandoned"] == 0
    assert result["event_id"] == "test-event"
    assert result["queue_length"] == 97  # 100 queue size - 3 procesados

    # Validaciones sobre las interacciones con Redis
    mock_redis_repo.queue_pop_safe.assert_called_once_with("test-event", batch_size=3)
    assert mock_redis_repo.set_allowed.call_count == 3
    assert mock_redis_repo.publish.call_count == 3
    mock_redis_repo.clear_processing.assert_called_once_with("test-event")
    mock_redis_repo.increment_processed_count.assert_called_once_with("test-event", 3)
    mock_redis_repo.increment_abandoned_count.assert_not_called()
    mock_redis_repo.set_event_stats_snapshot.assert_called_once()


@pytest.mark.asyncio
async def test_process_event_queue_with_abandon(mock_redis_repo):
    """Prueba el procesamiento de un lote mixto donde algunos usuarios simulados abandonan la cola."""
    # Usuarios: dos simulados y uno real
    mock_redis_repo.queue_pop_safe = AsyncMock(return_value=["sim-1", "sim-2", "real-1"])
    # Worker.py sobreescribe el parámetro leyendo de redis
    mock_redis_repo.get_event_config = AsyncMock(return_value={"speed": 360, "abandon_rate": 66.0})

    result = await worker.process_event_queue(
        event_id="test-event",
        batch_size=3,
        interval=1.0,
        # Abandon quota calculation: round(3 * 0.66) = 2. Processed quota = 1.
        # Flow: sim-1 (processed=0, quota=1 -> PROCESSED). sim-2 (processed=1, quota=1 -> ABANDONS). real-1 (is_sim=False -> PROCESSED).
        # Totals: 2 Processed, 1 Abandoned
        abandon_rate=66.0
    )

    assert result["users_processed"] == 2
    assert result["users_abandoned"] == 1

    assert mock_redis_repo.increment_processed_count.call_count == 1
    mock_redis_repo.increment_processed_count.assert_called_with("test-event", 2)
    
    assert mock_redis_repo.increment_abandoned_count.call_count == 1
    mock_redis_repo.increment_abandoned_count.assert_called_with("test-event", 1)


@pytest.mark.asyncio
async def test_run_worker_recovery(mock_redis_repo):
    """Prueba el inicio del Worker, su proceso de Recovery inicial y su apagado seguro (graceful exit)."""
    worker._running = True

    # El loop va a procesar una vez (porque mockeamos get_active_simulations para que responda)
    # y cuando llame a asyncio.sleep simularemos la interrupción forzando a False _running.
    async def mock_sleep(*args, **kwargs):
        worker._running = False

    with patch("asyncio.sleep", new_callable=AsyncMock, side_effect=mock_sleep):
        await worker.run_worker()

    # Verificar proceso de Recovery inicial
    mock_redis_repo.requeue_processing.assert_called_with("event-1")
    
    # Verificar procesamiento en el loop
    mock_redis_repo.get_event_config.assert_called_with("event-1")
    mock_redis_repo.publish.assert_called()
