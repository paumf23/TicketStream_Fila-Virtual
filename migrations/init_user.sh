#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# init_user.sh — Crear usuario dedicado para la app en MySQL
# ═══════════════════════════════════════════════════════════════════════════════
# Este script se ejecuta automáticamente UNA SOLA VEZ cuando MySQL se inicializa
# por primera vez (carpeta de datos vacía). Crea el usuario 'vq_app' con permisos
# limitados: solo puede leer, guardar, actualizar y borrar filas.
# NO puede destruir tablas, modificar la estructura ni acceder a otras bases.
#
# Las variables MYSQL_APP_USER y MYSQL_APP_PASSWORD vienen del archivo .env
# a través de docker-compose.prod.yml.
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Solo ejecutar si las variables están definidas (producción)
if [ -n "$MYSQL_APP_USER" ] && [ -n "$MYSQL_APP_PASSWORD" ]; then
    echo "🔒 Creando usuario dedicado '$MYSQL_APP_USER' para la aplicación..."

    mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<-EOSQL
        CREATE USER IF NOT EXISTS '${MYSQL_APP_USER}'@'%' IDENTIFIED BY '${MYSQL_APP_PASSWORD}';
        GRANT SELECT, INSERT, UPDATE, DELETE ON virtual_queue.* TO '${MYSQL_APP_USER}'@'%';
        FLUSH PRIVILEGES;
EOSQL

    echo "✅ Usuario '$MYSQL_APP_USER' creado con permisos limitados."
else
    echo "ℹ️  Variables MYSQL_APP_USER/MYSQL_APP_PASSWORD no definidas. Saltando creación de usuario dedicado."
fi
