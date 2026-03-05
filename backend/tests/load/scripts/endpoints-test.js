// ==============================================
// ENDPOINTS TEST — Virtual Queue
// ==============================================
// Tests de carga para cada endpoint HTTP individual.
// Permite identificar cuellos de botella específicos.
//
// Ejecutar:
//   docker-compose -f docker-compose.test.yml run k6 run /scripts/endpoints-test.js
// ==============================================

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// ── Configuración ──────────────────────────────
const API_BASE = __ENV.API_BASE_URL || 'http://api:8000';

// Métricas custom por endpoint
const enterQueueDuration = new Trend('endpoint_queue_enter_duration', true);
const leaveQueueDuration = new Trend('endpoint_queue_leave_duration', true);
const purchaseDuration = new Trend('endpoint_purchase_duration', true);
const eventsDuration = new Trend('endpoint_events_duration', true);
const enterQueueErrors = new Rate('endpoint_queue_enter_errors');
const purchaseErrors = new Rate('endpoint_purchase_errors');

export const options = {
    scenarios: {
        // Cada endpoint se testea con su propio escenario
        list_events: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { target: 100, duration: '30s' },   // Subir a 100 usuarios en 30s
                { target: 500, duration: '1m' },     // Subir a 500 en 1 minuto
                { target: 1000, duration: '1m' },    // Subir a 1000 en 1 minuto
                { target: 0, duration: '30s' },      // Bajar a 0 (enfriamiento)
            ],
            exec: 'testListEvents',
            tags: { endpoint: 'GET /api/events' },
        },

        enter_queue: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { target: 100, duration: '30s' },
                { target: 500, duration: '1m' },
                { target: 1000, duration: '1m' },
                { target: 0, duration: '30s' },
            ],
            exec: 'testEnterQueue',
            startTime: '3m30s',  // Empieza después del test anterior
            tags: { endpoint: 'POST /api/queue/enter' },
        },

        leave_queue: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { target: 100, duration: '30s' },
                { target: 500, duration: '1m' },
                { target: 1000, duration: '1m' },
                { target: 0, duration: '30s' },
            ],
            exec: 'testLeaveQueue',
            startTime: '7m',
            tags: { endpoint: 'DELETE /api/queue/leave' },
        },

        purchase_tickets: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { target: 50, duration: '30s' },
                { target: 200, duration: '1m' },
                { target: 500, duration: '1m' },
                { target: 0, duration: '30s' },
            ],
            exec: 'testPurchase',
            startTime: '10m30s',
            tags: { endpoint: 'POST /api/tickets/purchase' },
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<3000'],
        http_req_failed: ['rate<0.10'],
        'endpoint_queue_enter_duration': ['p(95)<2000'],
        'endpoint_purchase_duration': ['p(95)<3000'],
        'endpoint_queue_enter_errors': ['rate<0.10'],
        'endpoint_purchase_errors': ['rate<0.10'],
    },
};

// ── Funciones auxiliares ────────────────────────

function jsonHeaders() {
    return { headers: { 'Content-Type': 'application/json' } };
}

function uniqueUserId() {
    return `load-user-${__VU}-${__ITER}-${Date.now()}`;
}

// ── Tests por endpoint ─────────────────────────

// Test 1: GET /api/events
export function testListEvents() {
    const res = http.get(`${API_BASE}/api/events`);

    eventsDuration.add(res.timings.duration);

    check(res, {
        'GET /events: status 200': (r) => r.status === 200,
        'GET /events: tiene datos': (r) => {
            try {
                return JSON.parse(r.body) !== null;
            } catch {
                return false;
            }
        },
    });

    sleep(0.5);
}

// Test 2: POST /api/queue/enter
export function testEnterQueue() {
    const payload = JSON.stringify({
        user_id: uniqueUserId(),
        event_id: 'test-event-001',
    });

    const res = http.post(`${API_BASE}/api/queue/enter`, payload, jsonHeaders());

    enterQueueDuration.add(res.timings.duration);
    enterQueueErrors.add(res.status !== 200 && res.status !== 201);

    check(res, {
        'POST /queue/enter: status OK': (r) => r.status === 200 || r.status === 201,
        'POST /queue/enter: tiene position': (r) => {
            try {
                return JSON.parse(r.body).position !== undefined;
            } catch {
                return false;
            }
        },
    });

    sleep(0.3);
}

// Test 3: DELETE /api/queue/leave
export function testLeaveQueue() {
    // Primero entrar, luego salir
    const userId = uniqueUserId();
    const enterPayload = JSON.stringify({
        user_id: userId,
        event_id: 'test-event-001',
    });

    const enterRes = http.post(`${API_BASE}/api/queue/enter`, enterPayload, jsonHeaders());

    if (enterRes.status === 200 || enterRes.status === 201) {
        try {
            const body = JSON.parse(enterRes.body);
            if (body.queue_id) {
                const leaveRes = http.del(`${API_BASE}/api/queue/leave/${body.queue_id}`);

                leaveQueueDuration.add(leaveRes.timings.duration);

                check(leaveRes, {
                    'DELETE /queue/leave: status 200': (r) => r.status === 200,
                });
            }
        } catch {
            // Continuar
        }
    }

    sleep(0.3);
}

// Test 4: POST /api/tickets/purchase
export function testPurchase() {
    const userId = uniqueUserId();

    const payload = JSON.stringify({
        user_id: userId,
        event_id: 'test-event-001',
    });

    const res = http.post(`${API_BASE}/api/tickets/purchase`, payload, jsonHeaders());

    purchaseDuration.add(res.timings.duration);
    purchaseErrors.add(res.status !== 200 && res.status !== 201);

    check(res, {
        'POST /purchase: status OK o sin permiso': (r) => {
            // 200/201 = compra exitosa
            // 403 = sin permiso (esperado si no está en allowed_users)
            // 409 = sin stock (esperado)
            return [200, 201, 403, 409].includes(r.status);
        },
    });

    sleep(0.5);
}
