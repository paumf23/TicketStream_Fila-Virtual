<p align="center">
  <h1 align="center">🎟️ TicketStream</h1>
  <p align="center">
    <strong>Sistema de fila virtual en tiempo real para la venta de entradas a eventos masivos.</strong>
  </p>
  <p align="center">
    <a href="#-inicio-rápido">Inicio Rápido</a> •
    <a href="#-arquitectura">Arquitectura</a> •
    <a href="#-api-reference">API Reference</a> •
    <a href="#-frontend">Frontend</a> •
    <a href="#-testing">Testing</a> •
    <a href="#-documentación">Documentación</a>
  </p>
</p>

---

## 📋 Descripción

**TicketStream** es una plataforma full-stack con un **backend robusto y de alto rendimiento** que gestiona la venta de entradas a eventos masivos mediante un sistema de fila de espera virtual. Construida sobre una arquitectura event-driven con procesamiento asíncrono, operaciones atómicas en Redis y transacciones MySQL, la plataforma está diseñada para soportar **hasta 10.000 usuarios concurrentes** garantizando equidad en el orden de llegada y actualizaciones en tiempo real vía WebSocket. Además, el usuario puede **configurar una simulación avanzada** directamente desde la interfaz, ajustando parámetros como cantidad de usuarios, velocidad de procesamiento y tasa de abandono para analizar el comportamiento del sistema bajo diferentes escenarios de carga.

### ¿Qué problema resuelve?

Cuando un evento popular pone a la venta sus entradas, miles de usuarios intentan comprar al mismo tiempo. Sin un sistema de fila:

- Los servidores se saturan y caen.
- Usuarios con mejor conexión tienen ventaja injusta.
- Se producen sobreventa (race conditions) y experiencias frustrantes.

**TicketStream** organiza a los usuarios en una fila virtual ordenada, los procesa por lotes, y les otorga un turno temporizado para completar su compra de forma segura.

### Funcionalidades principales

- 🎫 **Fila de espera virtual** — Orden justo de llegada con posición en tiempo real.
- ⚡ **Actualizaciones en vivo** — WebSocket bidireccional para notificaciones instantáneas.
- 🔒 **Transacciones atómicas** — Sin sobreventa gracias a operaciones atómicas en Redis + transacciones MySQL.
- 📊 **Motor de simulación** — Inyección de usuarios ficticios para pruebas de carga desde la UI, con modo de simulación avanzada configurable por el usuario.
- 🏗️ **Arquitectura Event-Driven & Resiliente** — Worker independiente con patrón **Reliable Queue** (Lua atómico) que evita pérdida de datos durante el procesamiento.
- 📈 **Monitoreo integrado** — Dashboard Grafana con métricas k6 en tiempo real para pruebas de carga.
- 🐳 **Completamente contenerizado** — Un solo comando para levantar toda la infraestructura.

### Simulación

El sistema incluye dos modos de simulación que permiten poblar la fila con usuarios ficticios para observar el comportamiento del sistema:

**Simulación estándar** — Inyecta una cantidad de usuarios ficticios en la fila con configuración por defecto (velocidad: 360 u/min, abandono: 1.5%). Ideal para una demostración rápida.

**Simulación avanzada** — El usuario puede configurar desde la interfaz los siguientes parámetros:

| Parámetro | Descripción | Rango |
|---|---|---|
| **Población total** | Cantidad de usuarios simulados en la fila | 1 — 10.000 |
| **Velocidad de procesamiento** | Usuarios atendidos por minuto por el worker | > 0 |
| **Tasa de abandono** | Porcentaje de usuarios que abandonan la fila por ciclo | 0% — 100% |
| **Capacidad del evento** | Entradas disponibles para la venta | 10.000 — 50.000 |
| **Posición objetivo** | Posición del usuario real dentro de la fila simulada | 1 — población total |
| **Incluirme** | Si el usuario real se ubica dentro de la fila simulada | sí / no |

Ambos modos se controlan desde la sala de espera (`/cola/[eventId]`) y el procesamiento corre en el Worker (contenedor `vq_worker`) en segundo plano.

---

## 🛠️ Tech Stack

### Backend

| Tecnología | Versión | Rol |
|---|---|---|
| **Python** | 3.12 | Lenguaje principal |
| **FastAPI** | 0.115 | Framework web — REST API + WebSocket |
| **Uvicorn** | 0.34 | Servidor ASGI de alto rendimiento |
| **SQLAlchemy** | 2.0 | ORM async para MySQL |
| **Redis** | 7.0 | Motor de fila, pub/sub, cache de sesiones y permisos |
| **MySQL** | 8.0 | Base de datos persistente (eventos, tickets, pagos) |
| **Pydantic** | 2.x | Validación de datos y schemas |

### Frontend

| Tecnología | Versión | Rol |
|---|---|---|
| **Next.js** | 16.2 | Framework React con App Router y SSR |
| **React** | 19.2 | Librería de UI — componentes y hooks |
| **TypeScript** | 5.x | Tipado estático |

### Infraestructura

| Tecnología | Rol |
|---|---|
| **Docker & Docker Compose** | Orquestación de servicios |
| **k6** (Grafana Labs) | Tests de carga |
| **InfluxDB** | Almacenamiento de métricas de testing |
| **Grafana** | Dashboard de monitoreo para pruebas de carga |

---

## 🏛️ Arquitectura

El proyecto implementa una **arquitectura Event-Driven con capas**, donde el backend actúa como API pura (sin renderizado HTML) y el frontend se comunica con él vía REST y WebSocket.

```
Usuario ──► Next.js (React SSR/CSR) ──► FastAPI (API REST + WebSocket)
                                              │
                                    ┌─────────┴──────────┐
                                  Redis              MySQL
```

### Backend — Capas

```
Routers (HTTP/WS)  →  Services (Lógica de negocio)  →  Repositories (Acceso a datos)
                                                          ├── MySQL (SQLAlchemy async)
                                                          └── Redis (redis.asyncio)
```

| Capa | Responsabilidad |
|---|---|
| **Routers** | Endpoints HTTP y WebSocket. Delegan al servicio correspondiente. |
| **Services** | Lógica de negocio, validaciones, orquestación de operaciones. |
| **Repositories** | Acceso a datos — queries SQL y operaciones Redis. |
| **Worker** | Proceso en segundo plano que avanza la fila por lotes. |
| **Middleware** | Manejo global de errores (excepciones de dominio → respuestas HTTP). |

### Redis vs MySQL — Uso complementario

```
┌─────────────────────────────────────────────────────────────┐
│                     REDIS (Tiempo Real)                     │
│  • Fila de espera (LIST)                                    │
│  • Usuarios permitidos (HASH + TTL)                         │
│  • Posiciones actuales (STRING con INCR atómico)            │
│  • Pub/Sub para WebSocket broadcasts                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Compra exitosa
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     MYSQL (Persistencia)                    │
│  • Eventos creados                                          │
│  • Tickets vendidos (histórico)                             │
│  • Compradores y pagos                                      │
│  • Historial de la fila                                     │
└─────────────────────────────────────────────────────────────┘
```

### Manejo de Race Conditions

| Estrategia | Detalle |
|---|---|
| **Operaciones atómicas en Redis** | `LPUSH`, `LPOP`, `INCR` — atómicas por naturaleza. |
| **Transacciones MySQL** | `BEGIN/COMMIT` para la compra de tickets. |
| **TTL en permisos** | El usuario tiene un tiempo límite para completar su compra. |
| **Verificación doble** | Se verifica capacidad restante antes de confirmar la compra. |

---

## 🚀 Inicio Rápido

### Requisitos previos

- [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js 18+](https://nodejs.org/) (para el frontend)
- [Git](https://git-scm.com/)

### 1. Clonar el repositorio

```bash
git clone <tu-url-de-github>
cd Virtual\ Queue
```

> **Nota:** Reemplazá `<tu-url-de-github>` por la URL real de tu repositorio (ej: `https://github.com/tu-usuario/virtual-queue.git`).

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Los valores por defecto del `.env.example` están configurados para funcionar con Docker Compose sin cambios.

### 3. Levantar la infraestructura (Frontend + Backend + BD + Redis + Worker)

```bash
docker compose up -d
```

### 4. Verificar que los servicios estén corriendo

```bash
docker compose ps
```

Deberías ver 5 contenedores activos:

| Contenedor | Servicio | Puerto |
|---|---|---|
| `vq_frontend` | Frontend Next.js | `3000` |
| `vq_mysql` | Base de datos MySQL | `3306` |
| `vq_redis` | Motor de fila Redis | `6379` |
| `vq_api` | API FastAPI | `8000` |
| `vq_worker` | Procesador de fila (background) | No expone puerto |

### 5. Cargar datos de prueba

Este paso es **obligatorio** para que la aplicación tenga eventos visibles en la interfaz:

```bash
docker compose exec api python -m app.seed
```

### 6. Acceder a la aplicación

| Servicio | URL |
|---|---|
| 🌐 **Frontend** | http://localhost:3000 |
| 📖 **Swagger UI** (documentación interactiva de la API) | http://localhost:8000/docs |

---

## 📡 API Reference

### Infraestructura

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado de la API y conexión a Redis |

### Eventos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/events/` | Listar todos los eventos |
| `GET` | `/api/events/active` | Listar eventos activos (con venta abierta) |
| `GET` | `/api/events/{id}` | Detalle de un evento específico |
| `GET` | `/api/events/{id}/stats` | Estadísticas en tiempo real del evento |
| `POST` | `/api/events/` | Crear un nuevo evento |
| `PUT` | `/api/events/{id}/activate` | Activar un evento para la venta |
| `PUT` | `/api/events/{id}/sold-out` | Marcar un evento como agotado |

### Fila de Espera

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/queue/enter` | Entrar a la fila de un evento |
| `GET` | `/api/queue/position` | Consultar posición actual en la fila |
| `DELETE` | `/api/queue/leave` | Abandonar la fila voluntariamente |

### Tickets / Compras

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/tickets/purchase` | Comprar ticket(s) cuando se tiene el turno |
| `GET` | `/api/tickets/{id}` | Consultar detalle de un ticket comprado |

### Simulación

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/simulate/load` | Inyectar usuarios ficticios en la fila (simulación estándar) |
| `POST` | `/api/simulate/advanced` | Simulación avanzada con parámetros configurables (velocidad, abandono, posición) |

### WebSocket

| Ruta | Descripción |
|---|---|
| `ws://localhost:8000/ws/{event_id}` | Canal de actualizaciones en tiempo real por evento |

> **¿Qué es esta ruta?** No es una URL que abras en el navegador. Es un canal de comunicación **bidireccional** que el frontend (Next.js) usa internamente desde `lib/websocket.ts`. Cuando un usuario entra a la sala de espera de un evento, el frontend se conecta automáticamente a `ws://localhost:8000/ws/{event_id}` y recibe mensajes en tiempo real del backend vía Redis Pub/Sub.

**Mensajes WebSocket recibidos:**
- Actualización de posición en la fila
- Notificación de turno para comprar
- Estadísticas del evento en vivo (usuarios en fila, tickets vendidos, ingresos, etc.)

Para explorar y probar los endpoints REST directamente desde el navegador, accedé a la documentación interactiva en **http://localhost:8000/docs**. Los endpoints WebSocket no aparecen en Swagger ya que no son HTTP — son conexiones persistentes manejadas por el frontend.

---

## 🐍 Backend

### Estructura del Backend

```
backend/
├── Dockerfile                      # Imagen Docker (API + Worker)
├── requirements.txt                # Dependencias Python
├── pyproject.toml                  # Configuración de herramientas de desarrollo
├── README.md                       # Documentación específica del backend
├── app/
│   ├── main.py                     # Punto de entrada FastAPI
│   ├── config.py                   # Configuración (variables de entorno)
│   ├── database.py                 # Conexión async a MySQL
│   ├── redis.py                    # Pool de conexión a Redis
│   ├── dependencies.py             # Inyección de dependencias
│   ├── exceptions.py               # Jerarquía de excepciones del dominio
│   ├── worker.py                   # Procesador de fila (background)
│   ├── seed.py                     # Datos iniciales de prueba
│   ├── middleware/
│   │   └── error_handler.py        # Manejo global de errores
│   ├── models/                     # Modelos SQLAlchemy (ORM)
│   │   ├── event.py
│   │   ├── ticket.py
│   │   ├── buyer.py
│   │   ├── payment.py
│   │   └── queue_history.py
│   ├── schemas/                    # Schemas Pydantic (validación)
│   │   ├── event.py
│   │   ├── ticket.py
│   │   ├── queue.py
│   │   ├── simulate.py
│   │   └── responses.py
│   ├── routers/                    # Endpoints HTTP y WebSocket
│   │   ├── events.py
│   │   ├── queue.py
│   │   ├── tickets.py
│   │   ├── simulate.py
│   │   ├── health.py
│   │   └── websocket_handler.py
│   ├── services/                   # Lógica de negocio
│   │   ├── event_service.py
│   │   ├── queue_service.py
│   │   ├── purchase_service.py
│   │   └── connection_manager.py
│   └── repositories/              # Acceso a datos (MySQL + Redis)
│       ├── event_repository.py
│       ├── ticket_repository.py
│       ├── buyer_repository.py
│       ├── payment_repository.py
│       ├── queue_history_repository.py
│       └── redis_repository.py
└── tests/
    ├── conftest.py                 # Fixtures de pytest
    ├── test_basic.py               # Tests de endpoints
    ├── test_logic.py               # Tests de schemas y validación
    ├── test_worker.py              # Tests unitarios del Worker aislando a Redis
    ├── test_integration.py         # Tests de integración end-to-end
    └── load/                       # Tests de carga (k6)
        └── scripts/
            ├── smoke-test.js
            ├── endpoints-test.js
            ├── full-flow-test.js
            └── stress-test.js
```

---

## 🖥️ Frontend

### Páginas y Flujo de Usuario

| Ruta | Página | Descripción |
|---|---|---|
| `/` | **Home** | Landing page con listado de eventos activos |
| `/evento/[eventId]` | **Detalle del evento** | Información, estadísticas y botón para entrar a la fila |
| `/cola/[eventId]` | **Sala de espera** | Fila virtual con posición en tiempo real y estadísticas en vivo |
| `/compra/[eventId]` | **Formulario de compra** | Completar datos del comprador y procesar el pago |
| `/ticket/[ticketId]` | **Confirmación** | Ticket confirmado con código único |
| `/nosotros` | **Nosotros** | Información sobre el proyecto |

### Componentes principales

| Componente | Función |
|---|---|
| `EventCard` | Tarjeta de evento en la landing page |
| `EventHero` | Hero section del detalle del evento |
| `EventInfoCards` | Tarjetas informativas (fecha, precio, capacidad) |
| `EnterQueueForm` | Formulario para unirse a la fila |
| `QueueStatus` | Visualización de la posición en la fila |
| `LiveStats` | Estadísticas en tiempo real del evento |
| `TurnNotification` | Notificación cuando llega el turno |
| `PurchaseForm` | Formulario de datos del comprador y pago |
| `TicketConfirmation` | Vista de ticket comprado exitosamente |
| `ParticleTunnel` | Animación de loading con partículas |
| `SimulationHUD` | Panel de control de la simulación |
| `SimulationDrawer` | Drawer lateral para simulación avanzada |

### Estructura del Frontend

```
frontend/
├── public/                      # Archivos estáticos
├── src/
│   ├── app/                     # App Router (Next.js)
│   │   ├── layout.tsx           # Layout raíz (Header + Footer)
│   │   ├── page.tsx             # Home — Landing page
│   │   ├── globals.css          # Estilos globales
│   │   ├── evento/[eventId]/    # Detalle del evento
│   │   ├── cola/[eventId]/      # Sala de espera (fila virtual)
│   │   ├── compra/[eventId]/    # Formulario de compra
│   │   ├── ticket/[ticketId]/   # Confirmación del ticket
│   │   └── nosotros/            # Página informativa
│   ├── components/              # Componentes reutilizables
│   │   ├── common/              # Header, Footer, etc.
│   │   ├── EventCard/
│   │   ├── QueueStatus/
│   │   ├── LiveStats/
│   │   ├── PurchaseForm/
│   │   └── ...
│   ├── lib/                     # Utilidades y servicios
│   │   ├── api.ts               # Cliente HTTP para la API
│   │   ├── websocket.ts         # Cliente WebSocket
│   │   └── utils.ts             # Funciones utilitarias
│   └── types/
│       └── index.ts             # Definición de tipos TypeScript
├── package.json
├── tsconfig.json
└── next.config.ts
```

---

## 🧪 Testing

### Tests Unitarios y de Integración (Backend)

Con los contenedores ya corriendo (`docker compose up -d`), ejecutá este comando en tu terminal. El comando entra al contenedor `vq_api` (que ya tiene Python y las dependencias instaladas) y ejecuta pytest. **Los resultados se muestran directamente en tu terminal.**

```bash
# Ejecutar tests dentro del contenedor
docker compose exec api python -m pytest tests/ -v
```

El flag `-v` muestra cada test individual con su resultado (PASSED/FAILED). Los tests incluyen:

- **`test_basic.py`** (8 tests) — Verifican endpoints HTTP: health check, rutas 404, validaciones de request body (422) para cada endpoint.
- **`test_logic.py`** (15 tests) — Verifican schemas Pydantic (validación de datos de entrada) y la jerarquía de excepciones del dominio.
- **`test_worker.py`** (4 tests) — Pruebas unitarias aisladas del procesador en background. Verifica la correcta segregación de cuotas de abandono, actualizaciones y apagado seguro sin depender de bases de datos.
- **`test_integration.py`** — Pruebas reales de negocio. Verifica el orden FIFO de la fila usando Redis, comprueba que las compras descuentan atómicamente la capacidad del evento en MySQL, valida la salud de la conexión a caché, y verifica el handshake de conexiones WebSocket.

### Tests de Carga (k6 + Grafana)

El proyecto incluye un stack de testing que permite ejecutar pruebas de estrés con **k6** y visualizar las métricas en tiempo real en un dashboard de **Grafana**.

#### Levantar el stack de testing

Con los contenedores principales ya corriendo (`docker compose up -d`), ejecutar:

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d
```

Esto agrega 3 servicios adicionales:

| Contenedor | Servicio | Puerto |
|---|---|---|
| `virtual-queue-influxdb` | Almacenamiento de métricas | `8086` |
| `virtual-queue-grafana` | Dashboard de monitoreo | `3001` |
| `virtual-queue-k6` | Runner de tests (se ejecuta bajo demanda) | — |

#### Ejecutar un test de carga

Ejemplo con el Smoke Test (10 usuarios virtuales durante 30 segundos):

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm --entrypoint "k6 run /scripts/smoke-test.js" k6
```

Mientras el test corre, abrí **http://localhost:3001** en el navegador para ver el dashboard de Grafana con las métricas en tiempo real.

#### Escenarios disponibles

| # | Script | Usuarios | Duración | Objetivo |
|---|---|---|---|---|
| 1 | `smoke-test.js` | 10 VUs | 30s | Verificar que todos los endpoints funcionan |
| 2 | `endpoints-test.js` | 0 → 1.000 / endpoint | ~14 min | Identificar cuellos de botella por endpoint |
| 3 | `full-flow-test.js` | 0 → 1.000 | ~6 min | Flujo completo con WebSocket bajo carga |
| 4 | `stress-test.js` | 0 → 10.000 → 0 | ~12 min | Encontrar el punto de quiebre del sistema |

Para ejecutar cualquier otro escenario, reemplazá `smoke-test.js` por el nombre del script en el comando anterior.

#### Criterios de Éxito

| Métrica | Smoke | Load | Stress |
|---|---|---|---|
| **Latencia p95** | < 2s | < 3s | < 10s |
| **Tasa de error** | < 5% | < 10% | < 30% |
| **Checks OK** | > 95% | > 90% | — |

Para más detalles sobre métricas custom, interpretación de resultados y orden de ejecución recomendado, ver [`docs/TESTING.md`](docs/TESTING.md).

---

## ⚙️ Variables de Entorno

Estas variables configuran el comportamiento del backend. Se definen en el archivo `.env` (copiado desde `.env.example`). **Si usás Docker Compose, los valores por defecto ya funcionan sin modificar nada.** Solo necesitás cambiarlos si corrés la aplicación localmente sin Docker o querés ajustar el comportamiento del worker.

| Variable | Descripción | Valor por defecto | Cuándo modificarla |
|---|---|---|---|
| `REDIS_URL` | Dirección interna de Redis dentro de Docker | `redis://redis:6379/0` | Solo si corrés Redis localmente (`redis://localhost:6379/0`) |
| `DATABASE_URL` | Dirección interna de MySQL dentro de Docker | `mysql+asyncmy://root:secret@db:3306/virtual_queue` | Solo si corrés MySQL localmente (`...@localhost:3306/...`) |
| `ENVIRONMENT` | Entorno de ejecución | `development` | Cambiar a `production` en deploy |
| `LOG_LEVEL` | Nivel de logging en consola | `INFO` | Cambiar a `DEBUG` para más detalle |
| `CORS_ORIGINS` | Qué dominios pueden consumir la API | `http://localhost:3000` | Si el frontend corre en otro puerto/dominio |
| `BATCH_SIZE` | Cuántos usuarios procesa el worker por ciclo | `10` | Aumentar para procesar la fila más rápido |
| `PROCESS_INTERVAL` | Cada cuántos segundos el worker procesa un lote | `1` | Aumentar para ralentizar el procesamiento |
| `ALLOWED_TTL` | Segundos que tiene el usuario para comprar cuando le toca el turno | `300` (5 min) | Ajustar según la complejidad del formulario de compra |
| `RECONNECT_GRACE_PERIOD` | Segundos de gracia si se desconecta el WebSocket | `30` | Aumentar en redes inestables |

---

## 📁 Estructura del Proyecto

```
Virtual Queue/
│
├── 📄 README.md                        # ← Este archivo
├── 📄 .env.example                     # Variables de entorno (template)
├── 📄 .gitignore                       # Archivos excluidos de Git
├── 🐳 docker-compose.yml              # Orquestación principal (4 servicios)
├── 🐳 docker-compose.test.yml         # Stack de testing (k6 + InfluxDB + Grafana)
│
├── ⚙️  config/
│   └── redis.conf                      # Configuración de Redis (persistencia, memoria, clientes)
│
├── 🗃️  migrations/
│   └── init.sql                        # Schema inicial de MySQL (5 tablas)
│
├── 📚 docs/
│   ├── ARCHITECTURE.md                 # Documentación de arquitectura (C4 Model)
│   ├── TESTING.md                      # Plan de pruebas de carga
│   └── diagrams/                       # Diagramas C4, secuencia, ER, infraestructura
│
├── 🐍 backend/
│   ├── Dockerfile                      # Imagen Docker (API + Worker)
│   ├── requirements.txt                # Dependencias Python
│   ├── pyproject.toml                  # Configuración de herramientas de desarrollo
│   ├── README.md                       # Documentación específica del backend
│   ├── app/
│   │   ├── main.py                     # Punto de entrada FastAPI
│   │   ├── config.py                   # Configuración (env vars)
│   │   ├── database.py                 # Conexión async a MySQL
│   │   ├── redis.py                    # Pool de conexión a Redis
│   │   ├── dependencies.py             # Inyección de dependencias
│   │   ├── exceptions.py               # Excepciones del dominio
│   │   ├── worker.py                   # Procesador de fila (background)
│   │   ├── seed.py                     # Datos iniciales de prueba
│   │   ├── middleware/                 # Error handling global
│   │   ├── models/                     # Modelos SQLAlchemy (ORM)
│   │   ├── schemas/                    # Schemas Pydantic (validación)
│   │   ├── routers/                    # Endpoints HTTP y WebSocket
│   │   ├── services/                   # Lógica de negocio
│   │   └── repositories/              # Acceso a datos (MySQL + Redis)
│   └── tests/
│       ├── test_basic.py               # Tests de endpoints
│       ├── test_logic.py               # Tests de schemas y validación
│       ├── test_worker.py              # Tests unitarios del Worker
│       ├── test_integration.py         # Tests de integración
│       └── load/                       # Tests de carga (k6 scripts)
│           └── scripts/
│               ├── smoke-test.js
│               ├── endpoints-test.js
│               ├── full-flow-test.js
│               └── stress-test.js
│
└── ⚛️  frontend/
    ├── README.md                       # Documentación específica del frontend
    ├── package.json                    # Dependencias Node.js
    ├── tsconfig.json                   # Configuración TypeScript
    ├── next.config.ts                  # Configuración Next.js
    └── src/
        ├── app/                        # App Router (páginas)
        ├── components/                 # Componentes React
        ├── lib/                        # API client, WebSocket, utilidades
        └── types/                      # Tipos TypeScript
```

---

## 🗄️ Modelo de Datos

La base de datos MySQL contiene 5 tablas:

```
┌───────────┐     ┌───────────┐     ┌────────────┐
│  buyers   │────►│  tickets  │◄────│   events   │
│           │     │           │     │            │
│ id (PK)   │     │ id (PK)   │     │ id (PK)    │
│ first_name│     │ buyer_id  │     │ name       │
│ last_name │     │ event_id  │     │ capacity   │
│ dni       │     │ ticket_code│    │ price      │
│ email     │     │ price_paid│     │ status     │
└───────────┘     │ quantity  │     └────────────┘
                  │ status    │            │
                  └─────┬─────┘            │
                        │           ┌──────┴───────┐
                  ┌─────┴─────┐     │queue_history │
                  │ payments  │     │              │
                  │           │     │ user_id      │
                  │ id (PK)   │     │ event_id     │
                  │ ticket_id │     │ position     │
                  │ amount    │     │ wait_time    │
                  │ method    │     │ exit_reason  │
                  │ reference │     └──────────────┘
                  └───────────┘
```

---

## 🧑‍💻 Desarrollo Local (sin Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Ajustar .env para apuntar a servicios locales:
# REDIS_URL=redis://localhost:6379/0
# DATABASE_URL=mysql+asyncmy://root:secret@localhost:3306/virtual_queue

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

**Importante:** Para desarrollo local sin Docker, es necesario tener MySQL 8 y Redis 7 corriendo localmente o accesibles por red.

---

## 📚 Documentación

| Documento | Descripción |
|---|---|
| [`backend/README.md`](backend/README.md) | Documentación detallada del backend |
| [`frontend/README.md`](frontend/README.md) | Documentación específica del frontend |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Arquitectura del sistema (C4 Model) |
| [`docs/TESTING.md`](docs/TESTING.md) | Plan de pruebas de carga |
| [`docs/diagrams/`](docs/diagrams/) | Diagramas técnicos (C4, secuencia, ER, infraestructura) |
| [Swagger UI](http://localhost:8000/docs) | Documentación interactiva de la API (requiere API corriendo) |

---

## 📄 Licencia

Proyecto de desarrollo full-stack con enfoque principal en backend, abarcando arquitectura de sistemas distribuidos, procesamiento concurrente en tiempo real y orquestación de servicios contenerizados.

---

<p align="center">
  Desarrollado con ❤️ usando <strong>FastAPI</strong>, <strong>Next.js</strong>, <strong>Redis</strong> y <strong>MySQL</strong>
</p>
