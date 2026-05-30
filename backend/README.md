# 🐍 TicketStream — Backend

API REST + WebSocket para el sistema de fila virtual **TicketStream**. Backend robusto y de alto rendimiento que gestiona la venta de tickets con fila de espera en Redis, transacciones atómicas en MySQL, y actualizaciones en tiempo real vía WebSocket.

---

## 🛠️ Tech Stack

| Tecnología | Versión | Rol |
|---|---|---|
| **Python** | 3.12 | Lenguaje principal |
| **FastAPI** | 0.115 | Framework web — REST API + WebSocket |
| **Uvicorn** | 0.34 | Servidor ASGI de alto rendimiento |
| **SQLAlchemy** | 2.0 | ORM async para MySQL |
| **Redis** | 7.0 | Motor de fila, pub/sub, cache de sesiones y permisos |
| **MySQL** | 8.0 | Base de datos persistente (eventos, tickets, pagos) |
| **Pydantic** | 2.x | Validación de datos y schemas |
| **Pytest** | 8.3 | Testing |
| **Ruff** | — | Linter y formatter |

---

## 🏛️ Arquitectura en Capas

El backend sigue una arquitectura en capas con separación estricta de responsabilidades:

```
Routers (HTTP/WS)  →  Services (Lógica de negocio)  →  Repositories (Acceso a datos)
                                                          ├── MySQL (SQLAlchemy async)
                                                          └── Redis (redis.asyncio)
```

| Capa | Responsabilidad |
|---|---|
| **Routers** | Endpoints HTTP y WebSocket. Reciben el request, delegan al servicio y devuelven la respuesta. |
| **Services** | Lógica de negocio, validaciones, orquestación de operaciones entre repositorios. |
| **Repositories** | Acceso a datos — queries SQL (SQLAlchemy) y operaciones Redis. Solo la capa de datos. |
| **Worker** | Proceso independiente en segundo plano que avanza la fila por lotes (ver sección Worker). |
| **Middleware** | Manejo global de errores — convierte excepciones de dominio en respuestas HTTP automáticamente. |

---

## Patrones y Prácticas implementadas

| | Implementación |
|---|---|
| **Repository Pattern** | Capa de repositories para MySQL y Redis |
| **Service Layer** | Lógica de negocio separada de routers |
| **Reliable Queue (Redis)** | Lua script `LPOP → RPUSH` con recovery |
| **Pub/Sub para WebSocket** | Redis Pub/Sub como bus de mensajes |
| **Rate Limiting (Token Bucket vía Lua)** | Script Lua atómico con ventana deslizante |
| **Graceful Shutdown** | Signal handlers + flag `_running` |
| **Domain Exception Hierarchy** | Mapeo automático excepción → HTTP status |
| **Multi-stage Docker** | Builder → Runtime |

---

## ⚙️ Worker — Procesador de Fila

El **Worker** es un proceso independiente que corre en su propio contenedor Docker (`vq_worker`). Es el motor que hace avanzar la fila virtual.

### ¿Cómo funciona?

1. **Cada segundo** (configurable con `PROCESS_INTERVAL`), el worker revisa si hay simulaciones activas en Redis.
2. Para cada evento activo, **mueve un lote de usuarios** de la cola a una lista de procesamiento (atómico vía Lua) siguiendo el **Patrón Reliable Queue** para garantizar que ningún usuario se pierda si el Worker falla.
3. A cada usuario procesado le otorga un **permiso temporal** (TTL) para comprar.
4. Los usuarios simulados pueden **abandonar la fila** según la tasa de abandono configurada.
5. **Publica los resultados** por WebSocket (vía Redis Pub/Sub), actualizando la interfaz en tiempo real.

### Métricas que calcula por ciclo

| Métrica | Descripción |
|---|---|
| `processed_rate` | Usuarios atendidos por minuto |
| `throughput` | Salida total (atendidos + abandonos) por minuto |
| `incoming_rate` | Usuarios que ingresaron a la fila por minuto |
| `trend` | Tendencia de la fila (ingreso - salida). Positivo = crece, negativo = decrece |
| `effort` | Porcentaje de carga del worker (tiempo de ejecución / intervalo) |
| `revenue` | Recaudación acumulada (usuarios atendidos × precio del evento) |
| `occupancy_percentage` | Porcentaje de ocupación del evento |

### Configuración

El comportamiento del worker se controla con variables de entorno y con la configuración por evento en Redis (que el usuario puede ajustar desde la simulación avanzada):

| Parámetro | Fuente | Descripción |
|---|---|---|
| `PROCESS_INTERVAL` | `.env` | Cada cuántos segundos el worker procesa un lote (default: `1`) |
| `ALLOWED_TTL` | `.env` | Segundos que tiene el usuario para comprar (default: `300`) |
| `speed` | Redis (por evento) | Velocidad de procesamiento en usuarios/minuto |
| `abandon_rate` | Redis (por evento) | Porcentaje de abandono de usuarios simulados |

---

## 🛡️ Manejo de Errores

### Jerarquía de excepciones

El backend define una jerarquía de excepciones de dominio que se convierten automáticamente en respuestas HTTP con el status code correspondiente:

```
VirtualQueueError (500)
├── NotFoundError (404)        → Recurso no encontrado
├── ConflictError (409)        → Conflicto con el estado actual
├── ForbiddenError (403)       → Acción no permitida
├── BadRequestError (400)      → Datos o estado inválido
└── ValidationError (422)      → Error de validación de entrada
```

### Excepciones específicas de servicios

Los servicios definen excepciones más específicas que heredan de las base:

| Excepción | Hereda de | Servicio |
|---|---|---|
| `EventNotFoundError` | `NotFoundError` | `event_service` |
| `EventAlreadyActiveError` | `ConflictError` | `event_service` |
| `AlreadyInQueueError` | `ConflictError` | `queue_service` |
| `NotInQueueError` | `NotFoundError` | `queue_service` |
| `UserNotAllowedError` | `ForbiddenError` | `purchase_service` |
| `InsufficientCapacityError` | `ConflictError` | `purchase_service` |

El middleware en `middleware/__init__.py` captura cualquier `VirtualQueueError` y devuelve un JSON con `detail`, `error_type` y el status code correcto.

---

## 🚀 Instalación y Ejecución

### Requisitos

- [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/)

### Levantar los servicios

```bash
# Desde la raíz del proyecto
docker compose up -d

# Verificar que todo esté corriendo (4 contenedores: api, worker, mysql, redis)
docker compose ps

# Ver los logs de la API
docker compose logs api

# Ver los logs del worker
docker compose logs worker
```

La API estará disponible en **http://localhost:8000**.

### Swagger UI

Documentación interactiva de la API: **http://localhost:8000/docs**

### Cargar datos de prueba (Seed)

```bash
docker compose exec api python -m app.seed
```

---

## 📡 Endpoints

### Infraestructura

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado de la API y conexión a Redis |

### Eventos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/events/` | Listar todos los eventos |
| `GET` | `/api/events/active` | Listar eventos activos (acepta query param `?category=`) |
| `GET` | `/api/events/{id}` | Detalle de un evento |
| `GET` | `/api/events/{id}/stats` | Estadísticas en tiempo real del evento |
| `POST` | `/api/events/` | Crear un evento |
| `PUT` | `/api/events/{id}/activate` | Activar un evento para la venta |
| `PUT` | `/api/events/{id}/sold-out` | Marcar como agotado |

### Fila de Espera

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/queue/enter` | Entrar a la fila de un evento |
| `GET` | `/api/queue/position` | Consultar posición actual (`?user_id=...&event_id=...`) |
| `DELETE` | `/api/queue/leave` | Abandonar la fila voluntariamente |

### Tickets / Compras

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/tickets/purchase` | Comprar ticket(s) cuando se tiene el turno |
| `GET` | `/api/tickets/{id}` | Detalle de un ticket comprado |

### Simulación

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/simulate/load` | Simulación estándar — inyectar usuarios ficticios en la fila |
| `POST` | `/api/simulate/advanced` | Simulación avanzada — parámetros configurables |

**Parámetros de la simulación avanzada** (`POST /api/simulate/advanced`):

| Parámetro | Tipo | Descripción | Rango |
|---|---|---|---|
| `event_id` | `string` | UUID del evento | requerido |
| `num_users` | `int` | Población total simulada | 1 — 10.000 |
| `processing_speed` | `int` | Velocidad de procesamiento (usuarios/minuto) | > 0 |
| `abandon_rate` | `float` | Tasa de abandono por ciclo | 0% — 100% |
| `event_capacity` | `int` | Entradas disponibles para la venta | 10.000 — 50.000 |
| `include_me` | `bool` | Incluir al usuario real en la fila simulada | `true` / `false` |
| `user_id` | `string?` | ID del usuario real (si `include_me` es `true`) | opcional |
| `target_position` | `int?` | Posición del usuario real dentro de la fila | opcional |

### WebSocket

| Ruta | Descripción |
|---|---|
| `ws://localhost:8000/ws/{event_id}` | Canal de actualizaciones en tiempo real por evento |

---

## ⚙️ Variables de Entorno

Ver [`.env.example`](../.env.example) para la referencia completa. Resumen:

| Variable | Descripción | Default |
|---|---|---|
| `REDIS_URL` | Conexión a Redis | `redis://redis:6379/0` |
| `DATABASE_URL` | Conexión a MySQL (async) | `mysql+asyncmy://root:secret@db:3306/virtual_queue` |
| `ENVIRONMENT` | Entorno de ejecución | `development` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `CORS_ORIGINS` | Orígenes permitidos | `http://localhost:3000` |
| `BATCH_SIZE` | Usuarios por ciclo del worker (default de fallback) | `10` |
| `PROCESS_INTERVAL` | Segundos entre ciclos del worker | `1` |
| `ALLOWED_TTL` | Segundos para completar la compra | `300` |
| `RECONNECT_GRACE_PERIOD` | Gracia para reconexión WebSocket | `30` |

---

## 🧪 Tests

### Tests Unitarios y de Integración

```bash
# Ejecutar tests dentro del contenedor Docker
docker compose exec api python -m pytest tests/ -v
```

Los tests incluyen:

- **`test_basic.py`** (8 tests) — Verifican endpoints HTTP: health check, rutas 404, validaciones de request body (422).
- **`test_logic.py`** (17 tests) — Verifican schemas Pydantic (validación de datos) y la jerarquía de excepciones del dominio.
- **`test_integration.py`** — Pruebas reales de negocio. Verifica el orden FIFO de la fila usando Redis, comprueba que las compras descuentan atómicamente la capacidad del evento en MySQL, valida la salud de la conexión a caché, y verifica el handshake de conexiones WebSocket.

### Lint

```bash
docker compose exec api ruff check app/
```

### Tests de Carga (k6 + Grafana)

Para ejecutar pruebas de estrés con **k6** y visualizar métricas en **Grafana**:

```bash
# Levantar el stack completo de testing (API + InfluxDB + Grafana + k6)
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d
```

- **Grafana:** Disponible en `http://localhost:3001`.
- **Dashboards:** Incluye un tablero preconfigurado para ver latencia y usuarios de k6 en tiempo real.

Para más detalles sobre escenarios de carga, ver [`docs/TESTING.md`](../docs/TESTING.md).

---

## 📁 Estructura de Directorios

```
backend/
├── Dockerfile                      # Imagen Docker (API + Worker)
├── requirements.txt                # Dependencias Python
├── pyproject.toml                  # Configuración de ruff y pytest
├── app/
│   ├── main.py                     # Punto de entrada FastAPI (lifespan, CORS, routers)
│   ├── config.py                   # Configuración centralizada (variables de entorno)
│   ├── database.py                 # Conexión async a MySQL (SQLAlchemy)
│   ├── redis.py                    # Pool de conexión a Redis
│   ├── dependencies.py             # Inyección de dependencias (get_db)
│   ├── exceptions.py               # Jerarquía de excepciones del dominio
│   ├── worker.py                   # Motor de simulación — procesa la fila en segundo plano
│   ├── seed.py                     # Datos iniciales de prueba (eventos)
│   ├── middleware/
│   │   └── __init__.py             # Manejo global de errores (excepciones → HTTP)
│   ├── models/                     # Modelos SQLAlchemy (ORM)
│   │   ├── event.py                # Modelo de Evento
│   │   ├── ticket.py               # Modelo de Ticket
│   │   ├── buyer.py                # Modelo de Comprador
│   │   ├── payment.py              # Modelo de Pago
│   │   └── queue_history.py        # Historial de fila
│   ├── schemas/                    # Schemas Pydantic (validación de entrada/salida)
│   │   ├── event.py                # Schemas de Evento
│   │   ├── ticket.py               # Schemas de Ticket/Compra
│   │   ├── queue.py                # Schemas de Fila
│   │   ├── simulate.py             # Schemas de Simulación
│   │   └── responses.py            # Schemas de respuestas HTTP
│   ├── routers/                    # Endpoints HTTP y WebSocket
│   │   ├── events.py               # CRUD de eventos
│   │   ├── queue.py                # Operaciones de fila
│   │   ├── tickets.py              # Compra de tickets
│   │   ├── simulate.py             # Simulación estándar y avanzada
│   │   ├── health.py               # Health check
│   │   └── websocket_handler.py    # Endpoint WebSocket (tiempo real)
│   ├── services/                   # Lógica de negocio
│   │   ├── event_service.py        # Gestión de eventos
│   │   ├── queue_service.py        # Gestión de fila
│   │   ├── purchase_service.py     # Gestión de compras
│   │   └── connection_manager.py   # Gestión de conexiones WebSocket
│   └── repositories/              # Acceso a datos (MySQL + Redis)
│       ├── event_repository.py     # Queries de eventos (MySQL)
│       ├── ticket_repository.py    # Queries de tickets (MySQL)
│       ├── buyer_repository.py     # Queries de compradores (MySQL)
│       ├── payment_repository.py   # Queries de pagos (MySQL)
│       ├── queue_history_repository.py  # Queries de historial (MySQL)
│       └── redis_repository.py     # Operaciones Redis (fila, pub/sub, permisos, métricas)
└── tests/
    ├── conftest.py                 # Fixtures de pytest (client HTTP, mocks)
    ├── test_basic.py               # Tests de endpoints HTTP
    ├── test_logic.py               # Tests de schemas y excepciones
    └── load/                       # Tests de carga (k6)
        └── scripts/
            ├── smoke-test.js       # 10 VUs, 30s — verificar que todo funciona
            ├── endpoints-test.js   # 0→1000 VUs por endpoint — cuellos de botella
            ├── full-flow-test.js   # 0→1000 VUs — flujo completo con WebSocket
            └── stress-test.js      # 0→10000 VUs — punto de quiebre
```

---

<p align="center">
  Parte del proyecto <strong>TicketStream</strong> — Sistema de fila virtual en tiempo real
</p>
