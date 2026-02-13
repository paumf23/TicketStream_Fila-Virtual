# Diagrama de Estados del Usuario

## Descripción

Este diagrama muestra todos los estados posibles de un usuario en el sistema y las transiciones entre ellos.

## Diagrama Principal

```mermaid
stateDiagram-v2
    [*] --> Visitante: Accede al sitio
    
    Visitante --> EnCola: POST /queue/enter
    
    EnCola --> EnCola: Actualización de posición (WebSocket)
    EnCola --> Visitante: DELETE /queue/leave
    EnCola --> Desconectado: Pérdida de conexión
    EnCola --> Permitido: Worker lo mueve a allowed_users
    
    Desconectado --> EnCola: Reconexión (dentro de gracia)
    Desconectado --> Visitante: Timeout de reconexión
    
    Permitido --> Comprando: POST /tickets/purchase
    Permitido --> TurnoExpirado: TTL 5 min expira
    
    TurnoExpirado --> EnCola: Vuelve a entrar
    TurnoExpirado --> Visitante: Sale del sitio
    
    Comprando --> TicketAdquirido: Pago exitoso
    Comprando --> ErrorCompra: Pago fallido / Sin stock
    
    ErrorCompra --> Visitante: Eventos agotados
    ErrorCompra --> EnCola: Vuelve a intentar
    
    TicketAdquirido --> [*]: Flujo completado

    note right of EnCola
        Redis LIST: waiting_queue
        Posición actualizada cada 1s
    end note
    
    note right of Permitido
        Redis HASH: allowed_users
        TTL: 300 segundos
    end note
    
    note right of TicketAdquirido
        MySQL: tickets table
        Registro permanente
    end note
```

## Tabla de Estados

| Estado | Almacenamiento | Duración | Acciones Permitidas |
|--------|----------------|----------|---------------------|
| **Visitante** | Ninguno | Indefinida | Ver eventos, entrar a cola |
| **EnCola** | Redis LIST | Hasta ser llamado | Ver posición, salir de cola |
| **Desconectado** | Redis LIST (persiste) | 30s gracia | Reconectar |
| **Permitido** | Redis HASH + TTL | 5 minutos | Comprar ticket |
| **TurnoExpirado** | Ninguno | - | Volver a entrar |
| **Comprando** | Transacción MySQL | Segundos | Esperar resultado |
| **ErrorCompra** | Log en MySQL | - | Reintentar o salir |
| **TicketAdquirido** | MySQL tickets | Permanente | Ver/descargar ticket |

## Transiciones con Condiciones

```mermaid
flowchart TD
    A[EnCola] -->|position == 0| B{¿Usuario conectado?}
    B -->|Sí| C[Mover a Permitido]
    B -->|No hace 30s| D[Remover de cola]
    
    C --> E{¿Compra en 5 min?}
    E -->|Sí| F[TicketAdquirido]
    E -->|No| G[TurnoExpirado]
    
    F --> H{¿Capacidad disponible?}
    H -->|Sí| I[INSERT ticket]
    H -->|No| J[ErrorCompra: SOLD_OUT]
```

## Manejo de Reconexión

```mermaid
sequenceDiagram
    participant U as Usuario
    participant WS as WebSocket
    participant R as Redis

    Note over U,R: Usuario pierde conexión
    
    U->>WS: Conexión perdida
    WS->>R: HSET disconnected_users {user_id} TTL=30s
    WS->>WS: Iniciar timer interno (30s)
    
    Note over U,R: Dentro de 30 segundos
    
    U->>WS: Reconectar con session_token
    WS->>R: HGET disconnected_users {user_id}
    R-->>WS: {original_position, queue_id}
    WS->>R: HDEL disconnected_users {user_id}
    WS->>WS: Cancelar timer
    WS-->>U: Reconectado en posición X
    
    Note over U,R: Después de 30 segundos (sin reconexión)
    
    WS->>WS: Timer expira
    WS->>R: LREM waiting_queue {user_id}
    Note over WS: Usuario removido de la cola desde cualquier posición
```

### Explicación del Flujo

1. La conexión se cae → **WebSocket Server** detecta el cierre internamente.
2. **WS → Redis**: marca al usuario en `disconnected_users` con TTL de 30s (período de gracia).
3. **WS → WS**: inicia un timer interno de 30 segundos.

**Camino A — reconecta a tiempo:**

4. El usuario reconecta con su `session_token`.
5. **WS → Redis**: consulta `disconnected_users` → obtiene su posición original y `queue_id`.
6. **WS → Redis**: elimina el registro de `disconnected_users` (`HDEL`).
7. **WS** cancela el timer y le confirma al usuario su posición restaurada.

**Camino B — no reconecta en 30 segundos:**

8. El timer expira internamente en el WebSocket Server.
9. **WS → Redis**: ejecuta `LREM waiting_queue {user_id}` → lo elimina de la cola desde cualquier posición.
10. Las posiciones de los demás usuarios se actualizan automáticamente en el próximo ciclo del Worker (máximo 1 segundo después).
