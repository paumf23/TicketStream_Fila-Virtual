
from pydantic import BaseModel


class EventResponse(BaseModel):
    event_id: str
    name: str
    description: str | None = None
    image_url: str | None = None
    category: str | None = None
    rating: float | None = None
    rating_label: str | None = None
    total_capacity: int
    remaining_capacity: int
    price: float
    currency: str
    event_date: str
    sale_start: str
    sale_end: str
    status: str
    created_at: str
    updated_at: str


class EventListResponse(BaseModel):
    events: list[EventResponse]
    total: int


class EventStatsData(BaseModel):
    tickets_sold: int
    remaining_capacity: int
    occupancy_percentage: float
    queue_length: int
    revenue: float
    avg_wait_time_seconds: float | None = None
    peak_queue_length: int
    abandoned_count: int = 0
    processed_count: int = 0
    throughput: int = 0
    effort: float = 0.0
    trend: int = 0
    last_jump: int = 0
    incoming_rate: int = 0
    processed_rate: int = 0


class EventStatsResponse(EventResponse):
    stats: EventStatsData


class EnterQueueResponse(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    event_id: str
    position: int
    queue_length: int
    history_record_id: int
    event_name: str


class QueuePositionResponse(BaseModel):
    user_id: str
    event_id: str
    position: int
    queue_length: int
    estimated_wait: str


class LeaveQueueResponse(BaseModel):
    user_id: str
    event_id: str
    status: str


class PurchaseResponse(BaseModel):
    status: str
    message: str
    ticket_id: str
    ticket_code: str
    quantity: int
    buyer_id: str
    buyer_name: str
    event_id: str
    event_name: str
    price_paid: float
    ticket_status: str
    payment_reference: str
    purchased_at: str
    confirmed_at: str | None = None


class TicketDetailResponse(BaseModel):
    ticket_id: str
    ticket_code: str
    buyer_id: str
    buyer_name: str | None = None
    event_id: str
    event_name: str
    event_date: str | None = None
    price_paid: float
    status: str
    payment_reference: str | None = None
    payment_method: str | None = None
    payment_provider: str | None = None
    purchased_at: str
    confirmed_at: str | None = None


class SimulatedUser(BaseModel):
    user_id: str
    name: str


class SimulateLoadResponse(BaseModel):
    event_id: str
    event_name: str
    users_created: int
    queue_length: int
    sample_users: list[SimulatedUser]


class HealthResponse(BaseModel):
    status: str
    service: str
    redis: str


class ErrorResponse(BaseModel):
    detail: str
    error_type: str


class ValidationErrorDetail(BaseModel):
    campo: str
    mensaje: str
    tipo: str


class ValidationErrorResponse(BaseModel):
    detail: str
    errors: list[ValidationErrorDetail]
