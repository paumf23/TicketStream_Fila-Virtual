# ═══════════════════════════════════════════════════════════════════════════════
# Dockerfile — Entorno de Ejecución para Backend y Worker (Multi-Stage)
# ═══════════════════════════════════════════════════════════════════════════════

# --- STAGE 1: Builder ---
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: Runtime ---
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencia del SO para el driver de MySQL en runtime (sin herramientas de compilación pesadas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Traemos el entorno virtual precompilado
COPY --from=builder /opt/venv /opt/venv

# Traemos el código de la aplicación
COPY . .

EXPOSE 8000

# Comando por defecto para la API (Producción)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
