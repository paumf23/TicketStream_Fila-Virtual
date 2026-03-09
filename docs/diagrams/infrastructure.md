# Diagrama de Infraestructura (Docker)

## Descripción

Este diagrama muestra la arquitectura de contenedores Docker y cómo se despliega el sistema.

## Diagrama de Contenedores Docker

```mermaid
flowchart TB
    subgraph internet["Internet"]
        user["👤 Usuario"]
    end
    
    subgraph docker["Docker Host"]
        subgraph network["virtual-queue-network (bridge)"]
            
            subgraph frontend_container["📦 frontend (Next.js)"]
                direction TB
                nextjs["Next.js Server"]
                react["React SSR/CSR"]
            end
            
            subgraph app_container["📦 api (FastAPI)"]
                direction TB
                uvicorn["Uvicorn ASGI"]
                fastapi["FastAPI App"]
                ws_handler["WebSocket Handler"]
            end
            
            subgraph worker_container["📦 worker (Queue Processor)"]
                direction TB
                asyncio["asyncio Loop"]
                batch_proc["Batch Processor"]
            end
            
            subgraph redis_container["📦 redis"]
                redis_server["Redis Server"]
                redis_data[("redis-data volume")]
            end
            
            subgraph mysql_container["📦 mysql"]
                mysql_server["MySQL Server"]
                mysql_data[("mysql-data volume")]
            end
            
        end
    end
    
    user -->|"HTTP :3000"| frontend_container
    user <-->|"WebSocket :8000/ws"| app_container
    
    frontend_container -->|"HTTP :8000"| app_container
    
    app_container <-->|"6379"| redis_container
    app_container <-->|"3306"| mysql_container
    
    worker_container <-->|"6379"| redis_container
    
    redis_server --- redis_data
    mysql_server --- mysql_data
```

### Mapa de Comunicación entre Contenedores

```
Internet
  │
  ├── HTTP :3000 ──► frontend (Next.js)
  │                      │
  │                      ├── HTTP :8000 ──► api (FastAPI)
  │                                           │
  │                                           ├── 6379 ◄──► redis
  │                                           └── 3306 ◄──► mysql
  │
  └── WebSocket :8000/ws ◄──► api (FastAPI)
                                  │
                worker ◄──► 6379 ──► redis
```

**Explicación de las conexiones:**

1. **Usuario → Frontend (HTTP :3000):** El usuario accede a la UI servida por Next.js. El frontend renderiza las páginas (landing, sala de espera, compra) vía SSR y CSR.
2. **Frontend → API (HTTP :8000):** El frontend se comunica con FastAPI por HTTP dentro de la red Docker interna. Envía requests REST como `POST /api/queue/enter` o `POST /api/tickets/purchase`.
3. **Usuario → API (WebSocket :8000/ws):** El browser abre una conexión WebSocket directa hacia FastAPI para recibir actualizaciones de posición en tiempo real.
4. **API → Redis (6379):** FastAPI lee y escribe en Redis — cola de espera (`waiting_queue`), permisos (`allowed_users`), y Pub/Sub para broadcasts.
5. **API → MySQL (3306):** FastAPI persiste datos en MySQL — tickets vendidos, eventos y usuarios.
6. **Worker → Redis (6379):** El Worker solo se comunica con Redis. No tiene puerto expuesto porque no recibe requests de nadie — solo corre su loop interno cada segundo procesando la cola, moviendo usuarios a `allowed_users`, y publicando actualizaciones vía Pub/Sub.

Los dos **volúmenes persistentes** (`redis-data` y `mysql-data`) aseguran que los datos sobrevivan reinicios o destrucciones de los contenedores.

## Docker Compose

```yaml
version: '3.8'

services:
  # ============================================
  # FRONTEND (Next.js + React)
  # ============================================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    container_name: virtual-queue-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
    depends_on:
      api:
        condition: service_healthy
    networks:
      - virtual-queue-network
    restart: unless-stopped

  # ============================================
  # API SERVER (FastAPI - API pura)
  # ============================================
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: virtual-queue-api
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=mysql+asyncmy://root:secret@mysql:3306/virtual_queue
      - ENVIRONMENT=development
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=http://localhost:3000
    depends_on:
      redis:
        condition: service_healthy
      mysql:
        condition: service_healthy
    networks:
      - virtual-queue-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ============================================
  # WORKER (Procesador de Cola)
  # ============================================
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: virtual-queue-worker
    command: python -m app.worker
    environment:
      - REDIS_URL=redis://redis:6379/0
      - BATCH_SIZE=10
      - PROCESS_INTERVAL=1
      - ALLOWED_TTL=300
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - virtual-queue-network
    restart: unless-stopped
    deploy:
      replicas: 1  # Puede escalar a múltiples workers

  # ============================================
  # REDIS (Cola + Cache + Pub/Sub)
  # ============================================
  redis:
    image: redis:7-alpine
    container_name: virtual-queue-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - virtual-queue-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================
  # MYSQL (Persistencia)
  # ============================================
  mysql:
    image: mysql:8.0
    container_name: virtual-queue-mysql
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=secret
      - MYSQL_DATABASE=virtual_queue
    volumes:
      - mysql-data:/var/lib/mysql
      - ./migrations/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - virtual-queue-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-psecret"]
      interval: 10s
      timeout: 5s
      retries: 10

# ============================================
# REDES
# ============================================
networks:
  virtual-queue-network:
    driver: bridge

# ============================================
# VOLÚMENES PERSISTENTES
# ============================================
volumes:
  redis-data:
    driver: local
  mysql-data:
    driver: local
```

## Dockerfile (API Server — FastAPI)

```dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependencias de sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para cachear
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Crear usuario no-root
RUN addgroup --system app && adduser --system --group app

# Copiar wheels desde builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copiar código de la API (sin templates ni static)
COPY ./app ./app

# Cambiar a usuario no-root
USER app

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Dockerfile.frontend (Next.js)

```dockerfile
# ============================================
# Stage 1: Dependencies
# ============================================
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --only=production

# ============================================
# Stage 2: Builder
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ============================================
# Stage 3: Production
# ============================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Crear usuario no-root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copiar archivos necesarios
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

## Estructura de Directorios (Real)

```
Virtual Queue/
├── docker-compose.yml          # Orquestador (MySQL, Redis, API, Worker)
├── backend/                    # Contenedor de toda la lógica del servidor
│   ├── Dockerfile              # Imagen para API y Worker
│   ├── requirements.txt        # Dependencias de Python
│   ├── app/                    # Código fuente FastAPI
│   │   ├── main.py             # Punto de entrada
│   │   ├── worker.py           # Procesador de cola
│   │   ├── seed.py             # Script de carga de datos iniciales
│   │   ├── database.py         # Configuración SQLAlchemy
│   │   ├── redis.py            # Cliente de Redis
│   │   ├── config.py           # Variables de entorno
│   │   ├── dependencies.py     # Inyectores de FastAPI
│   │   ├── models/             # Tablas MySQL (Base)
│   │   ├── repositories/       # Acceso a datos (SQL/Redis)
│   │   ├── services/           # Lógica de negocio (Complejo)
│   │   │   └── connection_manager.py  # Gestor de WebSockets
│   │   ├── routers/            # Endpoints de la API
│   │   │   └── simulate.py     # Simulación de carga
│   │   └── schemas/            # Validación Pydantic
│   └── tests/                  # Pruebas unitarias/integración
├── frontend/                   # Aplicación Next.js (Actualmente vacío)
│   └── [Estructura planeada: src/, components/, etc.]
├── docs/                       # Documentación y Diagramas
│   ├── ARCHITECTURE.md
│   └── diagrams/
└── migrations/                 # [Planeado] Inicialización SQL
```

## Comandos de Desarrollo

```bash
# Iniciar todo el stack (5 contenedores)
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f frontend api worker

# Escalar workers (para pruebas de carga)
docker-compose up -d --scale worker=3

# Reiniciar solo el frontend
docker-compose restart frontend

# Reiniciar solo la API (sin perder datos)
docker-compose restart api

# Desarrollo local del frontend (sin Docker)
cd frontend && npm run dev

# Detener y limpiar
docker-compose down

# Detener y eliminar volúmenes (¡CUIDADO!)
docker-compose down -v
```
