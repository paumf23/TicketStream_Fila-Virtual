
import pytest
from fastapi.testclient import TestClient
from app.main import app

# Creamos un "cliente de prueba" que simula ser un navegador llamando a la API
client = TestClient(app)

def test_health_check_basic():
    """
    PRUEBA UNITARIA SIMPLE:
    Verifica que el endpoint /health responda algo, 
    incluso si no hay base de datos.
    """
    # 1. Ejecutamos la acción
    response = client.get("/health")
    
    # 2. Verificamos el resultado (Asertamos)
    # Queremos que el código de respuesta sea 200 (Éxito)
    assert response.status_code == 200
    
    # Queremos que el cuerpo de la respuesta contenga la palabra "status"
    data = response.json()
    assert "status" in data
    assert data["service"] == "virtual-queue-api"

def test_root_404():
    """
    Verifica que si entramos a una ruta que no existe, la API responda 404.
    """
    response = client.get("/ruta-inexistente")
    assert response.status_code == 404
