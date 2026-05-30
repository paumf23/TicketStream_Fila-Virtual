#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# init-letsencrypt.sh — Genera certificados temporales para que Nginx arranque
# ═══════════════════════════════════════════════════════════════════════════════
# Nginx necesita que existan los archivos de certificado SSL antes de iniciar.
# Este script genera un certificado autofirmado temporal que permite arrancar
# el stack por primera vez. Después, cuando agregues el contenedor de Certbot,
# este reemplazará los certificados temporales por los reales de Let's Encrypt.
#
# USO:
#   chmod +x init-letsencrypt.sh
#   ./init-letsencrypt.sh
#   docker compose -f docker-compose.prod.yml up -d --build
# ═══════════════════════════════════════════════════════════════════════════════

set -e

DOMAIN="ticketstream.ddns.net"
CERT_DIR="./certbot/conf/live/$DOMAIN"

echo "══════════════════════════════════════════════════════════"
echo "  Generando certificados temporales para: $DOMAIN"
echo "══════════════════════════════════════════════════════════"

# Crear la estructura de directorios
mkdir -p "$CERT_DIR"
mkdir -p "./certbot/www"

# Generar certificado autofirmado temporal (válido por 1 año)
openssl req -x509 -nodes -newkey rsa:2048 \
  -days 365 \
  -keyout "$CERT_DIR/privkey.pem" \
  -out "$CERT_DIR/fullchain.pem" \
  -subj "/CN=$DOMAIN" \
  2>/dev/null

echo ""
echo "✅ Certificados temporales creados en: $CERT_DIR/"
echo "   - fullchain.pem (certificado)"
echo "   - privkey.pem   (clave privada)"
echo ""
echo "⚠️  Estos son certificados AUTOFIRMADOS (el navegador mostrará una"
echo "   advertencia de seguridad). Se reemplazarán automáticamente cuando"
echo "   configures el contenedor de Certbot."
echo ""
echo "📋 Siguiente paso:"
echo "   docker compose -f docker-compose.prod.yml up -d --build"
echo "══════════════════════════════════════════════════════════"
