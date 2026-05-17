# Virtual Queue - Arquitectura del Sistema

## Modelo Arquitectónico

Este proyecto implementa una **arquitectura Event-Driven con Capas**, documentada siguiendo el **C4 Model**.

### ¿Por qué Event-Driven + Layered?

| Característica      | Beneficio para Virtual Queue                |
| ------------------- | ------------------------------------------- |
| **Asincronía**      | Miles de usuarios concurrentes sin bloquear |
| **Desacoplamiento** | Worker procesa cola independiente del API   |
| **Escalabilidad**   | Múltiples workers pueden procesar la cola   |
| **Resiliencia**     | Si el API cae, la cola en Redis persiste    |

---

## Stack Tecnológico

### Frontend
| Tecnología       | Rol                                                        |
| ---------------- | ---------------------------------------------------------- |
| **Next.js 14+**  | Framework React con App Router, SSR y API routes           |
| **React 18+**    | Librería de UI — componentes, hooks, estado                |
| **TypeScript**   | Tipado estático para mayor robustez                        |

### Backend
| Tecnología           | Rol                                                    |
| -------------------- | ------------------------------------------------------ |
| **FastAPI + Uvicorn** | API REST pura + WebSocket server                      |
| **Python + asyncio**  | Worker background que procesa la cola                 |
| **Redis 7+**          | Cola de espera, permisos (TTL), Pub/Sub               |
| **MySQL 8+**          | Persistencia: eventos, tickets, compradores, pagos    |
| **Docker**            | Contenedorización de todos los servicios              |

### Separación Frontend / Backend

```
Usuario ──► Next.js (React SSR/CSR) ──► FastAPI (API REST + WebSocket)
                                              │
                                    ┌─────────┴──────────┐
                                  Redis              MySQL
```

- **Next.js** renderiza toda la UI (landing, sala de espera, compra).
- **FastAPI** es una **API pura** — no renderiza HTML ni usa Jinja2.
- Las conexiones **WebSocket** se establecen directamente desde el browser (React) hacia FastAPI.

---

## Índice de Diagramas

1. [C4 Nivel 1: Contexto del Sistema](diagrams/Modelo%20C4/c4-context.md)
2. [C4 Nivel 2: Contenedores](diagrams/Modelo%20C4/c4-containers.md)
3. [C4 Nivel 3: Componentes](diagrams/Modelo%20C4/c4-components.md)
4. [Diagrama de Secuencia: Flujo de Cola](diagrams/sequence-queue-flow.md)
5. [Diagrama de Estados del Usuario](diagrams/state-user.md)
6. [Diagrama Entidad-Relación (MySQL)](diagrams/er-database.md)
7. [Diagrama de Infraestructura (Docker)](diagrams/infrastructure.md)
8. [Diagrama de Infraestructura de Testing (k6 + Grafana)](diagrams/infrastructure-testing.md)
9. [Plan de Pruebas de Carga](TESTING.md)

---

## Decisiones Arquitectónicas

### Next.js Standalone vs Static Export

Se optó por **Next.js standalone** (contenedor Docker propio) en lugar de static export porque:
- Se necesita **WebSocket nativo** desde el cliente React.
- **SSR** mejora el SEO y la performance de carga inicial.
- Las **API routes** de Next.js permiten proxying y middleware del lado servidor.

### Redis vs MySQL: Uso Complementario

```
┌─────────────────────────────────────────────────────────────┐
│                     REDIS (Tiempo Real)                     │
│  • Cola de espera (LIST)                                    │
│  • Usuarios permitidos (HASH + TTL 5min)                    │
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
│  • Usuarios registrados                                     │
│  • Compradores y pagos                                      │
└─────────────────────────────────────────────────────────────┘
```

### Manejo de Race Conditions

1. **Patrón Reliable Queue (Redis)**: Uso de scripts Lua para movimiento atómico de la cola a lista de procesamiento (idempotencia).
2. **Transacciones MySQL**: `BEGIN/COMMIT` para la compra de tickets
3. **TTL en Permisos**: Usuario permitido tiene 5 minutos para comprar, luego expira
4. **Verificación Doble**: Antes de confirmar compra, se verifica capacidad restante
