# Virtual Queue — Plan de Pruebas de Carga

## Objetivo

Verificar que el sistema Virtual Queue soporta **10.000 usuarios concurrentes** con tiempos de respuesta aceptables y sin pérdida de datos.

## Stack de Testing

| Herramienta | Rol | URL |
|-------------|-----|-----|
| **k6** (Grafana Labs) | Ejecuta los tests de carga | CLI |
| **InfluxDB** | Almacena métricas de cada test | `localhost:8086` |
| **Grafana** | Dashboard visual en tiempo real | `localhost:3001` |

## Escenarios de Test

### 1. Smoke Test (`smoke-test.js`)

| Parámetro | Valor |
|-----------|-------|
| Usuarios | 10 VUs |
| Duración | 30 segundos |
| Objetivo | Verificar que todos los endpoints funcionan |

**Endpoints probados:** `GET /health`, `GET /api/events`, `POST /api/queue/enter`, `DELETE /api/queue/leave`

---

### 2. Endpoints Test (`endpoints-test.js`)

| Parámetro | Valor |
|-----------|-------|
| Usuarios | 0 → 1.000 por endpoint |
| Duración | ~14 minutos (3.5 min por endpoint) |
| Objetivo | Identificar cuellos de botella por endpoint |

**Endpoints:** Cada uno se testea de forma aislada con métricas custom (`endpoint_queue_enter_duration`, `endpoint_purchase_duration`, etc.)

---

### 3. Full Flow Test (`full-flow-test.js`)

| Parámetro | Valor |
|-----------|-------|
| Usuarios | 0 → 1.000 |
| Duración | ~6 minutos |
| Objetivo | Verificar el flujo completo con WebSocket |

**Flujo:** Entrar a cola → Conectar WebSocket → Esperar turno → Comprar ticket → Cerrar WebSocket

---

### 4. Stress Test (`stress-test.js --env SCENARIO=stress`)

| Parámetro | Valor |
|-----------|-------|
| Usuarios | 0 → 500 → 1.000 → 5.000 → 10.000 → 0 |
| Duración | ~12 minutos |
| Objetivo | Encontrar el punto de quiebre del sistema |

**Progresión gradual** para identificar en qué número de usuarios la latencia se degrada.

---

### 5. Spike Test (`stress-test.js --env SCENARIO=spike`)

| Parámetro | Valor |
|-----------|-------|
| Usuarios | 0 → 10.000 en 10 segundos |
| Duración | ~2 minutos |
| Objetivo | Verificar resiliencia ante picos repentinos |

**Simula** el momento exacto en que abren las ventas de un evento masivo.

---

## Métricas y Criterios de Éxito

### Thresholds (criterios de aprobación/fallo)

| Métrica | Smoke | Load | Stress | Spike |
|---------|-------|------|--------|-------|
| **Latencia p95** | < 2s | < 3s | < 10s | < 10s |
| **Tasa de error** | < 5% | < 10% | < 30% | < 30% |
| **Checks OK** | > 95% | > 90% | — | — |
| **WS errors** | — | < 10% | — | — |

### Métricas Custom

| Métrica | Descripción |
|---------|-------------|
| `endpoint_queue_enter_duration` | Latencia de `POST /queue/enter` |
| `endpoint_purchase_duration` | Latencia de `POST /tickets/purchase` |
| `flow_queue_wait_time` | Tiempo total en la cola (WebSocket) |
| `flow_purchase_time` | Tiempo de la transacción de compra |
| `flow_completed_total` | Flujos completados exitosamente |
| `flow_failed_total` | Flujos fallidos |
| `ws_messages_received_total` | Total de mensajes WebSocket recibidos |
| `ws_connection_errors` | Tasa de errores de conexión WebSocket |

## Orden de Ejecución Recomendado

```
1° Smoke Test      → ¿Funciona todo?
        │ OK
        ▼
2° Endpoints Test  → ¿Algún endpoint es lento?
        │ OK
        ▼
3° Full Flow Test  → ¿El flujo con WebSocket funciona bajo carga?
        │ OK
        ▼
4° Stress Test     → ¿Hasta cuántos usuarios soporta?
        │ OK
        ▼
5° Spike Test      → ¿Sobrevive un pico de 10.000 de golpe?
```

## Interpretación de Resultados en Grafana

### Dashboard: Virtual Queue — k6 Load Testing

| Panel | Qué buscar |
|-------|-----------|
| **Virtual Users** | Verificar que la rampa de usuarios sigue el patrón esperado |
| **Requests/s** | Debería subir proporcionalmente con los VUs |
| **Tiempo de Respuesta** | Si p95 sube abruptamente, hay un cuello de botella |
| **Tasa de Errores** | Picos de error indican saturación del sistema |
| **WebSocket Connections** | Deben subir y mantenerse estables |
| **Checks OK** | Si baja de 90%, algo está fallando en las respuestas |
| **Latencia Promedio** | Verde (< 500ms), amarillo (< 2s), rojo (> 2s) |
