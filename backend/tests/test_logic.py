
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.event import CreateEventRequest
from app.schemas.queue import EnterQueueRequest, LeaveQueueRequest
from app.schemas.simulate import SimulateLoadRequest
from app.schemas.ticket import PurchaseRequest

# ══════════════════════════════════════════════════════════════
# Tests de Schemas — Eventos
# ══════════════════════════════════════════════════════════════

class TestEventSchema:

    def test_valid_event(self):
        now = datetime.now()
        event = CreateEventRequest(
            name="Concierto Rock",
            description="Un gran evento",
            total_capacity=100,
            price=50.5,
            event_date=now + timedelta(days=10),
            sale_start=now,
            sale_end=now + timedelta(days=9),
        )
        assert event.name == "Concierto Rock"
        assert event.price == 50.5

    def test_negative_price_rejected(self):
        now = datetime.now()
        with pytest.raises(ValidationError):
            CreateEventRequest(
                name="Evento Test",
                total_capacity=10,
                price=-100,
                event_date=now + timedelta(days=10),
                sale_start=now,
                sale_end=now + timedelta(days=9),
            )

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            CreateEventRequest(total_capacity=10)

    def test_zero_capacity_rejected(self):
        now = datetime.now()
        with pytest.raises(ValidationError):
            CreateEventRequest(
                name="Evento Test",
                total_capacity=0,
                price=50,
                event_date=now + timedelta(days=10),
                sale_start=now,
                sale_end=now + timedelta(days=9),
            )

    def test_empty_name_rejected(self):
        now = datetime.now()
        with pytest.raises(ValidationError):
            CreateEventRequest(
                name="",
                total_capacity=100,
                price=50,
                event_date=now + timedelta(days=10),
                sale_start=now,
                sale_end=now + timedelta(days=9),
            )


# ══════════════════════════════════════════════════════════════
# Tests de Schemas — Cola
# ══════════════════════════════════════════════════════════════

class TestQueueSchema:

    def test_valid_enter_request(self):
        req = EnterQueueRequest(
            user_id="user-123",
            event_id="evt-456",
            first_name="Juan",
            last_name="Pérez",
        )
        assert req.user_id == "user-123"

    def test_missing_user_id(self):
        with pytest.raises(ValidationError):
            EnterQueueRequest(
                event_id="evt-456",
                first_name="Juan",
                last_name="Pérez",
            )

    def test_valid_leave_request(self):
        req = LeaveQueueRequest(user_id="user-123", event_id="evt-456")
        assert req.event_id == "evt-456"


# ══════════════════════════════════════════════════════════════
# Tests de Schemas — Compras
# ══════════════════════════════════════════════════════════════

class TestPurchaseSchema:

    def test_valid_purchase(self):
        req = PurchaseRequest(
            user_id="user-123",
            event_id="evt-456",
            first_name="María",
            last_name="González",
            dni="12345678",
            email="maria@test.com",
            payment_method="credit_card",
            quantity=2,
        )
        assert req.quantity == 2

    def test_zero_quantity_rejected(self):
        with pytest.raises(ValidationError):
            PurchaseRequest(
                user_id="user-123",
                event_id="evt-456",
                first_name="María",
                last_name="González",
                dni="12345678",
                email="maria@test.com",
                payment_method="credit_card",
                quantity=0,
            )

    def test_missing_email(self):
        with pytest.raises(ValidationError):
            PurchaseRequest(
                user_id="user-123",
                event_id="evt-456",
                first_name="María",
                last_name="González",
                dni="12345678",
                payment_method="credit_card",
            )


# ══════════════════════════════════════════════════════════════
# Tests de Schemas — Simulación
# ══════════════════════════════════════════════════════════════

class TestSimulateSchema:

    def test_valid_simulate_request(self):
        req = SimulateLoadRequest(event_id="evt-123", num_users=50)
        assert req.num_users == 50

    def test_zero_users_rejected(self):
        with pytest.raises(ValidationError):
            SimulateLoadRequest(event_id="evt-123", num_users=0)


# ══════════════════════════════════════════════════════════════
# Tests de Excepciones
# ══════════════════════════════════════════════════════════════

class TestExceptions:

    def test_exception_hierarchy(self):
        from app.exceptions import (
            BadRequestError,
            ConflictError,
            ForbiddenError,
            NotFoundError,
            ValidationError,
            VirtualQueueError,
        )

        assert issubclass(NotFoundError, VirtualQueueError)
        assert issubclass(ConflictError, VirtualQueueError)
        assert issubclass(ForbiddenError, VirtualQueueError)
        assert issubclass(BadRequestError, VirtualQueueError)
        assert issubclass(ValidationError, VirtualQueueError)

    def test_status_codes(self):
        from app.exceptions import (
            BadRequestError,
            ConflictError,
            ForbiddenError,
            NotFoundError,
        )

        assert NotFoundError.status_code == 404
        assert ConflictError.status_code == 409
        assert ForbiddenError.status_code == 403
        assert BadRequestError.status_code == 400

    def test_service_exceptions_inherit_correctly(self):
        from app.exceptions import ConflictError, ForbiddenError, NotFoundError
        from app.services.event_service import EventAlreadyActiveError, EventNotFoundError
        from app.services.purchase_service import InsufficientCapacityError, UserNotAllowedError
        from app.services.queue_service import AlreadyInQueueError, NotInQueueError

        assert issubclass(EventNotFoundError, NotFoundError)
        assert issubclass(EventAlreadyActiveError, ConflictError)
        assert issubclass(UserNotAllowedError, ForbiddenError)
        assert issubclass(InsufficientCapacityError, ConflictError)
        assert issubclass(AlreadyInQueueError, ConflictError)
        assert issubclass(NotInQueueError, NotFoundError)

    def test_exception_message(self):
        from app.exceptions import NotFoundError

        error = NotFoundError("Evento no encontrado")
        assert error.message == "Evento no encontrado"
        assert error.status_code == 404
        assert str(error) == "Evento no encontrado"
