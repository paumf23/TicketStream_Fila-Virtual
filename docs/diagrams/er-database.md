# Diagrama Entidad-Relación (MySQL)
<div style="width: 140%;">

## Descripción

Este diagrama muestra el modelo de datos relacional para la persistencia en MySQL.

## Diagrama ER

```mermaid
erDiagram
    BUYERS ||--o{ TICKETS : purchases
    EVENTS ||--o{ TICKETS : has
    EVENTS ||--o{ QUEUE_HISTORY : for
    TICKETS ||--|| PAYMENTS : has

    BUYERS {
        varchar(36) id PK "UUID"
        varchar(100) first_name "Nombre del comprador"
        varchar(100) last_name "Apellido del comprador"
        varchar(20) dni "Documento Nacional de Identidad"
        varchar(100) email "Email del comprador"
        timestamp created_at "Fecha de registro"
    }
    
    EVENTS {
        varchar(36) id PK "UUID"
        varchar(255) name "Nombre del evento"
        text description "Descripción"
        int total_capacity "Capacidad total"
        int remaining_capacity "Tickets disponibles"
        decimal(10-2) price "Precio del ticket"
        varchar(3) currency "Moneda (ARS, USD)"
        datetime event_date "Fecha del evento"
        datetime sale_start "Inicio de ventas"
        datetime sale_end "Fin de ventas"
        enum status "draft, active, sold_out, cancelled"
        timestamp created_at "Fecha creación"
        timestamp updated_at "Última actualización"
    }
    
    TICKETS {
        varchar(36) id PK "UUID"
        varchar(36) buyer_id FK "Comprador"
        varchar(36) event_id FK "Evento asociado"
        varchar(50) ticket_code UK "Código legible: VQ-XXXXXXXXXXXX"
        decimal(10-2) price_paid "Precio pagado"
        enum status "pending, confirmed, used, cancelled"
        timestamp purchased_at "Fecha de compra"
        timestamp confirmed_at "Fecha de confirmación"
    }

    PAYMENTS {
        varchar(36) id PK "UUID"
        varchar(36) ticket_id FK "Ticket asociado"
        decimal(10-2) amount "Monto pagado"
        enum payment_method "credit_card, debit_card, mercado_pago"
        enum status "completed, failed, refunded"
        varchar(100) payment_reference UK "Referencia de transacción"
        timestamp created_at "Fecha del pago"
    }
    
    QUEUE_HISTORY {
        bigint id PK "Auto-increment"
        varchar(36) user_id "UUID anónimo del usuario en la cola"
        varchar(36) event_id FK "Evento"
        int initial_position "Posición al entrar"
        timestamp entered_at "Entrada a la cola"
        timestamp allowed_at "Cuando fue permitido"
        timestamp exited_at "Salida (compra o abandono)"
        enum exit_reason "purchased, expired, abandoned, disconnected"
        int wait_time_seconds "Tiempo en cola"
    }
    
```

## Índices Recomendados

```sql
-- BUYERS
CREATE INDEX idx_buyers_dni ON buyers(dni);
CREATE INDEX idx_buyers_email ON buyers(email);

-- EVENTS
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_sale_dates ON events(sale_start, sale_end);
CREATE INDEX idx_events_event_date ON events(event_date);

-- TICKETS
CREATE INDEX idx_tickets_buyer ON tickets(buyer_id);
CREATE INDEX idx_tickets_event ON tickets(event_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_code ON tickets(ticket_code);

-- PAYMENTS
CREATE INDEX idx_payments_ticket ON payments(ticket_id);
CREATE INDEX idx_payments_reference ON payments(payment_reference);

-- QUEUE_HISTORY
CREATE INDEX idx_queue_user_event ON queue_history(user_id, event_id);
CREATE INDEX idx_queue_entered ON queue_history(entered_at);
CREATE INDEX idx_queue_exit_reason ON queue_history(exit_reason);
```

## Notas de Diseño

### Race Condition en Compras

Para evitar sobreventa, la compra usa `SELECT ... FOR UPDATE`:

```sql
BEGIN TRANSACTION;

-- Bloquea la fila del evento
SELECT remaining_capacity 
FROM events 
WHERE id = ? 
FOR UPDATE;

-- Verifica capacidad
-- Si remaining_capacity > 0:

INSERT INTO buyers (id, first_name, last_name, dni, email) VALUES (...);
INSERT INTO tickets (id, buyer_id, event_id, ...) VALUES (...);
INSERT INTO payments (id, ticket_id, amount, payment_method, ...) VALUES (...);

UPDATE events 
SET remaining_capacity = remaining_capacity - 1 
WHERE id = ?;

COMMIT;
```

### Particionamiento Sugerido (Escala Futura)

```sql
-- Particionar queue_history por mes (tabla histórica grande)
ALTER TABLE queue_history 
PARTITION BY RANGE (UNIX_TIMESTAMP(entered_at)) (
    PARTITION p_2024_01 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01')),
    PARTITION p_2024_02 VALUES LESS THAN (UNIX_TIMESTAMP('2024-03-01')),
    -- ...
);
```
