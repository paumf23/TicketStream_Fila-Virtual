# Diagrama Entidad-Relación (MySQL)
<div style="width: 140%;">

## Descripción

Este diagrama muestra el modelo de datos relacional para la persistencia en MySQL.

## Diagrama ER

```mermaid
erDiagram
    USERS ||--o{ TICKETS : purchases
    USERS ||--o{ QUEUE_HISTORY : enters
    EVENTS ||--o{ TICKETS : has
    EVENTS ||--o{ QUEUE_HISTORY : for
    TICKETS ||--o{ AUDIT_LOG : generates
    
    USERS {
        varchar(36) id PK "UUID"
        varchar(255) session_token UK "Token de sesión"
        varchar(100) email "Opcional para notificaciones"
        timestamp created_at "Fecha de creación"
        timestamp last_seen_at "Última actividad"
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
        varchar(36) id PK "UUID - Código único del ticket"
        varchar(36) user_id FK "Usuario comprador"
        varchar(36) event_id FK "Evento asociado"
        varchar(50) ticket_code UK "Código legible: TKT-XXXX-XXXX"
        decimal(10-2) price_paid "Precio pagado"
        enum status "pending, confirmed, used, cancelled"
        varchar(100) payment_reference "Ref. pasarela (simulado)"
        timestamp purchased_at "Fecha de compra"
        timestamp confirmed_at "Fecha de confirmación"
    }
    
    QUEUE_HISTORY {
        bigint id PK "Auto-increment"
        varchar(36) user_id FK "Usuario"
        varchar(36) event_id FK "Evento"
        int initial_position "Posición al entrar"
        timestamp entered_at "Entrada a la cola"
        timestamp allowed_at "Cuando fue permitido"
        timestamp exited_at "Salida (compra o abandono)"
        enum exit_reason "purchased, expired, abandoned, disconnected"
        int wait_time_seconds "Tiempo en cola"
    }
    
    AUDIT_LOG {
        bigint id PK "Auto-increment"
        varchar(50) action "TICKET_PURCHASED, TICKET_CANCELLED, etc."
        varchar(36) user_id "Usuario involucrado"
        varchar(36) entity_id "ID de la entidad afectada"
        varchar(50) entity_type "ticket, event, etc."
        json old_value "Valor anterior (si aplica)"
        json new_value "Valor nuevo"
        varchar(45) ip_address "IP del cliente"
        text user_agent "User-Agent del navegador"
        timestamp created_at "Timestamp del evento"
    }
```

## Índices Recomendados

```sql
-- USERS
CREATE INDEX idx_users_session_token ON users(session_token);
CREATE INDEX idx_users_last_seen ON users(last_seen_at);

-- EVENTS
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_sale_dates ON events(sale_start, sale_end);
CREATE INDEX idx_events_event_date ON events(event_date);

-- TICKETS
CREATE INDEX idx_tickets_user ON tickets(user_id);
CREATE INDEX idx_tickets_event ON tickets(event_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_code ON tickets(ticket_code);

-- QUEUE_HISTORY
CREATE INDEX idx_queue_user_event ON queue_history(user_id, event_id);
CREATE INDEX idx_queue_entered ON queue_history(entered_at);
CREATE INDEX idx_queue_exit_reason ON queue_history(exit_reason);

-- AUDIT_LOG
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);
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

INSERT INTO tickets (id, user_id, event_id, ...) VALUES (...);

UPDATE events 
SET remaining_capacity = remaining_capacity - 1 
WHERE id = ?;

INSERT INTO audit_log (...) VALUES (...);

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

-- Particionar audit_log por mes
ALTER TABLE audit_log
PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (...);
```
