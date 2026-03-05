
# ═══════════════════════════════════════════════════════════════════════════════
# schemas/__init__.py — Paquete de Schemas Pydantic
# ═══════════════════════════════════════════════════════════════════════════════
# Los schemas de Pydantic definen la FORMA de los datos que entran y salen
# de la API. Son la frontera de validación entre HTTP y nuestro código.
#
# En este proyecto, los schemas están definidos INLINE dentro de cada router:
#   - events.py  → CreateEventRequest
#   - queue.py   → EnterQueueRequest, QueuePositionRequest, LeaveQueueRequest
#   - tickets.py → PurchaseRequest
#
# ¿Por qué inline y no en archivos separados?
#   Porque cada schema se usa en un solo router. Mantenerlos juntos
#   con sus endpoints hace que el código sea más fácil de seguir.
#
# Si en el futuro un schema se reutiliza en múltiples routers,
# se puede mover a este paquete (schemas/) como archivo compartido.
# ═══════════════════════════════════════════════════════════════════════════════
