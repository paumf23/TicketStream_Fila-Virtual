
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from app.schemas.event import CreateEventRequest

def test_event_schema_validation():
    """
    Prueba que el esquema de creación de eventos
    valide correctamente los datos.
    """
    now = datetime.now()
    valid_data = {
        "name": "Concierto Rock",
        "description": "Un gran evento",
        "total_capacity": 100,
        "price": 50.5,
        "event_date": now + timedelta(days=10),
        "sale_start": now,
        "sale_end": now + timedelta(days=9)
    }
    event = CreateEventRequest(**valid_data)
    assert event.name == "Concierto Rock"
    assert event.price == 50.5

def test_event_schema_invalid_price():
    """
    Prueba que el sistema NO permita precios negativos
    (gt=0 o ge=0 en el esquema).
    """
    now = datetime.now()
    invalid_data = {
        "name": "Evento Gratis Mal",
        "total_capacity": 10,
        "price": -100, # Precio negativo
        "event_date": now + timedelta(days=10),
        "sale_start": now,
        "sale_end": now + timedelta(days=9)
    }
    
    with pytest.raises(ValidationError):
        CreateEventRequest(**invalid_data)

def test_event_schema_missing_fields():
    """
    Prueba que falte un campo obligatorio (como el nombre).
    """
    incomplete_data = {
        "total_capacity": 10
    }
    with pytest.raises(ValidationError):
        CreateEventRequest(**incomplete_data)
