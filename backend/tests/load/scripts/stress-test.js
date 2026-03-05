// ==============================================
// STRESS TEST + SPIKE TEST — Virtual Queue
// ==============================================
// Escenarios progresivos para llevar el sistema
// al límite y verificar su comportamiento.
//
// Ejecutar stress test:
//   docker-compose -f docker-compose.test.yml run k6 run /scripts/stress-test.js --env SCENARIO=stress
//
// Ejecutar spike test:
//   docker-compose -f docker-compose.test.yml run k6 run /scripts/stress-test.js --env SCENARIO=spike
//
// Ejecutar todos:
//   docker-compose -f docker-compose.test.yml run k6 run /scripts/stress-test.js
// ==============================================

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ── Configuración ──────────────────────────────
const API_BASE = __ENV.API_BASE_URL || 'http://api:8000';
const WS_BASE = __ENV.WS_BASE_URL || 'ws://api:8000';
const SCENARIO = __ENV.SCENARIO || 'all';

// Métricas custom
const flowCompleted = new Counter('stress_flow_completed');
const flowFailed = new Counter('stress_flow_failed');

// ── Escenarios ─────────────────────────────────

function getScenarios() {
    const scenarios = {};

    // ── STRESS TEST ───────────────────────────
    // Sube gradualmente hasta 10.000 usuarios
    // para encontrar el punto de quiebre.
    //
    // Visualización:
    //
    //   Usuarios
    //   10.000 │                    ╭──────────╮
    //          │                   ╱            ╲
    //    5.000 │              ╭───╯              ╲
    //          │             ╱                    ╲
    //    1.000 │        ╭───╯                      ╲
    //          │       ╱                            ╲
    //       0  │──────╯                              ╲────
    //          └──────────────────────────────────────────►
    //           0min   2min   4min   7min   10min  12min
    //
    if (SCENARIO === 'stress' || SCENARIO === 'all') {
        scenarios.stress = {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { target: 500, duration: '2m' },   // Calentamiento: 0 → 500 en 2 min
                { target: 1000, duration: '2m' },   // Carga normal: 500 → 1.000 en 2 min
                { target: 5000, duration: '3m' },   // Carga alta: 1.000 → 5.000 en 3 min
                { target: 10000, duration: '3m' },   // Carga máxima: 5.000 → 10.000 en 3 min
                { target: 0, duration: '2m' },   // Enfriamiento: 10.000 → 0 en 2 min
            ],
            exec: 'stressFlowTest',
            tags: { test_type: 'stress' },
        };
    }

    // ── SPIKE TEST ────────────────────────────
    // Sube de 0 a 10.000 de golpe (en 10 segundos)
    // para simular el momento en que abren las ventas.
    //
    // Visualización:
    //
    //   Usuarios
    //   10.000 │    ╭──────────────╮
    //          │    │              │
    //          │    │              │
    //          │    │              │
    //          │    │              │
    //       0  │────╯              ╰──────
    //          └──────────────────────────►
    //           0s   10s    1min    1m10s
    //
    if (SCENARIO === 'spike' || SCENARIO === 'all') {
        scenarios.spike = {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { target: 10000, duration: '10s' },  // 0 → 10.000 en 10 SEGUNDOS
                { target: 10000, duration: '1m' },   // Mantener 10.000 durante 1 minuto
                { target: 0, duration: '10s' },  // Bajar a 0
            ],
            exec: 'stressFlowTest',
            startTime: SCENARIO === 'all' ? '13m' : '0s',  // Si se corren todos, empieza después del stress
            tags: { test_type: 'spike' },
        };
    }

    return scenarios;
}

export const options = {
    scenarios: getScenarios(),
    thresholds: {
        http_req_duration: ['p(95)<10000'],   // Más permisivo bajo estrés extremo
        http_req_failed: ['rate<0.30'],       // Hasta 30% de errores es aceptable bajo 10k
    },
};

// ── Test de flujo bajo estrés ──────────────────

export function stressFlowTest() {
    const userId = `stress-${__VU}-${__ITER}-${Date.now()}`;
    const eventId = 'test-event-001';

    // 1. Entrar a la cola
    const enterPayload = JSON.stringify({
        user_id: userId,
        event_id: eventId,
    });

    const enterRes = http.post(`${API_BASE}/api/queue/enter`, enterPayload, {
        headers: { 'Content-Type': 'application/json' },
        timeout: '10s',
    });

    const enteredOk = check(enterRes, {
        'stress: queue/enter OK': (r) => r.status === 200 || r.status === 201,
    });

    if (!enteredOk) {
        flowFailed.add(1);
        sleep(0.5);
        return;
    }

    let queueId;
    try {
        queueId = JSON.parse(enterRes.body).queue_id;
    } catch {
        flowFailed.add(1);
        sleep(0.5);
        return;
    }

    // 2. Conectar WebSocket (con timeout corto para no saturar)
    const wsUrl = `${WS_BASE}/ws?user_id=${userId}&event_id=${eventId}`;
    let receivedTurn = false;

    const wsRes = ws.connect(wsUrl, { timeout: '15s' }, function (socket) {
        socket.on('message', function (message) {
            try {
                const data = JSON.parse(message);
                if (data.status === 'YOUR_TURN' || data.type === 'your_turn') {
                    receivedTurn = true;
                    socket.close();
                }
            } catch {
                // Ignorar
            }
        });

        socket.on('error', function () {
            // Bajo estrés, errores WS son esperados
        });

        // Timeout más corto bajo estrés
        socket.setTimeout(function () {
            socket.close();
        }, 15000);
    });

    // 3. Intentar comprar (si recibió turno)
    if (receivedTurn) {
        const purchasePayload = JSON.stringify({
            user_id: userId,
            event_id: eventId,
        });

        const purchaseRes = http.post(
            `${API_BASE}/api/tickets/purchase`,
            purchasePayload,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: '10s',
            }
        );

        const purchaseOk = check(purchaseRes, {
            'stress: purchase OK': (r) => [200, 201, 403, 409].includes(r.status),
        });

        if (purchaseOk) {
            flowCompleted.add(1);
        } else {
            flowFailed.add(1);
        }
    } else {
        // Limpiar: salir de la cola si no compró
        if (queueId) {
            http.del(`${API_BASE}/api/queue/leave/${queueId}`);
        }
        flowFailed.add(1);
    }

    // Pausa mínima entre iteraciones
    sleep(0.3);
}
