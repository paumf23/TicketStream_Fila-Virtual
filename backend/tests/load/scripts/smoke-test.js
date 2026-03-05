// ==============================================
// SMOKE TEST — Virtual Queue
// ==============================================
// Prueba inicial con pocos usuarios para verificar
// que todos los endpoints funcionan correctamente.
//
// Ejecutar:
//   docker-compose -f docker-compose.test.yml run k6 run /scripts/smoke-test.js
// ==============================================

import http from 'k6/http';
import { check, sleep } from 'k6';

// ── Configuración ──────────────────────────────
const API_BASE = __ENV.API_BASE_URL || 'http://api:8000';

export const options = {
    vus: 10,              // 10 usuarios virtuales
    duration: '30s',      // durante 30 segundos
    thresholds: {
        // Criterios de éxito: si alguno falla, el test falla
        http_req_duration: ['p(95)<2000'],  // 95% de requests en menos de 2 segundos
        http_req_failed: ['rate<0.05'],     // menos de 5% de errores
        checks: ['rate>0.95'],             // más de 95% de checks pasan
    },
};

// ── Test ────────────────────────────────────────
export default function () {
    // 1. Health check
    const healthRes = http.get(`${API_BASE}/health`);
    check(healthRes, {
        'health: status 200': (r) => r.status === 200,
    });

    // 2. Listar eventos
    const eventsRes = http.get(`${API_BASE}/api/events`);
    check(eventsRes, {
        'events: status 200': (r) => r.status === 200,
        'events: respuesta es JSON': (r) => r.headers['Content-Type']?.includes('application/json'),
    });

    // 3. Entrar a la cola (con un event_id de prueba)
    const enterPayload = JSON.stringify({
        user_id: `smoke-user-${__VU}-${__ITER}`,
        event_id: 'test-event-001',
    });

    const enterRes = http.post(`${API_BASE}/api/queue/enter`, enterPayload, {
        headers: { 'Content-Type': 'application/json' },
    });

    check(enterRes, {
        'queue/enter: status 200 o 201': (r) => r.status === 200 || r.status === 201,
        'queue/enter: tiene position': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.position !== undefined;
            } catch {
                return false;
            }
        },
    });

    // 4. Salir de la cola
    if (enterRes.status === 200 || enterRes.status === 201) {
        try {
            const enterBody = JSON.parse(enterRes.body);
            if (enterBody.queue_id) {
                const leaveRes = http.del(`${API_BASE}/api/queue/leave/${enterBody.queue_id}`);
                check(leaveRes, {
                    'queue/leave: status 200': (r) => r.status === 200,
                });
            }
        } catch {
            // Si no puede parsear, continúa
        }
    }

    // Pausa entre iteraciones (simula usuario real)
    sleep(1);
}
