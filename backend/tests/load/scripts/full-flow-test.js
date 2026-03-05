// ==============================================
// FULL FLOW TEST — Virtual Queue
// ==============================================
// Simula el flujo completo de un usuario real:
// 1. Entrar a la cola (HTTP)
// 2. Conectar WebSocket y esperar actualizaciones
// 3. Recibir YOUR_TURN
// 4. Comprar ticket (HTTP)
// 5. Cerrar WebSocket
//
// Ejecutar:
//   docker-compose -f docker-compose.test.yml run k6 run /scripts/full-flow-test.js
// ==============================================

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ── Configuración ──────────────────────────────
const API_BASE = __ENV.API_BASE_URL || 'http://api:8000';
const WS_BASE = __ENV.WS_BASE_URL || 'ws://api:8000';

// Métricas custom
const flowCompleted = new Counter('flow_completed_total');
const flowFailed = new Counter('flow_failed_total');
const queueWaitTime = new Trend('flow_queue_wait_time', true);
const purchaseTime = new Trend('flow_purchase_time', true);
const wsMessagesReceived = new Counter('ws_messages_received_total');
const wsConnectionErrors = new Rate('ws_connection_errors');

export const options = {
    scenarios: {
        full_flow: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { target: 50, duration: '30s' },    // Calentamiento: subir a 50
                { target: 200, duration: '1m' },     // Subir a 200
                { target: 500, duration: '2m' },     // Subir a 500
                { target: 1000, duration: '2m' },    // Subir a 1000
                { target: 0, duration: '1m' },       // Enfriamiento
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<5000'],       // Más permisivo por ser flujo completo
        http_req_failed: ['rate<0.15'],
        ws_connection_errors: ['rate<0.10'],
        flow_purchase_time: ['p(95)<3000'],
    },
};

// ── Funciones auxiliares ────────────────────────

function jsonHeaders() {
    return { headers: { 'Content-Type': 'application/json' } };
}

function uniqueUserId() {
    return `flow-user-${__VU}-${__ITER}-${Date.now()}`;
}

// ── Test: Flujo completo ───────────────────────

export default function () {
    const userId = uniqueUserId();
    const eventId = 'test-event-001';

    // ════════════════════════════════════════════
    // FASE 1: Entrar a la cola
    // ════════════════════════════════════════════
    const enterPayload = JSON.stringify({
        user_id: userId,
        event_id: eventId,
    });

    const enterRes = http.post(`${API_BASE}/api/queue/enter`, enterPayload, jsonHeaders());

    const enteredOk = check(enterRes, {
        'FASE 1 — queue/enter: status OK': (r) => r.status === 200 || r.status === 201,
    });

    if (!enteredOk) {
        flowFailed.add(1);
        return; // Si no puede entrar, termina este usuario
    }

    let queueId;
    try {
        const enterBody = JSON.parse(enterRes.body);
        queueId = enterBody.queue_id;
    } catch {
        flowFailed.add(1);
        return;
    }

    // ════════════════════════════════════════════
    // FASE 2: Conectar WebSocket y esperar turno
    // ════════════════════════════════════════════
    const wsUrl = `${WS_BASE}/ws?user_id=${userId}&event_id=${eventId}`;
    const queueStartTime = Date.now();

    let receivedTurn = false;

    const wsRes = ws.connect(wsUrl, {}, function (socket) {
        socket.on('open', function () {
            // Conexión WebSocket establecida
        });

        socket.on('message', function (message) {
            wsMessagesReceived.add(1);

            try {
                const data = JSON.parse(message);

                // Verificar si es nuestro turno
                if (data.status === 'YOUR_TURN' || data.type === 'your_turn') {
                    receivedTurn = true;
                    const waitTime = Date.now() - queueStartTime;
                    queueWaitTime.add(waitTime);
                    socket.close();
                }

                // Actualización de posición — solo registrar
                if (data.position !== undefined || data.type === 'position_update') {
                    // El usuario sigue esperando
                }
            } catch {
                // Mensaje no JSON, ignorar
            }
        });

        socket.on('error', function (e) {
            wsConnectionErrors.add(1);
        });

        socket.on('close', function () {
            // Conexión cerrada
        });

        // Timeout: si después de 30s no recibe turno, cerrar
        socket.setTimeout(function () {
            if (!receivedTurn) {
                socket.close();
            }
        }, 30000);
    });

    check(wsRes, {
        'FASE 2 — WebSocket: conexión exitosa': (r) => r && r.status === 101,
    });

    if (!wsRes || wsRes.status !== 101) {
        wsConnectionErrors.add(1);
    }

    // ════════════════════════════════════════════
    // FASE 3: Comprar ticket (si recibió turno)
    // ════════════════════════════════════════════
    if (receivedTurn) {
        const purchasePayload = JSON.stringify({
            user_id: userId,
            event_id: eventId,
        });

        const purchaseStart = Date.now();
        const purchaseRes = http.post(
            `${API_BASE}/api/tickets/purchase`,
            purchasePayload,
            jsonHeaders()
        );
        purchaseTime.add(Date.now() - purchaseStart);

        const purchaseOk = check(purchaseRes, {
            'FASE 3 — purchase: status OK': (r) => r.status === 200 || r.status === 201,
            'FASE 3 — purchase: tiene ticket_id': (r) => {
                try {
                    const body = JSON.parse(r.body);
                    return body.ticket_id !== undefined || body.ticket_code !== undefined;
                } catch {
                    return false;
                }
            },
        });

        if (purchaseOk) {
            flowCompleted.add(1);
        } else {
            flowFailed.add(1);
        }
    } else {
        // No recibió turno en el timeout
        flowFailed.add(1);

        // Salir de la cola antes de terminar
        if (queueId) {
            http.del(`${API_BASE}/api/queue/leave/${queueId}`);
        }
    }

    // Pausa antes de la siguiente iteración
    sleep(1);
}
