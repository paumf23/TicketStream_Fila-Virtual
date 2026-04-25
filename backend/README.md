# Virtual Queue — Backend

API REST + WebSocket para un sistema de cola virtual de eventos masivos. Gestiona la venta de tickets con cola de espera en Redis, transacciones atómicas en MySQL, y actualizaciones en tiempo real vía WebSocket.

## Tech Stack

| Tecnología | Uso |
|---|---|
| **Python 3.12** | Lenguaje principal |
| **FastAPI** | Framework web (REST + WebSocket) |
| **Redis 7** | Motor de cola, pub/sub, cache de sesiones |
| **MySQL 8** | Base de datos persistente (eventos, tickets, pagos) |
| **SQLAlchemy 2** | ORM async |
| **Docker** | Contenerización y orquestación |
| **Pytest** | Testing |
| **Ruff** | Linter |

## Arquitectura

El backend sigue una arquitectura en capas:

```
Routers (HTTP/WS)  →  Services (Lógica de negocio)  →  Repositories (Acceso a datos)
                                                          ├── MySQL (SQLAlchemy)
                                                          └── Redis (aioredis)
```

- **Routers**: Endpoints HTTP y WebSocket. Delegan al servicio correspondiente.
- **Services**: Lógica de negocio, validaciones, orquestación de operaciones.
- **Repositories**: Acceso a datos (queries SQL, operaciones Redis). Solo la capa de datos.
- **Middleware**: Manejo global de errores (convierte excepciones de dominio en respuestas HTTP).

## Requisitos Previos

- [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/)

## Instalación y Ejecución

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Virtual\ Queue

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Levantar toda la infraestructura
docker compose up -d

# 4. Verificar que todo esté corriendo
docker compose ps

# 5. Ver los logs de la API
docker compose logs api
```

La API estará disponible en `http://localhost:8000`.

### Swagger UI

Acceder a la documentación interactiva en: **http://localhost:8000/docs**

### Cargar datos de prueba (Seed)

```bash
docker compose exec api python -m app.seed
```

## Endpoints Principales

### Infraestructura

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado de la API y conexión a Redis |

### Eventos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/events/` | Listar todos los eventos |
| `GET` | `/api/events/active` | Listar eventos activos |
| `GET` | `/api/events/{id}` | Detalle de un evento |
| `GET` | `/api/events/{id}/stats` | Estadísticas del evento |
| `POST` | `/api/events/` | Crear un evento |
| `PUT` | `/api/events/{id}/activate` | Activar un evento |
| `PUT` | `/api/events/{id}/sold-out` | Marcar como agotado |

### Cola de Espera

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/queue/enter` | Entrar a la cola |
| `GET` | `/api/queue/position` | Consultar posición |
| `DELETE` | `/api/queue/leave` | Abandonar la cola |

### Tickets / Compras

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/tickets/purchase` | Comprar ticket(s) |
| `GET` | `/api/tickets/{id}` | Detalle de un ticket |

### Simulación

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/simulate/load` | Inyectar usuarios ficticios |

### WebSocket

| Ruta | Descripción |
|------|-------------|
| `ws://localhost:8000/ws/{event_id}` | Actualizaciones en tiempo real |

## Variables de Entorno

Ver [`.env.example`](../.env.example) para la referencia completa de variables disponibles.

## Tests

```bash
# Correr tests dentro del contenedor
docker compose exec api python -m pytest tests/ -v

# Correr lint
docker compose exec api ruff check app/
```

### Tests de Carga (Load Testing)

Para ejecutar las simulaciones de estrés con **k6** y visualizar las métricas en **Grafana**, usá el siguiente comando que combina la infraestructura base con el stack de testing:

```bash
# Levantar el stack completo de testing (API + InfluxDB + Grafana + k6)
docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d
```

*   **Grafana:** Disponible en `http://localhost:3001` (login: `admin` / `admin`).
*   **Dashboards:** Incluye un tablero preconfigurado para ver latencia y usuarios de k6 en tiempo real.

### Desarrollo local (sin Docker)

Si necesitás correr los tests sin Docker, ajustar los defaults en `.env`:

```env
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=mysql+asyncmy://root:secret@localhost:3306/virtual_queue
```

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Estructura de Directorios

```
backend/
├── Dockerfile              # Imagen Docker para API y Worker
├── requirements.txt        # Dependencias de Python
├── pyproject.toml          # Configuración de ruff y pytest
├── app/
│   ├── main.py             # Punto de entrada FastAPI
│   ├── config.py           # Configuración (variables de entorno)
│   ├── database.py         # Conexión async a MySQL
│   ├── redis.py            # Pool de conexión a Redis
│   ├── dependencies.py     # Inyección de dependencias
│   ├── exceptions.py       # Jerarquía de excepciones del dominio
│   ├── worker.py           # Procesador de cola (background)
│   ├── seed.py             # Datos iniciales de prueba
│   ├── middleware/          # Manejo global de errores
│   ├── models/             # Modelos SQLAlchemy (ORM)
│   ├── schemas/            # Schemas Pydantic (validación)
│   ├── routers/            # Endpoints HTTP y WebSocket
│   ├── services/           # Lógica de negocio
│   └── repositories/       # Acceso a datos (MySQL + Redis)
└── tests/
    ├── test_basic.py       # Tests de endpoints
    ├── test_logic.py       # Tests de schemas/validación
    └── load/               # Tests de carga (k6)
```
