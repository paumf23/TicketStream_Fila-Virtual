// ══════════════════════════════════════════════════════════════
// lib/api.ts — Cliente API (funciones para hablar con el backend)
// ══════════════════════════════════════════════════════════════
// Centraliza todas las llamadas HTTP al backend FastAPI.
// Cada función corresponde a un endpoint del backend.
// ══════════════════════════════════════════════════════════════

import type {
  EventListResponse,
  Event,
  EventStatsResponse,
  EnterQueueResponse,
  QueuePositionResponse,
  PurchaseResponse,
  TicketDetailResponse,
} from "@/types";

// La URL base del backend FastAPI.
// NEXT_PUBLIC_ es un prefijo especial de Next.js que hace que la variable
// sea accesible desde el navegador (sin ese prefijo, solo se puede usar en el servidor).
// Si estamos en el servidor (SSR), usamos la URL interna de Docker (api:8000).
// Si estamos en el navegador (CSR), usamos la URL expuesta al usuario (localhost:8000).
const API_BASE = typeof window === "undefined"
  ? process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Función genérica para hacer requests ─────────────────────
// Todas las funciones de abajo usan esta función internamente.
// Se encarga de: armar la URL, enviar los headers, y manejar errores.
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    cache: "no-store", // Deshabilitar cache para asegurar datos frescos
    ...options,
  });

  // Si el backend devuelve un error (status 4xx o 5xx), se lanza una excepción
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Error ${response.status}`);
  }

  return response.json();
}

// ══════════════════════════════════════════════════════════════
// EVENTOS
// ══════════════════════════════════════════════════════════════

// GET /api/events/active → Lista de eventos activos (para la landing page)
export const getActiveEvents = (category?: string) => {
  const endpoint = category 
    ? `/api/events/active?category=${encodeURIComponent(category)}`
    : "/api/events/active";
  return request<EventListResponse>(endpoint);
};

// GET /api/events/{eventId} → Detalle de un evento específico
export const getEvent = (eventId: string) =>
  request<Event>(`/api/events/${eventId}`);

// GET /api/events/{eventId}/stats → Estadísticas de un evento
export const getEventStats = (eventId: string) =>
  request<EventStatsResponse>(`/api/events/${eventId}/stats`);

// ══════════════════════════════════════════════════════════════
// COLA DE ESPERA
// ══════════════════════════════════════════════════════════════

// POST /api/queue/enter → Entrar a la cola de un evento
export const enterQueue = (data: {
  user_id: string;
  event_id: string;
  first_name: string;
  last_name: string;
}) =>
  request<EnterQueueResponse>("/api/queue/enter", {
    method: "POST",
    body: JSON.stringify(data),
  });

// GET /api/queue/position?user_id=...&event_id=... → Consultar posición actual
export const getQueuePosition = (userId: string, eventId: string) =>
  request<QueuePositionResponse>(
    `/api/queue/position?user_id=${userId}&event_id=${eventId}`
  );

// ══════════════════════════════════════════════════════════════
// COMPRA DE TICKETS
// ══════════════════════════════════════════════════════════════

// POST /api/tickets/purchase → Comprar entrada(s)
export const purchaseTicket = (data: {
  user_id: string;
  event_id: string;
  first_name: string;
  last_name: string;
  dni: string;
  email: string;
  payment_method: string;
  payment_provider: string;
  quantity: number;
}) =>
  request<PurchaseResponse>("/api/tickets/purchase", {
    method: "POST",
    body: JSON.stringify(data),
  });

// GET /api/tickets/{ticketId} → Detalle de un ticket comprado
export const getTicketDetail = (ticketId: string) =>
  request<TicketDetailResponse>(`/api/tickets/${ticketId}`);

// ══════════════════════════════════════════════════════════════
// SIMULACIÓN
// ══════════════════════════════════════════════════════════════

// POST /api/simulate/load → Crear usuarios ficticios en la fila
export const simulateLoad = (eventId: string, numUsers: number) =>
  request<{ event_id: string; queue_length: number }>("/api/simulate/load", {
    method: "POST",
    body: JSON.stringify({ event_id: eventId, num_users: numUsers }),
  });


// POST /api/simulate/advanced → Simulación Pro (Mission Control)
export const advancedSimulate = (data: {
  event_id: string;
  num_users: number;
  include_me: boolean;
  user_id?: string;
  target_position?: number;
  processing_speed: number;
  abandon_rate: number;
  event_capacity: number;
}) =>
  request<{
    status: string;
    message: string;
    target_position?: number;
    config: { speed: number; abandon_rate: number };
  }>("/api/simulate/advanced", {
    method: "POST",
    body: JSON.stringify(data),
  });
