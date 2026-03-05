
# ═══════════════════════════════════════════════════════════════════════════════
# main.py — Punto de Entrada y Corazón de la Aplicación
# ═══════════════════════════════════════════════════════════════════════════════
# Este archivo es el corazón de la aplicación porque es el ORQUESTADOR.
# Los routers, services y repositories son módulos independientes que por sí
# solos no hacen nada: necesitan que main.py los ensamble y los conecte.
#
# Responsabilidades concretas:
#   1. Crea la instancia de FastAPI (el objeto central que ES la aplicación).
#   2. Configura el ciclo de vida (lifespan): qué ocurre al encender y apagar.
#   3. Habilita CORS para que el frontend pueda comunicarse con el backend.
#   4. Registra (monta) todos los routers bajo sus prefijos correspondientes.
#
#
# Ejecución:
#   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# ═══════════════════════════════════════════════════════════════════════════════


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


# ═══════════════════════════════════════════════════════════════════════════════
# LIFESPAN — Ciclo de Vida de la Aplicación
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida del servidor."""

    # ── STARTUP ──────────────────────────────────────────────────────────────
    from app.database import engine, Base
    from app.redis import redis_pool
    try:
        await redis_pool.ping()
        print("✅ Redis conectado")
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        raise

    
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ MySQL: tablas verificadas/creadas")

    print(f"🚀 Virtual Queue API iniciada (env: {settings.ENVIRONMENT})")

    # ── YIELD (línea divisoria temporal) ─────────────────────────────────────
    
    yield

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    await redis_pool.aclose()
    print("🔌 Redis desconectado")

    await engine.dispose()
    print("🔌 MySQL desconectado")

    print("👋 Virtual Queue API finalizada")


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
