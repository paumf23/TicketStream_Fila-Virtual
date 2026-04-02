-- ═══════════════════════════════════════════════════════════════════════════════
-- init.sql — Inicialización Automática de la Base de Datos
-- ═══════════════════════════════════════════════════════════════════════════════

-- Crear base de datos si no existe (aunque Docker Compose la crea, esto es Backup)
CREATE DATABASE IF NOT EXISTS virtual_queue;
USE virtual_queue;

-- 1. Tabla: buyers
CREATE TABLE IF NOT EXISTS buyers (
    id VARCHAR(36) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dni VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_buyer_dni (dni),
    INDEX idx_buyer_email (email)
) ENGINE=InnoDB;

-- 2. Tabla: events
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    category VARCHAR(50),
    rating DECIMAL(3, 1),
    rating_label VARCHAR(50),
    total_capacity INT NOT NULL,
    remaining_capacity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'ARS',
    event_date DATETIME NOT NULL,
    sale_start DATETIME NOT NULL,
    sale_end DATETIME NOT NULL,
    status ENUM('draft', 'active', 'sold_out') DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_event_status (status)
) ENGINE=InnoDB;

-- 3. Tabla: tickets
CREATE TABLE IF NOT EXISTS tickets (
    id VARCHAR(36) PRIMARY KEY,
    buyer_id VARCHAR(36) NOT NULL,
    event_id VARCHAR(36) NOT NULL,
    ticket_code VARCHAR(50) UNIQUE NOT NULL,
    price_paid DECIMAL(10, 2) NOT NULL,
    quantity INT DEFAULT 1,
    status ENUM('pending', 'confirmed', 'used') DEFAULT 'pending',
    purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confirmed_at DATETIME NULL,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id),
    FOREIGN KEY (event_id) REFERENCES events(id),
    INDEX idx_ticket_code (ticket_code),
    INDEX idx_ticket_buyer (buyer_id),
    INDEX idx_ticket_event (event_id)
) ENGINE=InnoDB;

-- 4. Tabla: payments
CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(36) PRIMARY KEY,
    ticket_id VARCHAR(36) UNIQUE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('card', 'wallet') NOT NULL,
    payment_provider VARCHAR(50) NULL,
    status ENUM('completed', 'failed') DEFAULT 'completed',
    payment_reference VARCHAR(100) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    INDEX idx_payment_ref (payment_reference)
) ENGINE=InnoDB;

-- 5. Tabla: queue_history
CREATE TABLE IF NOT EXISTS queue_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    event_id VARCHAR(36) NOT NULL,
    initial_position INT NOT NULL,
    entered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    allowed_at DATETIME NULL,
    exited_at DATETIME NULL,
    exit_reason ENUM('purchased', 'expired', 'abandoned', 'disconnected') NULL,
    wait_time_seconds INT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id),
    INDEX idx_history_user (user_id),
    INDEX idx_history_event (event_id)
) ENGINE=InnoDB;

-- Insertar Evento de Prueba
INSERT INTO events (id, name, description, total_capacity, remaining_capacity, price, event_date, sale_start, sale_end, status)
VALUES (
    'evt-test-001', 
    'Gran Concierto de Rock', 
    'Un evento masivo para probar la cola virtual.', 
    1000, 1000, 50000.00, 
    '2026-12-31 21:00:00', 
    '2026-03-01 10:00:00', 
    '2026-12-30 23:59:59', 
    'active'
);
