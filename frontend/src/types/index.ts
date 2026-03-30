// ══════════════════════════════════════════════════════════════
// types/index.ts — Tipos TypeScript del Frontend
// ══════════════════════════════════════════════════════════════
// Estos tipos son el "espejo" de los schemas Pydantic del backend
// (backend/app/schemas/responses.py).
// Si el backend cambia un campo, hay que actualizarlo acá también.
// ══════════════════════════════════════════════════════════════

// --- Eventos ---
// Espeja: EventResponse en responses.py
export interface Event {
  event_id: string;
  name: string;
  description: string | null;
  image_url: string | null;
  category: string | null;
  total_capacity: number;
  remaining_capacity: number;
  price: number;
  currency: string;
  event_date: string;
  sale_start: string;
  sale_end: string;
  status: "draft" | "active" | "sold_out";
  rating: number | null;
  rating_label: string | null;
  created_at: string;
  updated_at: string;
}

// Espeja: EventListResponse en responses.py
export interface EventListResponse {
  events: Event[];
  total: number;
}

// Espeja: EventStatsData en responses.py
export interface EventStats {
  tickets_sold: number;
  remaining_capacity: number;
  occupancy_percentage: number;
  queue_length: number;
  revenue: number;
  avg_wait_time_seconds: number | null;
  peak_queue_length: number;
}

// Espeja: EventStatsResponse en responses.py
export interface EventStatsResponse extends Event {
  stats: EventStats;
}

// --- Cola de Espera ---
// Espeja: EnterQueueResponse en responses.py
export interface EnterQueueResponse {
  user_id: string;
  first_name: string;
  last_name: string;
  event_id: string;
  position: number;
  queue_length: number;
  history_record_id: number;
  event_name: string;
}

// Espeja: QueuePositionResponse en responses.py
export interface QueuePositionResponse {
  user_id: string;
  event_id: string;
  position: number;
  queue_length: number;
  estimated_wait: string;
}

// --- Compra / Tickets ---
// Espeja: PurchaseResponse en responses.py
export interface PurchaseResponse {
  status: string;
  message: string;
  ticket_id: string;
  ticket_code: string;
  quantity: number;
  buyer_id: string;
  buyer_name: string;
  event_id: string;
  event_name: string;
  price_paid: number;
  ticket_status: string;
  payment_reference: string;
  purchased_at: string;
  confirmed_at: string | null;
}

// Espeja: TicketDetailResponse en responses.py
export interface TicketDetailResponse {
  ticket_id: string;
  ticket_code: string;
  buyer_id: string;
  buyer_name: string | null;
  event_id: string;
  event_name: string;
  event_date: string | null;
  price_paid: number;
  status: string;
  payment_reference: string | null;
  payment_method: string | null;
  purchased_at: string;
  confirmed_at: string | null;
}

// --- WebSocket (mensajes que envía el worker via Redis Pub/Sub) ---
// Espeja: los JSON que publica worker.py con redis_repository.publish()
export interface WsYourTurn {
  type: "your_turn";
  user_id: string;
  event_id: string;
  event_name: string;
  ttl_seconds: number;
}

export interface WsPositionUpdate {
  type: "position_update";
  event_id: string;
  queue_length: number;
  users_processed: number;
}

// Union type: un mensaje de WebSocket puede ser cualquiera de estos dos
export type WsMessage = WsYourTurn | WsPositionUpdate;

// --- Errores de la API ---
// Espeja: ErrorResponse en responses.py
export interface ApiError {
  detail: string;
  error_type: string;
}
