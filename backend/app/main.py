
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


# ═══════════════════════════════════════════════════════════════════════════════
# LIFESPAN — Ciclo de Vida de la Aplicación
# ═══════════════════════════════════════════════════════════════════════════════

import logging

# Configuración de Logging Estructurado (Básico para Consola)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando ciclo de vida de la aplicación...")

    # ── STARTUP ──────────────────────────────────────────────────────────────
    from app.database import engine, Base
    from app.redis import redis_pool
    
    # Intentar conectar a Redis (No bloqueante para el Smoke Test)
    try:
        await redis_pool.ping()
        logger.info("✅ Redis conectado correctamente")
    except Exception as e:
        logger.error(f"⚠️ Redis no disponible (Esperado sin Docker): {e}")
        # No re-lanzamos el error para permitir que la API prenda e ir al Swagger
    
    # Intentar conectar a MySQL (No bloqueante para el Smoke Test)
    try:
        if settings.ENVIRONMENT == "development":
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ MySQL: tablas verificadas/creadas")
    except Exception as e:
        logger.error(f"⚠️ MySQL no disponible (Esperado sin Docker): {e}")

    logger.info(f"🚀 Virtual Queue API iniciada (entorno: {settings.ENVIRONMENT})")

    # ── YIELD (línea divisoria temporal) ─────────────────────────────────────
    
    yield

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    await redis_pool.aclose()
    logger.info("🔌 Redis desconectado")

    await engine.dispose()
    logger.info("🔌 MySQL desconectado")

    logger.info("👋 Virtual Queue API finalizada correctamente")


# ═══════════════════════════════════════════════════════════════════════════════
# INSTANCIA DE FASTAPI
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Virtual Queue API",
    description=(
        "API REST + WebSocket para el sistema de cola virtual. "
        "Gestiona eventos masivos con cola de espera en Redis, "
        "compra de tickets con transacciones atómicas en MySQL, "
        "y actualizaciones en tiempo real vía WebSocket."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CORS (Cross-Origin Resource Sharing)
# ═══════════════════════════════════════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRO DE ROUTERS
# ═══════════════════════════════════════════════════════════════════════════════

from app.routers import health
from app.routers import events
from app.routers import queue
from app.routers import tickets
from app.routers import simulate
from app.routers import websocket_handler


app.include_router(health.router)

app.include_router(
    events.router,
    prefix="/api/events",
    tags=["Eventos"],
)

app.include_router(
    queue.router,
    prefix="/api/queue",
    tags=["Cola de Espera"],
)

app.include_router(
    tickets.router,
    prefix="/api/tickets",
    tags=["Tickets / Compras"],
)

app.include_router(
    simulate.router,
    prefix="/api/simulate",
    tags=["Simulación"],
)

app.include_router(
    websocket_handler.router,
    tags=["WebSocket"],
)
