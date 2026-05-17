# C4 Nivel 3: Diagrama de Componentes

## Descripción

Este diagrama muestra los componentes internos del API Server (FastAPI) y del Frontend App (Next.js), detallando servicios, controladores y su interacción.

## Diagrama - API Server

```mermaid
C4Component
    title Virtual Queue - Componentes de API Server

    Container_Boundary(api, "API Server (FastAPI)") {
        Component(router, "API Router", "FastAPI Router", "Enruta requests a los endpoints correspondientes")
        
        Component(queueController, "Queue Controller", "Python", "Endpoints: /enter, /position, /leave")
        Component(purchaseController, "Purchase Controller", "Python", "Endpoints: /purchase, /verify")
        Component(eventController, "Event Controller", "Python", "Endpoints: /events, /events/{id}")
        Component(wsHandler, "WebSocket Handler", "FastAPI WebSocket", "Conexiones WS, push de actualizaciones")
        
        Component(queueService, "Queue Service", "Python", "Lógica de cola: agregar, posición, remover")
        Component(purchaseService, "Purchase Service", "Python", "Lógica de compra: verificar permiso, procesar, confirmar")
        Component(eventService, "Event Service", "Python", "Lógica de eventos: crear, listar, verificar capacidad")
        
        Component(redisRepo, "Redis Repository", "Python + redis-py", "Abstracción de operaciones Redis")
        Component(mysqlRepo, "MySQL Repository", "Python + SQLAlchemy", "Abstracción de operaciones MySQL")
    }

    Container_Ext(frontend, "Frontend App", "Next.js + React")
    ContainerDb_Ext(redis, "Redis", "In-memory store")
    ContainerDb_Ext(mysql, "MySQL", "Relational DB")

    Rel(frontend, router, "API REST calls", "HTTPS")
    Rel(frontend, wsHandler, "WebSocket", "WSS")

    Rel(router, queueController, "Delega")
    Rel(router, purchaseController, "Delega")
    Rel(router, eventController, "Delega")
    
    Rel(queueController, queueService, "Usa")
    Rel(purchaseController, purchaseService, "Usa")
    Rel(eventController, eventService, "Usa")
    
    Rel(queueService, redisRepo, "Lee/escribe cola")
    Rel(purchaseService, redisRepo, "Verifica permisos")
    Rel(purchaseService, mysqlRepo, "Persiste tickets")
    Rel(eventService, mysqlRepo, "Lee/escribe eventos")
    
    Rel(redisRepo, redis, "Redis Protocol")
    Rel(mysqlRepo, mysql, "MySQL Protocol")
    Rel(wsHandler, redisRepo, "Subscribe Pub/Sub")
```

## Componentes del API Server

### Controllers (Capa de Presentación)

| Componente | Endpoints | Responsabilidad |
|------------|-----------|-----------------|
| **Queue Controller** | `POST /api/queue/enter`<br>`GET /api/queue/position/{id}`<br>`DELETE /api/queue/leave/{id}` | Manejar entrada/salida de cola |
| **Purchase Controller** | `POST /api/tickets/purchase`<br>`GET /api/tickets/verify/{id}` | Procesar y verificar compras |
| **Event Controller** | `GET /api/events`<br>`GET /api/events/{id}`<br>`POST /api/events` (admin) | CRUD de eventos |
| **WebSocket Handler** | `WS /ws/{user_id}` | Conexiones persistentes, push de actualizaciones de posición |

### Services (Capa de Aplicación)

| Componente | Métodos Principales | Lógica de Negocio |
|------------|---------------------|-------------------|
| **Queue Service** | `enter_queue()`, `get_position()`, `leave_queue()` | Asignar posición, calcular espera estimada |
| **Purchase Service** | `verify_permission()`, `process_purchase()`, `confirm()` | Verificar TTL, decrementar capacidad atómicamente |
| **Event Service** | `create()`, `get_available()`, `check_capacity()` | Validar fechas, verificar stock |

### Repositories (Capa de Infraestructura)

| Componente | Operaciones |
|------------|-------------|
| **Redis Repository** | `lpush()`, `queue_pop_safe()` (Lua), `llen()`, `hset()`, `hget()`, `hdel()`, `publish()` |
| **MySQL Repository** | `insert_ticket()`, `insert_buyer()`, `insert_payment()`, `get_event()`, `update_capacity()` |

---

## Diagrama - Frontend App

```mermaid
C4Component
    title Virtual Queue - Componentes de Frontend App

    Container_Boundary(frontend, "Frontend App (Next.js)") {
        Component(pages, "Pages (App Router)", "Next.js 14+", "/ (landing), /event/[id], /queue/[id], /purchase/[id]")
        Component(components, "UI Components", "React", "QueueStatus, Timer, TicketCard, EventList, ProgressBar")
        Component(hooks, "Custom Hooks", "React", "useWebSocket, useQueue, useCountdown, useAuth")
        Component(apiClient, "API Client", "TypeScript + fetch", "Wrapper tipado para comunicación con FastAPI")
        Component(stateManager, "State Management", "React Context / Zustand", "Estado global: usuario, posición en cola, permisos")
    }

    Container_Ext(api, "API Server", "FastAPI")

    Rel(pages, components, "Renderiza")
    Rel(pages, hooks, "Usa")
    Rel(hooks, apiClient, "Llama API REST")
    Rel(hooks, stateManager, "Lee/escribe estado")
    Rel(apiClient, api, "HTTPS / WSS")
```

### Páginas (App Router)

| Ruta | Componente | Descripción |
|------|------------|-------------|
| `/` | `page.tsx` | Landing — lista de eventos disponibles |
| `/event/[id]` | `page.tsx` | Detalle del evento, botón "Entrar a la cola" |
| `/queue/[id]` | `page.tsx` | Sala de espera — posición en tiempo real, barra de progreso |
| `/purchase/[id]` | `page.tsx` | Pantalla de compra — timer de 5 min, formulario de pago |

### Custom Hooks

| Hook | Responsabilidad |
|------|-----------------|
| `useWebSocket(url)` | Conectar/reconectar WebSocket, parsear mensajes |
| `useQueue(eventId)` | Estado de la cola: posición, estimado, turno |
| `useCountdown(seconds)` | Timer regresivo para TTL de 5 minutos |
| `useAuth()` | Session token del usuario |

---

## Diagrama - Queue Worker

```mermaid
C4Component
    title Virtual Queue - Componentes de Queue Worker

    Container_Boundary(worker, "Queue Worker") {
        Component(scheduler, "Scheduler", "Python + asyncio", "Loop cada 1 segundo")
        Component(batchProcessor, "Batch Processor", "Python", "Procesa lotes de 10 usuarios")
        Component(notifier, "Notifier", "Python", "Publica actualizaciones via Pub/Sub")
        Component(redisClient, "Redis Client", "redis-py async", "Conexión a Redis")
    }

    ContainerDb_Ext(redis, "Redis", "In-memory store")

    Rel(scheduler, batchProcessor, "Dispara cada segundo")
    Rel(batchProcessor, redisClient, "EVAL queue_pop_safe (Atómico)")
    Rel(batchProcessor, redisClient, "HSET allowed_users + TTL")
    Rel(batchProcessor, redisClient, "DEL processing (Cleanup)")
    Rel(batchProcessor, notifier, "Usuarios movidos")
    Rel(notifier, redisClient, "PUBLISH position_updates")
    Rel(redisClient, redis, "Redis Protocol")
```

### Flujo del Worker

```python
# Pseudocódigo del Worker
async def process_batch():
    while True:
        # 1. Mover lote de la cola a lista de procesamiento (atómico via Lua)
        users = await redis_repo.queue_pop_safe(event_id, batch_size=10)
        
        for user_id in users:
            # 2. Agregar a permitidos con TTL de 5 minutos
            await redis_repo.set_allowed(event_id, user_id, ttl=300)
        
        # 3. Limpiar lista de procesamiento (batch exitoso)
        await redis_repo.clear_processing(event_id)
        
        # 3. Notificar a todos los conectados
        await redis.publish("position_updates", json.dumps({
            "moved": len(users),
            "queue_length": await redis.llen("waiting_queue")
        }))
        
        # 4. Esperar 1 segundo
        await asyncio.sleep(1)
```
