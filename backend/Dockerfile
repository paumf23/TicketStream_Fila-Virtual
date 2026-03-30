
# ═══════════════════════════════════════════════════════════════════════════════
# Dockerfile — Entorno de Ejecución para Backend y Worker
# ═══════════════════════════════════════════════════════════════════════════════

# Usamos Python 3.12-slim (más moderno que el 3.11 sugerido en los diagramas)
FROM python:3.12-slim

# Evitar archivos .pyc y asegurar logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias para MySQL y compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalación de dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código del backend (asumiendo que el contexto es la carpeta backend/)
COPY . .

EXPOSE 8000

# Comando por defecto para la API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
