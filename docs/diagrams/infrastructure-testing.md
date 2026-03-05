# Diagrama de Infraestructura de Testing

## Descripción

Este diagrama muestra la arquitectura de contenedores Docker para el entorno de load testing con k6, Grafana e InfluxDB.

## Diagrama de Contenedores — Stack de Testing

```mermaid
flowchart TB
    subgraph docker["Docker Host"]
        subgraph main_stack["Stack Principal (docker-compose.yml)"]
            direction TB
            frontend["📦 frontend (Next.js)\n:3000"]
            api["📦 api (FastAPI)\n:8000"]
            worker["📦 worker"]
            redis["📦 redis\n:6379"]
            mysql["📦 mysql\n:3306"]
        end

        subgraph test_stack["Stack de Testing (docker-compose.test.yml)"]
            direction TB
            k6["📦 k6 (Grafana k6)\nRunner de tests"]
            influxdb["📦 influxdb\n:8086"]
            grafana["📦 grafana\n:3001"]
        end
    end

    dev["👤 Developer"]

    dev -->|"Ejecuta tests"| k6
    dev -->|"Ve dashboard\nhttp://localhost:3001"| grafana

    k6 -->|"HTTP requests\nsimulando usuarios"| api
    k6 -->|"WebSocket\nconexiones"| api
    k6 -->|"Envía métricas"| influxdb

    grafana -->|"Lee métricas"| influxdb

    api <-->|"6379"| redis
    api <-->|"3306"| mysql
    worker <-->|"6379"| redis
    frontend -->|"HTTP :8000"| api
```

## Flujo de Datos del Testing

```mermaid
sequenceDiagram
    participant D as Developer
    participant K as k6
    participant API as FastAPI (API)
    participant I as InfluxDB
    participant G as Grafana

    D->>K: Ejecutar test script
    
    loop Por cada usuario virtual
        K->>API: HTTP/WebSocket requests
        API-->>K: Responses
        K->>I: Enviar métricas (latencia, errores, etc.)
    end

    D->>G: Abrir dashboard (localhost:3001)
    G->>I: Consultar métricas
    I-->>G: Series temporales
    G-->>D: Dashboard en tiempo real
```

## Red Docker

Todos los contenedores (tanto del stack principal como del stack de testing) están conectados a la misma red `virtual-queue-network`. Esto permite que k6 acceda a la API por nombre de host (`http://api:8000`) sin exponer puertos adicionales.

```
┌─────────────────────────────────────────────────────────┐
│                virtual-queue-network (bridge)            │
│                                                          │
│  Stack Principal         Stack de Testing                │
│  ┌────────────┐         ┌────────────┐                  │
│  │ frontend   │         │ k6 ────────│──► api           │
│  │ api        │◄────────│            │                  │
│  │ worker     │         │ influxdb ◄─│── k6 (métricas)  │
│  │ redis      │         │            │                  │
│  │ mysql      │         │ grafana ───│──► influxdb      │
│  └────────────┘         └────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## Comandos de Testing

```bash
# ── Preparación ─────────────────────────────────

# 1. Levantar stack principal
docker-compose up -d

# 2. Levantar Grafana + InfluxDB (sin k6, que corre bajo demanda)
docker-compose -f docker-compose.test.yml up -d grafana influxdb

# 3. Abrir Grafana
# http://localhost:3001 (usuario: admin, password: admin)

# ── Ejecutar Tests ─────────────────────────────

# Smoke test (10 usuarios, 30 segundos)
docker-compose -f docker-compose.test.yml run k6 run /scripts/smoke-test.js

# Test de endpoints individuales (~14 minutos)
docker-compose -f docker-compose.test.yml run k6 run /scripts/endpoints-test.js

# Test de flujo completo con WebSocket (~6 minutos)
docker-compose -f docker-compose.test.yml run k6 run /scripts/full-flow-test.js

# Stress test: 0 → 10.000 gradual (~12 minutos)
docker-compose -f docker-compose.test.yml run k6 run /scripts/stress-test.js --env SCENARIO=stress

# Spike test: 0 → 10.000 de golpe (~2 minutos)
docker-compose -f docker-compose.test.yml run k6 run /scripts/stress-test.js --env SCENARIO=spike

# Stress + Spike juntos (~15 minutos)
docker-compose -f docker-compose.test.yml run k6 run /scripts/stress-test.js

# ── Limpieza ───────────────────────────────────

# Detener stack de testing
docker-compose -f docker-compose.test.yml down

# Detener todo (principal + testing)
docker-compose down && docker-compose -f docker-compose.test.yml down

# Eliminar datos de métricas
docker-compose -f docker-compose.test.yml down -v
```
