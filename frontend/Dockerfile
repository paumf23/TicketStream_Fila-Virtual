# ═══════════════════════════════════════════════════════════════════════════════
# Dockerfile — Entorno de Ejecución para Frontend (Multi-Stage Next.js)
# ═══════════════════════════════════════════════════════════════════════════════

# --- STAGE 1: Instalación de Dependencias ---
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
# npm ci instala estrictamente según el package-lock.json
RUN npm ci

# --- STAGE 2: Construcción de la app ---
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
# Construye usando la configuración "standalone"
RUN npm run build

# --- STAGE 3: Servidor Productivo Final ---
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Copiamos estáticos públicos
COPY --from=builder /app/public ./public

# Copiamos el servidor empaquetado y estáticos autogenerados
# Solo copiamos lo necesario del .next/standalone y static
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

# Ejecutamos el servidor de node nativo en lugar del comando engorroso de npm
CMD ["node", "server.js"]
